"""CelesTrak OMM CSV and SATCAT connector with strict usage-policy compliance."""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal
from urllib.parse import urlparse

import httpx

from ..models.wire import ObjectKind, SatcatMetadata

ALLOWED_HOST = "celestrak.org"
DEFAULT_GP_GROUPS: tuple[str, ...] = ("STATIONS", "ACTIVE", "COSMOS-2251-DEBRIS")
DEFAULT_SATCAT_URL = "https://celestrak.org/satcat/satcat.csv"
MIN_REFRESH_INTERVAL_SECONDS = 7200  # CelesTrak policy: >= 2 hours between GP downloads

REQUIRED_OMM_FIELDS = frozenset(
    {
        "OBJECT_NAME",
        "NORAD_CAT_ID",
        "EPOCH",
        "MEAN_MOTION",
        "ECCENTRICITY",
        "INCLINATION",
        "RA_OF_ASC_NODE",
        "ARG_OF_PERICENTER",
        "MEAN_ANOMALY",
        "BSTAR",
    }
)

OperationalStatus = Literal["ACTIVE", "INACTIVE", "UNKNOWN"]


class CelesTrakError(RuntimeError):
    """Raised when a CelesTrak feed cannot be fetched or parsed."""


@dataclass(frozen=True)
class RawOmmRecord:
    """Normalized OMM CSV record preserving full-precision NORAD catalog IDs."""

    norad_cat_id: str
    object_name: str
    object_id: str
    epoch_utc: datetime
    mean_motion: float
    eccentricity: float
    inclination: float
    ra_of_asc_node: float
    arg_of_pericenter: float
    mean_anomaly: float
    bstar: float
    mean_motion_dot: float
    mean_motion_ddot: float
    ephemeris_type: int
    classification_type: str
    element_set_no: int
    rev_at_epoch: int
    source_group: str

    def to_omm_dict(self) -> dict[str, object]:
        """Return an OMM dictionary compatible with `sgp4.omm.initialize`."""
        return {
            "OBJECT_NAME": self.object_name,
            "OBJECT_ID": self.object_id,
            "EPOCH": self.epoch_utc.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "MEAN_MOTION": self.mean_motion,
            "ECCENTRICITY": self.eccentricity,
            "INCLINATION": self.inclination,
            "RA_OF_ASC_NODE": self.ra_of_asc_node,
            "ARG_OF_PERICENTER": self.arg_of_pericenter,
            "MEAN_ANOMALY": self.mean_anomaly,
            "EPHEMERIS_TYPE": self.ephemeris_type,
            "CLASSIFICATION_TYPE": self.classification_type,
            "NORAD_CAT_ID": int(self.norad_cat_id),
            "ELEMENT_SET_NO": self.element_set_no,
            "REV_AT_EPOCH": self.rev_at_epoch,
            "BSTAR": self.bstar,
            "MEAN_MOTION_DOT": self.mean_motion_dot,
            "MEAN_MOTION_DDOT": self.mean_motion_ddot,
        }


@dataclass(frozen=True)
class CelesTrakFetchResult:
    """Result of fetching and normalizing CelesTrak GP + SATCAT feeds."""

    fetched_at_utc: datetime
    sources: list[str]
    omm_records: list[RawOmmRecord]
    satcat_by_id: dict[str, SatcatMetadata]
    warning_codes: list[str] = field(default_factory=list)
    decayed_filtered_count: int = 0


