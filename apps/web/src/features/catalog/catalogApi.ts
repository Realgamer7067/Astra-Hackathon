import type { components } from "../../../../../packages/contracts/api";

export type CatalogStatus = components["schemas"]["CatalogStatus"];
export type CatalogRefreshResult =
  components["schemas"]["CatalogRefreshResult"];
export type ObjectSearchPage = components["schemas"]["ObjectSearchPage"];
export type ObjectDetail = components["schemas"]["ObjectDetail"];
export type RenderStates = components["schemas"]["RenderStates"];
export type CatalogObject = components["schemas"]["CatalogObject"];
export type CartesianState = components["schemas"]["CartesianState"];
export type SourceMode = CatalogStatus["mode"];
export type ObjectKind = CatalogObject["kind"];
export type OperationalStatus = CatalogObject["operational_status"];

export function modeBadgeLabel(mode: SourceMode): string {
  if (mode === "LIVE") return "LIVE CATALOG";
  if (mode === "CACHED") return "CACHED";
  return "OFFLINE DEMO";
}

export function formatSourceAge(
  isoUtc: string | null | undefined,
  nowMs: number = Date.now(),
): string {
  if (!isoUtc) return "No live fetch";
  const parsed = Date.parse(isoUtc);
  if (Number.isNaN(parsed)) return "Unknown";
  const diffMin = Math.max(0, Math.floor((nowMs - parsed) / 60_000));
  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 48) return `${diffHr}h ago`;
  const diffDays = Math.floor(diffHr / 24);
  return `${diffDays}d ago`;
}

async function readJsonOrThrow<T>(
  response: Response,
  fallbackMessage: string,
): Promise<T> {
  if (!response.ok) {
    let message = fallbackMessage;
    try {
      const body = (await response.json()) as { error?: { message?: string } };
      if (body.error?.message) message = body.error.message;
    } catch {
      // Keep fallback message when response body is not JSON.
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export async function fetchCatalogStatus(
  signal?: AbortSignal,
): Promise<CatalogStatus> {
  const res = await fetch("/api/v1/catalog/status", { signal });
  return readJsonOrThrow<CatalogStatus>(res, "Catalog status unavailable");
}

export async function refreshCatalog(
  signal?: AbortSignal,
): Promise<CatalogRefreshResult> {
  const res = await fetch("/api/v1/catalog/refresh", {
    method: "POST",
    signal,
  });
  return readJsonOrThrow<CatalogRefreshResult>(res, "Catalog refresh failed");
}

export type SearchParams = {
  query?: string;
  kind?: ObjectKind | "";
  operationalStatus?: OperationalStatus | "";
  limit?: number;
  cursor?: string | null;
};

export async function searchObjects(
  params: SearchParams,
  signal?: AbortSignal,
): Promise<ObjectSearchPage> {
  const qs = new URLSearchParams();
  if (params.query?.trim()) qs.set("query", params.query.trim());
  if (params.kind) qs.set("kind", params.kind);
  if (params.operationalStatus)
    qs.set("operational_status", params.operationalStatus);
  qs.set("limit", String(params.limit ?? 50));
  if (params.cursor) qs.set("cursor", params.cursor);
  const res = await fetch(`/api/v1/objects?${qs.toString()}`, { signal });
  return readJsonOrThrow<ObjectSearchPage>(res, "Catalog search failed");
}

export async function fetchObjectDetail(
  objectId: string,
  signal?: AbortSignal,
): Promise<ObjectDetail> {
  const res = await fetch(`/api/v1/objects/${encodeURIComponent(objectId)}`, {
    signal,
  });
  return readJsonOrThrow<ObjectDetail>(res, "Object detail unavailable");
}

export async function fetchRenderStates(
  options: {
    at?: string;
    scope?: "visible" | "selected" | "preset";
    limit?: number;
  } = {},
  signal?: AbortSignal,
): Promise<RenderStates> {
  const qs = new URLSearchParams();
  if (options.at) qs.set("at", options.at);
  qs.set("scope", options.scope ?? "visible");
  qs.set("limit", String(options.limit ?? 200));
  const res = await fetch(`/api/v1/states?${qs.toString()}`, { signal });
  return readJsonOrThrow<RenderStates>(res, "Orbital states unavailable");
}
