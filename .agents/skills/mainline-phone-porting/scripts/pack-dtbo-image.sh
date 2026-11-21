#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

usage() {
  cat <<'EOF'
Create an Android DT table image from an explicit AOSP mkdtimg configuration,
then dump, hash, and preserve the exact configuration and input provenance.

Usage:
  pack-dtbo-image.sh --config dtboimg.cfg --output dtbo.img [options]

Options:
  --mkdtimg TOOL  mkdtimg executable or path (default: mkdtimg).
  --force         Replace existing output and sidecar evidence files.
  --dry-run       Validate config/input blobs and print commands without writing.
  -h, --help      Show this help.

The config must follow mkdtimg cfg_create syntax, contain an explicit global
page_size before the first entry, and name at least one existing FDT blob. Entry
order and id/rev/custom selectors are preserved exactly. Determine all selector
values from the target bootloader, vendor source, or a known-good image—this
script cannot infer them. It never signs or flashes the resulting image.
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

blob_magic() {
  od -An -tx1 -N4 "$1" | tr -d '[:space:]'
}

config=
output=
mkdtimg_tool=mkdtimg
force=false
dry_run=false

while (($#)); do
  case "$1" in
    --config)
      need_value "$@"; config=$2; shift 2 ;;
    --output)
      need_value "$@"; output=$2; shift 2 ;;
    --mkdtimg)
      need_value "$@"; mkdtimg_tool=$2; shift 2 ;;
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

[[ -n $config ]] || die "--config is required"
[[ -n $output ]] || die "--output is required"
[[ -f $config ]] || die "configuration does not exist: $config"
command -v od >/dev/null 2>&1 || die "od is not installed"
command -v sha256sum >/dev/null 2>&1 || die "sha256sum is not installed"

config=$(realpath "$config")
config_dir=$(dirname "$config")
config_name=$(basename "$config")
output=$(realpath -m "$output")
[[ $output != / ]] || die "invalid output path"
[[ $output != "$config" ]] || die "output must not replace the configuration"

page_size=$(awk '
  /^[[:space:]]*($|#)/ { next }
  /^[^[:space:]]/ { exit }
  /^[[:space:]]+page_size[[:space:]]*=/ {
    line=$0
    sub(/^[[:space:]]+page_size[[:space:]]*=[[:space:]]*/, "", line)
    sub(/[[:space:]]+#.*/, "", line)
    sub(/[[:space:]]+$/, "", line)
    print line
    exit
  }
' "$config")
[[ -n $page_size ]] || \
  die "config must set an explicit global page_size before the first entry"
[[ $page_size =~ ^(0[xX][0-9A-Fa-f]+|[1-9][0-9]*)$ ]] || \
  die "invalid page_size value: $page_size"

mapfile -t entry_names < <(awk '
  /^[[:space:]]*($|#)/ { next }
  /^[^[:space:]]/ {
    line=$0
    sub(/[[:space:]]+#.*/, "", line)
    sub(/[[:space:]]+$/, "", line)
    if (length(line)) print line
  }
' "$config")
((${#entry_names[@]} > 0)) || die "config contains no DTB/DTBO entries"

declare -a entry_paths=()
for entry in "${entry_names[@]}"; do
  if [[ $entry = /* ]]; then
    entry_path=$entry
  else
    entry_path=$config_dir/$entry
  fi
  [[ -f $entry_path ]] || die "config entry does not exist: $entry"
  entry_path=$(realpath "$entry_path")
  magic=$(blob_magic "$entry_path")
  [[ $magic == d00dfeed ]] || die "config entry is not an FDT blob: $entry"
  size=$(wc -c <"$entry_path")
  ((size % 4 == 0)) || \
    die "config entry is not four-byte aligned; rebuild with the verified dtc alignment: $entry"
  entry_paths+=("$entry_path")
done

dump_output=$output.dump.txt
hash_output=$output.sha256
config_output=$output.config
manifest_output=$output.manifest
for candidate in "$output" "$dump_output" "$hash_output" "$config_output" "$manifest_output"; do
  [[ $candidate != "$config" ]] || die "an output sidecar would replace the input configuration: $candidate"
  for entry_path in "${entry_paths[@]}"; do
    [[ $candidate != "$entry_path" ]] || die "an output sidecar would replace an input FDT: $candidate"
  done
done
if ! $force; then
  for candidate in "$output" "$dump_output" "$hash_output" "$config_output" "$manifest_output"; do
    [[ ! -e $candidate ]] || die "output exists; use --force to replace it: $candidate"
  done
fi

if $dry_run; then
  printf 'Validated DT table plan (no files written):\n'
  printf '  (cd %q && ' "$config_dir"
  printf '%q ' "$mkdtimg_tool" cfg_create "$output" "$config_name"
  printf ')\n'
  print_command "$mkdtimg_tool" dump "$output"
  printf '  sha256sum %q\n' "$output"
  exit 0
fi

mkdtimg_tool=$(resolve_tool "$mkdtimg_tool")
output_dir=$(dirname "$output")
mkdir -p -- "$output_dir"
temp_dir=$(mktemp -d "$output_dir/.dtbo-image.XXXXXX")
cleanup() { rm -rf -- "$temp_dir"; }
trap cleanup EXIT

image_tmp=$temp_dir/dtbo.img
dump_tmp=$temp_dir/dtbo.img.dump.txt
hash_tmp=$temp_dir/dtbo.img.sha256
config_tmp=$temp_dir/dtbo.img.config
manifest_tmp=$temp_dir/dtbo.img.manifest

(cd "$config_dir" && "$mkdtimg_tool" cfg_create "$image_tmp" "$config_name")
image_magic=$(blob_magic "$image_tmp")
[[ $image_magic == d7b7ab1e ]] || \
  die "mkdtimg output lacks the Android DT table magic (found $image_magic)"
"$mkdtimg_tool" dump "$image_tmp" >"$dump_tmp"
image_hash=$(sha256sum "$image_tmp")
image_hash=${image_hash%% *}
printf '%s  %s\n' "$image_hash" "$(basename "$output")" >"$hash_tmp"
cp -- "$config" "$config_tmp"

{
  printf 'format_version=2\n'
  printf 'created_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'mkdtimg=%s\n' "$mkdtimg_tool"
  printf 'mkdtimg_version=%s\n' "$(tool_version "$mkdtimg_tool")"
  printf 'mkdtimg_sha256=%s\n' "$(sha256sum "$mkdtimg_tool" | awk '{print $1}')"
  printf 'config=%s\n' "$config"
  printf 'config_sha256=%s\n' "$(sha256sum "$config" | awk '{print $1}')"
  printf 'page_size=%s\n' "$page_size"
  printf 'entry_count=%d\n' "${#entry_paths[@]}"
  index=0
  for entry_path in "${entry_paths[@]}"; do
    printf 'entry_%d=%s\n' "$index" "$entry_path"
    printf 'entry_%d_sha256=%s\n' "$index" "$(sha256sum "$entry_path" | awk '{print $1}')"
    ((index += 1))
  done
  printf 'image_sha256=%s\n' "$image_hash"
  printf 'claim_limit=Container construction only; no selector, signing, bootloader, or hardware compatibility claim.\n'
} >"$manifest_tmp"

mv -f -- "$image_tmp" "$output"
mv -f -- "$dump_tmp" "$dump_output"
mv -f -- "$hash_tmp" "$hash_output"
mv -f -- "$config_tmp" "$config_output"
mv -f -- "$manifest_tmp" "$manifest_output"
printf 'DT table image and evidence written to %s and sidecars.\n' "$output"