def validate_celestrak_url(url: str) -> str:
    """Enforce HTTPS and strict CelesTrak host allowlist to prevent SSRF."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
        raise CelesTrakError(f"Disallowed provider URL: {url}")
    return url


def parse_utc_epoch(raw: str) -> datetime:
    """Parse an ISO-8601 epoch string as timezone-aware UTC."""
    text = raw.strip()
    if not text:
        raise ValueError("empty epoch")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _parse_finite_float(row: dict[str, str], key: str, default: float | None = None) -> float:
    raw = (row.get(key) or "").strip()
    if not raw:
        if default is not None:
            return default
        raise ValueError(f"missing {key}")
    val = float(raw)
    if not math.isfinite(val):
        raise ValueError(f"non-finite {key}")
    return val


def _parse_int(row: dict[str, str], key: str, default: int = 0) -> int:
    raw = (row.get(key) or "").strip()
    if not raw:
        return default
    return int(raw)


def normalize_norad_id(raw: str) -> str:
    """Validate and normalize a numeric NORAD catalog ID (supports 6-digit+ and 9-digit)."""
    digits = raw.strip()
    if not digits or not digits.isdigit():
        raise ValueError(f"invalid NORAD_CAT_ID: {raw!r}")
    return str(int(digits)) if digits.startswith("0") and len(digits) > 1 else digits


def map_object_kind(raw_type: str | None) -> ObjectKind:
    """Map SATCAT OBJECT_TYPE to canonical ObjectKind."""
    cleaned = (raw_type or "").strip().upper()
    if cleaned in {"PAY", "PAYLOAD"}:
        return "PAYLOAD"
    if cleaned in {"R/B", "ROCKET BODY", "ROCKET_BODY"}:
        return "ROCKET_BODY"
    if cleaned in {"DEB", "DEBRIS"}:
        return "DEBRIS"
    return "UNKNOWN"


def map_operational_status(raw_code: str | None) -> OperationalStatus:
    """Map SATCAT OPS_STATUS_CODE; never assume unknown status is active."""
    cleaned = (raw_code or "").strip().upper()
    if cleaned in {"+", "P", "B", "S", "X"}:
        return "ACTIVE"
    if cleaned in {"-", "D"}:
        return "INACTIVE"
    return "UNKNOWN"


def parse_omm_csv(csv_text: str, source_group: str) -> tuple[list[RawOmmRecord], list[str]]:
    """Parse CelesTrak OMM CSV text into normalized RawOmmRecord items."""
    stripped = csv_text.strip()
    if not stripped:
        raise CelesTrakError(f"Empty OMM CSV response for group {source_group}")

    reader = csv.DictReader(io.StringIO(stripped))
    if not reader.fieldnames:
        raise CelesTrakError(f"Malformed OMM CSV header for group {source_group}")

    fieldnames = {name.strip() for name in reader.fieldnames if name}
    missing = REQUIRED_OMM_FIELDS - fieldnames
    if missing:
        raise CelesTrakError(
            f"Malformed OMM CSV for group {source_group}: missing {sorted(missing)}"
        )

    records: list[RawOmmRecord] = []
    warnings: list[str] = []
    skipped = 0

    for raw_row in reader:
        row = {k.strip(): (v or "").strip() for k, v in raw_row.items() if k is not None}
        try:
            norad_id = normalize_norad_id(row.get("NORAD_CAT_ID", ""))
            name = row.get("OBJECT_NAME") or f"NORAD {norad_id}"
            epoch = parse_utc_epoch(row.get("EPOCH", ""))
            record = RawOmmRecord(
                norad_cat_id=norad_id,
                object_name=name,
                object_id=row.get("OBJECT_ID", ""),
                epoch_utc=epoch,
                mean_motion=_parse_finite_float(row, "MEAN_MOTION"),
                eccentricity=_parse_finite_float(row, "ECCENTRICITY"),
                inclination=_parse_finite_float(row, "INCLINATION"),
                ra_of_asc_node=_parse_finite_float(row, "RA_OF_ASC_NODE"),
                arg_of_pericenter=_parse_finite_float(row, "ARG_OF_PERICENTER"),
                mean_anomaly=_parse_finite_float(row, "MEAN_ANOMALY"),
                bstar=_parse_finite_float(row, "BSTAR", default=0.0),
                mean_motion_dot=_parse_finite_float(row, "MEAN_MOTION_DOT", default=0.0),
                mean_motion_ddot=_parse_finite_float(row, "MEAN_MOTION_DDOT", default=0.0),
                ephemeris_type=_parse_int(row, "EPHEMERIS_TYPE", default=0),
                classification_type=row.get("CLASSIFICATION_TYPE") or "U",
                element_set_no=_parse_int(row, "ELEMENT_SET_NO", default=999),
                rev_at_epoch=_parse_int(row, "REV_AT_EPOCH", default=0),
                source_group=source_group,
            )
            if record.mean_motion <= 0 or not (0.0 <= record.eccentricity < 1.0):
                raise ValueError("orbital elements out of range")
            records.append(record)
        except ValueError:
            skipped += 1

    if not records:
        raise CelesTrakError(f"No valid OMM records parsed for group {source_group}")
    if skipped > 0:
        warnings.append("PARTIAL_OMM_PARSE_ERRORS")
    return records, warnings


def parse_satcat_csv(csv_text: str) -> dict[str, SatcatMetadata]:
    """Parse CelesTrak SATCAT CSV keyed by normalized NORAD_CAT_ID."""
    stripped = csv_text.strip()
    if not stripped:
        return {}
    reader = csv.DictReader(io.StringIO(stripped))
    if not reader.fieldnames:
        return {}

    result: dict[str, SatcatMetadata] = {}
    for raw_row in reader:
        row = {k.strip(): (v or "").strip() for k, v in raw_row.items() if k is not None}
        raw_id = row.get("NORAD_CAT_ID", "")
        if not raw_id:
            continue
        try:
            norad_id = normalize_norad_id(raw_id)
        except ValueError:
            continue

        rcs_val: float | None = None
        raw_rcs = row.get("RCS", "")
        if raw_rcs:
            try:
                parsed_rcs = float(raw_rcs)
                if math.isfinite(parsed_rcs) and parsed_rcs >= 0:
                    rcs_val = parsed_rcs
            except ValueError:
                rcs_val = None

        result[norad_id] = SatcatMetadata(
            norad_cat_id=norad_id,
            object_type_raw=row.get("OBJECT_TYPE") or None,
            operational_status_code=row.get("OPS_STATUS_CODE") or None,
            launch_date=row.get("LAUNCH_DATE") or None,
            decay_date=row.get("DECAY_DATE") or None,
            rcs_m2=rcs_val,
            owner=row.get("OWNER") or None,
        )
    return result


class CelesTrakConnector:
    """Policy-compliant CelesTrak GP + SATCAT client."""

    def __init__(
        self,
        *,
        groups: tuple[str, ...] = DEFAULT_GP_GROUPS,
        satcat_url: str = DEFAULT_SATCAT_URL,
        timeout_seconds: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.groups = groups
        self.satcat_url = validate_celestrak_url(satcat_url)
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def _get_text(self, client: httpx.Client, url: str) -> str:
        validate_celestrak_url(url)
        try:
            response = client.get(
                url,
                headers={"Accept-Encoding": "gzip, deflate", "User-Agent": "ASTRA-Lab/0.1"},
            )
        except httpx.HTTPError as exc:
            raise CelesTrakError(f"CelesTrak request failed for {url}: {exc}") from exc

        # Policy: never hammer or retry after non-200 responses.
        if response.status_code != 200:
            raise CelesTrakError(f"CelesTrak returned HTTP {response.status_code} for {url}")
        return response.text

    def fetch(self, *, now_utc: datetime | None = None) -> CelesTrakFetchResult:
        """Fetch configured GP groups and SATCAT, deduplicate, and filter decayed objects."""
        fetched_at = (now_utc or datetime.now(UTC)).astimezone(UTC)
        warnings: list[str] = ["PARTIAL_CATALOG_COVERAGE"]
        sources: list[str] = []
        by_id: dict[str, RawOmmRecord] = {}
        epoch_conflict = False

        with httpx.Client(timeout=self.timeout_seconds, transport=self.transport) as client:
            for group in self.groups:
                url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=CSV"
                csv_text = self._get_text(client, url)
                records, group_warnings = parse_omm_csv(csv_text, group)
                warnings.extend(group_warnings)
                sources.append(f"CelesTrak GP ({group})")
                for rec in records:
                    existing = by_id.get(rec.norad_cat_id)
                    if existing is None:
                        by_id[rec.norad_cat_id] = rec
                    else:
                        if existing.epoch_utc != rec.epoch_utc:
                            epoch_conflict = True
                        if rec.epoch_utc > existing.epoch_utc:
                            by_id[rec.norad_cat_id] = rec

            satcat_by_id: dict[str, SatcatMetadata] = {}
            try:
                satcat_csv = self._get_text(client, self.satcat_url)
                satcat_by_id = parse_satcat_csv(satcat_csv)
                if satcat_by_id:
                    sources.append("CelesTrak SATCAT")
            except CelesTrakError:
                warnings.append("SATCAT_UNAVAILABLE")

        if epoch_conflict:
            warnings.append("DUPLICATE_EPOCH_CONFLICT")

        filtered_records: list[RawOmmRecord] = []
        decayed_count = 0
        for rec in by_id.values():
            sat = satcat_by_id.get(rec.norad_cat_id)
            if sat and sat.decay_date:
                decayed_count += 1
                continue
            filtered_records.append(rec)

        if decayed_count > 0:
            warnings.append("DECAYED_OBJECTS_FILTERED")

        filtered_records.sort(key=lambda r: r.norad_cat_id)
        deduped_warnings = list(dict.fromkeys(warnings))
        return CelesTrakFetchResult(
            fetched_at_utc=fetched_at,
            sources=sources,
            omm_records=filtered_records,
            satcat_by_id=satcat_by_id,
            warning_codes=deduped_warnings,
            decayed_filtered_count=decayed_count,
        )
