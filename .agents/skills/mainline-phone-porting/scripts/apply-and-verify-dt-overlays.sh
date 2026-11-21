#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

usage() {
  cat <<'EOF'
Apply one or more compiled device-tree overlays to an exact base DTB offline,
then decompile, hash, and document the merged result.

Usage:
  apply-and-verify-dt-overlays.sh --base BASE.dtb \
    --overlay FIRST.dtbo [--overlay NEXT.dtbo ...] --output MERGED.dtb [options]

Options:
  --fdtoverlay TOOL  fdtoverlay executable or path (default: fdtoverlay).
  --dtc TOOL         dtc executable or path (default: dtc).
  --force            Replace existing output and sidecar evidence files.
  --dry-run          Validate inputs and print the planned commands only.
  -h, --help         Show this help.

Outputs:
  MERGED.dtb
  MERGED.dtb.dts
  MERGED.dtb.sha256
  MERGED.dtb.manifest

Overlay order is exactly the order of --overlay arguments. Structural success
does not prove that a bootloader selects the overlay or that it is correct for
the hardware. This script never flashes or modifies an input artifact.
EOF
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 2
}

need_value() {
  [[ $# -ge 2 && -n ${2:-} ]] || die "$1 requires a value"
}

print_command() {
  printf '  '
  printf '%q ' "$@"
  printf '\n'
}

resolve_tool() {
  local requested=$1 resolved
  if [[ $requested == */* ]]; then
    [[ -x $requested ]] || die "tool is not executable: $requested"
    realpath "$requested"
  else
    resolved=$(command -v "$requested" 2>/dev/null) || die "tool is not installed: $requested"
    realpath "$resolved"
  fi
}

tool_version() {
  local tool=$1 output
  if output=$("$tool" --version 2>&1); then
    printf '%s\n' "$output" | sed -n '1p'
  else
    printf 'unavailable'
  fi
}

check_fdt_magic() {
  local file=$1 magic
  magic=$(od -An -tx1 -N4 "$file" | tr -d '[:space:]')
  [[ $magic == d00dfeed ]] || die "not an FDT blob (magic $magic): $file"
}

base=
output=
fdtoverlay_tool=fdtoverlay
dtc_tool=dtc
force=false
dry_run=false
declare -a overlays=()

while (($#)); do
  case "$1" in
    --base)
      need_value "$@"; base=$2; shift 2 ;;
    --overlay)
      need_value "$@"; overlays+=("$2"); shift 2 ;;
    --output)
      need_value "$@"; output=$2; shift 2 ;;
    --fdtoverlay)
      need_value "$@"; fdtoverlay_tool=$2; shift 2 ;;
    --dtc)
      need_value "$@"; dtc_tool=$2; shift 2 ;;
    --force)
      force=true; shift ;;
    --dry-run)
      dry_run=true; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      die "unknown argument: $1" ;;
  esac
done

[[ -n $base ]] || die "--base is required"
[[ -n $output ]] || die "--output is required"
((${#overlays[@]} > 0)) || die "at least one --overlay is required"
command -v od >/dev/null 2>&1 || die "od is not installed"
[[ -f $base ]] || die "base DTB does not exist: $base"
base=$(realpath "$base")
check_fdt_magic "$base"

declare -a overlay_abs=()
for overlay in "${overlays[@]}"; do
  [[ -f $overlay ]] || die "overlay does not exist: $overlay"
  overlay=$(realpath "$overlay")
  check_fdt_magic "$overlay"
  overlay_abs+=("$overlay")
done

output=$(realpath -m "$output")
[[ $output != / ]] || die "invalid output path"
[[ $output != "$base" ]] || die "output must not replace the base DTB"
for overlay in "${overlay_abs[@]}"; do
  [[ $output != "$overlay" ]] || die "output must not replace an input overlay"
done

dts_output=$output.dts
hash_output=$output.sha256
manifest_output=$output.manifest
for candidate in "$output" "$dts_output" "$hash_output" "$manifest_output"; do
  [[ $candidate != "$base" ]] || die "an output sidecar would replace the base DTB: $candidate"
  for overlay in "${overlay_abs[@]}"; do
    [[ $candidate != "$overlay" ]] || die "an output sidecar would replace an input overlay: $candidate"
  done
done
if ! $force; then
  for candidate in "$output" "$dts_output" "$hash_output" "$manifest_output"; do
    [[ ! -e $candidate ]] || die "output exists; use --force to replace it: $candidate"
  done
fi

if $dry_run; then
  printf 'Validated overlay plan (no files written):\n'
  print_command "$fdtoverlay_tool" -i "$base" -o "$output" "${overlay_abs[@]}"
  print_command "$dtc_tool" -I dtb -O dts -o "$dts_output" "$output"
  printf '  sha256sum %q\n' "$output"
  exit 0
fi

command -v sha256sum >/dev/null 2>&1 || die "sha256sum is not installed"
fdtoverlay_tool=$(resolve_tool "$fdtoverlay_tool")
dtc_tool=$(resolve_tool "$dtc_tool")

output_dir=$(dirname "$output")
mkdir -p -- "$output_dir"
temp_dir=$(mktemp -d "$output_dir/.dt-overlay.XXXXXX")
cleanup() { rm -rf -- "$temp_dir"; }
trap cleanup EXIT

merged=$temp_dir/merged.dtb
decoded=$temp_dir/merged.dts
hash_sidecar=$temp_dir/merged.sha256
manifest=$temp_dir/merged.manifest

"$fdtoverlay_tool" -i "$base" -o "$merged" "${overlay_abs[@]}"
check_fdt_magic "$merged"
"$dtc_tool" -I dtb -O dts -o "$decoded" "$merged"
merged_hash=$(sha256sum "$merged")
merged_hash=${merged_hash%% *}
printf '%s  %s\n' "$merged_hash" "$(basename "$output")" >"$hash_sidecar"

{
  printf 'format_version=2\n'
  printf 'created_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'fdtoverlay=%s\n' "$fdtoverlay_tool"
  printf 'fdtoverlay_version=%s\n' "$(tool_version "$fdtoverlay_tool")"
  printf 'fdtoverlay_sha256=%s\n' "$(sha256sum "$fdtoverlay_tool" | awk '{print $1}')"
  printf 'dtc=%s\n' "$dtc_tool"
  printf 'dtc_version=%s\n' "$(tool_version "$dtc_tool")"
  printf 'dtc_sha256=%s\n' "$(sha256sum "$dtc_tool" | awk '{print $1}')"
  printf 'base=%s\n' "$base"
  printf 'base_sha256=%s\n' "$(sha256sum "$base" | awk '{print $1}')"
  printf 'overlay_count=%d\n' "${#overlay_abs[@]}"
  index=0
  for overlay in "${overlay_abs[@]}"; do
    printf 'overlay_%d=%s\n' "$index" "$overlay"
    printf 'overlay_%d_sha256=%s\n' "$index" "$(sha256sum "$overlay" | awk '{print $1}')"
    ((index += 1))
  done
  printf 'merged_sha256=%s\n' "$merged_hash"
  printf 'claim_limit=Offline structural application only; no hardware or bootloader compatibility claim.\n'
} >"$manifest"

mv -f -- "$merged" "$output"
mv -f -- "$decoded" "$dts_output"
mv -f -- "$hash_sidecar" "$hash_output"
mv -f -- "$manifest" "$manifest_output"
printf 'Merged DTB and evidence written to %s and sidecars.\n' "$output"
