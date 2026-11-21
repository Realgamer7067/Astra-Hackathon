#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

usage() {
  cat <<'EOF'
Build explicit Linux kernel artifacts in an out-of-tree directory and preserve
source, toolchain, command, log, and output provenance.

Usage:
  build-kernel-artifacts.sh --tree DIR --out DIR [configuration] \
    --target TARGET [--target TARGET ...] [options]

Configuration (choose at most one):
  --config-target TARGET  Run a verified Kbuild config target.
  --config-file FILE      Copy a known config to OUT/.config, then olddefconfig.
  If neither is supplied, OUT/.config must already exist and olddefconfig runs.

Options:
  --arch ARCH             Kbuild ARCH (default: arm64; ARM32 normally uses arm).
  --jobs N                Parallel jobs (default: detected CPU count).
  --llvm VALUE            LLVM=1, LLVM=-<suffix>, or LLVM=<path-ending-in-/>.
  --cross-compile PREFIX  Pass CROSS_COMPILE=PREFIX consistently.
  --make-arg NAME=VALUE   Additional Kbuild variable; repeat as needed.
  --target TARGET         Exact build target; repeat as needed.
  --reuse-output          Permit a non-empty O= directory and compare its
                          pre/post content hashes. Without this, non-empty O=
                          is refused to prevent stale-artifact attribution.
  --dry-run               Validate inputs and print commands without writing.
  -h, --help              Show this help.

Evidence is stored under OUT/.mainline-port-evidence/run.*. The artifact hash
file contains every regular output file that is new or content-changed in this
run, including zImage, modules and vendor-specific outputs. Complete pre/post
inventories, including symlinks, make unchanged and deleted paths visible when
--reuse-output is used.

Safety and scope:
  * OUT must be outside the Git worktree/source tree.
  * This script never cleans, installs, signs, packs, flashes, or communicates
    with a device.
  * A successful build proves compilation only, not target compatibility.
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

command_string() {
  local rendered
  printf -v rendered '%q ' "$@"
  printf '%s' "${rendered% }"
}

path_is_within() {
  local child=${1%/}/ parent=${2%/}/
  [[ $child == "$parent"* ]]
}

is_relevant_untracked_source() {
  local path=$1 base=${1##*/}
  case "$base" in
    Kconfig*|Makefile*|*defconfig|*.config) return 0 ;;
  esac
  case "$path" in
    *.c|*.h|*.S|*.s|*.rs|*.dts|*.dtsi|*.dtso|*.yaml|*.yml|*.json|*.toml|*.patch|*.diff|*.sh|*.py)
      return 0 ;;
  esac
  return 1
}

tree=
out=
arch=arm64
config_target=
config_file=
jobs=
llvm=
cross_compile=
reuse_output=false
dry_run=false
declare -a targets=()
declare -a make_args=()

while (($#)); do
  case "$1" in
    --tree)
      need_value "$@"; tree=$2; shift 2 ;;
    --out)
      need_value "$@"; out=$2; shift 2 ;;
    --arch)
      need_value "$@"; arch=$2; shift 2 ;;
    --config-target)
      need_value "$@"; config_target=$2; shift 2 ;;
    --config-file)
      need_value "$@"; config_file=$2; shift 2 ;;
    --jobs)
      need_value "$@"; jobs=$2; shift 2 ;;
    --llvm)
      need_value "$@"; llvm=$2; shift 2 ;;
    --cross-compile)
      need_value "$@"; cross_compile=$2; shift 2 ;;
    --make-arg)
      need_value "$@"; make_args+=("$2"); shift 2 ;;
    --target)
      need_value "$@"; targets+=("$2"); shift 2 ;;
    --reuse-output)
      reuse_output=true; shift ;;
    --dry-run)
      dry_run=true; shift ;;
    -h|--help)
      usage; exit 0 ;;
    --)
      shift
      (($# == 0)) || die "positional arguments are not accepted; use --target"
      ;;
    *)
      die "unknown argument: $1" ;;
  esac
done

[[ -n $tree ]] || die "--tree is required"
[[ -n $out ]] || die "--out is required"
[[ $tree != *$'\n'* && $tree != *$'\t'* && $out != *$'\n'* && $out != *$'\t'* ]] || \
  die "source and output paths must not contain tabs/newlines"
((${#targets[@]} > 0)) || die "at least one --target is required"
[[ ! ( -n $config_target && -n $config_file ) ]] || \
  die "choose only one of --config-target and --config-file"
[[ $arch =~ ^[A-Za-z0-9_.+-]+$ ]] || die "invalid ARCH: $arch"

if [[ -n $llvm ]]; then
  if [[ $llvm == 1 || $llvm =~ ^-[A-Za-z0-9._+-]+$ ]]; then
    :
  elif [[ $llvm == /*/ ]]; then
    [[ -d ${llvm%/} ]] || die "LLVM tool directory does not exist: ${llvm%/}"
  else
    die "--llvm must be 1, a suffix such as -14, or an absolute path ending in /"
  fi
fi
[[ $cross_compile != *$'\n'* && $cross_compile != *$'\t'* && $cross_compile != *' '* ]] || \
  die "--cross-compile must not contain whitespace"

if [[ -z $jobs ]]; then
  if command -v nproc >/dev/null 2>&1; then jobs=$(nproc); else jobs=1; fi
fi
[[ $jobs =~ ^[1-9][0-9]*$ ]] || die "--jobs must be a positive integer"

for required in git find realpath; do
  command -v "$required" >/dev/null 2>&1 || die "$required is not installed"
done

[[ -d $tree ]] || die "kernel tree does not exist: $tree"
[[ -f $tree/Makefile ]] || die "no top-level Makefile found in: $tree"
tree_abs=$(realpath "$tree")
out_abs=$(realpath -m "$out")
[[ $out_abs != / ]] || die "refusing to use / as the output directory"
[[ $out_abs != "$tree_abs" ]] || die "output directory must differ from source tree"
[[ ! -e $out_abs || -d $out_abs ]] || die "output path exists and is not a directory: $out_abs"

source_boundary=$tree_abs
repo_root=
tree_pathspec=.
if git -C "$tree_abs" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  repo_root=$(git -C "$tree_abs" rev-parse --show-toplevel)
  source_boundary=$(realpath "$repo_root")
  tree_pathspec=$(realpath --relative-to="$source_boundary" "$tree_abs")
  [[ -n $tree_pathspec ]] || tree_pathspec=.
fi
path_is_within "$out_abs" "$source_boundary" && \
  die "OUT must be outside the source Git worktree: $source_boundary"

if [[ -d $out_abs ]] && [[ -n $(find "$out_abs" -mindepth 1 -maxdepth 1 -print -quit) ]] && ! $reuse_output; then
  die "OUT is non-empty; choose a new directory or pass --reuse-output explicitly"
fi

if [[ -n $config_file ]]; then
  [[ -f $config_file ]] || die "config file does not exist: $config_file"
  config_file=$(realpath "$config_file")
fi

validate_target() {
  local target=$1
  [[ $target != -* && $target != *'='* && $target != *[[:space:]]* && -n $target ]] || \
    die "invalid make target: $target"
  case "$target" in
    clean|mrproper|distclean|clobber|install|modules_install|dtbs_install|headers_install|firmware_install)
      die "target is outside this build-only script's scope: $target" ;;
  esac
}

[[ -z $config_target ]] || validate_target "$config_target"
for target in "${targets[@]}"; do validate_target "$target"; done

declare -A make_values=()
for arg in "${make_args[@]}"; do
  [[ $arg != *$'\n'* && $arg != *$'\t'* ]] || die "--make-arg must not contain tabs/newlines"
  [[ $arg =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] || \
    die "--make-arg must be a NAME=VALUE assignment: $arg"
  name=${arg%%=*}
  case "$name" in
    O|KBUILD_OUTPUT|ARCH|LLVM|CROSS_COMPILE|MAKEFLAGS|SHELL)
      die "use the script option instead of overriding $name" ;;
  esac
  make_values[$name]=${arg#*=}
done

declare -a make_base=(make -C "$tree_abs" "O=$out_abs" "ARCH=$arch")
[[ -z $llvm ]] || make_base+=("LLVM=$llvm")
[[ -z $cross_compile ]] || make_base+=("CROSS_COMPILE=$cross_compile")
make_base+=("${make_args[@]}")

if [[ -n $config_target ]]; then
  declare -a config_command=("${make_base[@]}" "$config_target")
elif [[ -n $config_file ]]; then
  declare -a config_command=("${make_base[@]}" olddefconfig)
else
  [[ -f $out_abs/.config ]] || \
    die "no configuration supplied and $out_abs/.config does not exist"
  declare -a config_command=("${make_base[@]}" olddefconfig)
fi
declare -a build_command=("${make_base[@]}" "-j$jobs" "${targets[@]}")

if $dry_run; then
  printf 'Validated build plan (no files written):\n'
  printf '  source provenance will be captured before OUT is created or modified\n'
  if [[ -n $config_file ]]; then
    print_command install -m 0644 -- "$config_file" "$out_abs/.config"
  fi
  print_command "${config_command[@]}"
  print_command "${build_command[@]}"
  exit 0
fi

for required in make sha256sum sort awk stat mktemp cmp cp readlink sed wc date dirname install tee mkdir rm; do
  command -v "$required" >/dev/null 2>&1 || die "$required is not installed"
done

# Capture source state before creating or changing OUT. Resolve TMPDIR first so
# even temporary evidence cannot make the source worktree look dirty.
capture_base=${TMPDIR:-/tmp}
[[ -d $capture_base ]] || die "temporary directory base does not exist: $capture_base"
capture_base=$(realpath "$capture_base")
path_is_within "$capture_base" "$source_boundary" && \
  die "TMPDIR must be outside the source worktree before provenance capture"
capture_tmp=$(mktemp -d "$capture_base/mainline-phone-port-build.XXXXXX")
run_dir=
manifest_file=
build_finished=false
cleanup() {
  local rc=$?
  if [[ -n $manifest_file && -f $manifest_file ]] && ! $build_finished; then
    printf 'build_result=failed\nexit_code=%d\n' "$rc" >>"$manifest_file"
  fi
  rm -rf -- "$capture_tmp"
  exit "$rc"
}
trap cleanup EXIT

capture_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
source_kind=non-git
source_commit=unavailable
source_branch=unavailable
source_dirty=unknown
untracked_copied=0

if [[ -n $repo_root ]]; then
  source_kind=git
  source_commit=$(git -C "$repo_root" rev-parse HEAD)
  source_branch=$(git -C "$repo_root" symbolic-ref --quiet --short HEAD || printf 'detached')
  git -C "$repo_root" status --porcelain=v1 -uall -- "$tree_pathspec" >"$capture_tmp/source-status-before"
  git -C "$repo_root" diff --binary HEAD -- "$tree_pathspec" >"$capture_tmp/source-tracked.patch"
  git -C "$repo_root" submodule status --recursive -- "$tree_pathspec" >"$capture_tmp/source-submodules-before" 2>&1 || true
  git -C "$repo_root" submodule foreach --recursive --quiet \
    'printf "submodule=%s\n" "$displaypath"; git rev-parse HEAD; git status --porcelain=v1 -uall' \
    >"$capture_tmp/source-submodule-worktrees-before" 2>&1 || true
  if [[ -s $capture_tmp/source-status-before ]]; then source_dirty=yes; else source_dirty=no; fi

  mkdir -p "$capture_tmp/untracked-sources"
  : >"$capture_tmp/source-untracked.sha256"
  while IFS= read -r -d '' relative; do
    if [[ $relative == *$'\n'* || $relative == *$'\t'* ]]; then
      printf 'Skipped control-character path: %q\n' "$relative" >>"$capture_tmp/source-untracked-skipped"
      continue
    fi
    is_relevant_untracked_source "$relative" || continue
    source_path=$repo_root/$relative
    destination=$capture_tmp/untracked-sources/$relative
    mkdir -p -- "$(dirname "$destination")"
    cp -a -- "$source_path" "$destination"
    if [[ -L $destination ]]; then
      link_target=$(readlink "$destination")
      digest=$(printf '%s' "$link_target" | sha256sum | awk '{print $1}')
      printf '%s  %s [symlink-target]\n' "$digest" "$relative" >>"$capture_tmp/source-untracked.sha256"
    elif [[ -f $destination ]]; then
      digest=$(sha256sum "$destination" | awk '{print $1}')
      printf '%s  %s\n' "$digest" "$relative" >>"$capture_tmp/source-untracked.sha256"
    fi
    ((untracked_copied += 1))
  done < <(git -C "$repo_root" ls-files --others --exclude-standard -z -- "$tree_pathspec")
else
  printf 'Source is not a Git worktree.\n' >"$capture_tmp/source-status-before"
  printf 'No Git diff is available.\n' >"$capture_tmp/source-tracked.patch"
  printf 'No Git submodule state is available.\n' >"$capture_tmp/source-submodules-before"
  printf 'No Git submodule worktree state is available.\n' >"$capture_tmp/source-submodule-worktrees-before"
  : >"$capture_tmp/source-untracked.sha256"
fi

mkdir -p -- "$out_abs/.mainline-port-evidence"
run_dir=$(mktemp -d "$out_abs/.mainline-port-evidence/run.XXXXXX")
cp -a -- "$capture_tmp/." "$run_dir/"

log_file=$run_dir/build.log
manifest_file=$run_dir/manifest
pre_inventory=$run_dir/output-before.tsv
post_inventory=$run_dir/output-after.tsv
artifact_hashes=$run_dir/artifacts-new-or-changed.sha256
deleted_outputs=$run_dir/outputs-deleted.txt
toolchain_file=$run_dir/toolchain.manifest
: >"$log_file"

inventory_output() {
  local destination=$1 item relative kind size digest link_target
  : >"$destination"
  while IFS= read -r -d '' item; do
    relative=${item#"$out_abs"/}
    if [[ $relative == *$'\n'* || $relative == *$'\t'* ]]; then
      die "output path contains a tab/newline and cannot be inventoried safely: $relative"
    fi
    if [[ -L $item ]]; then
      kind=symlink
      link_target=$(readlink "$item")
      size=${#link_target}
      digest=$(printf '%s' "$link_target" | sha256sum | awk '{print $1}')
    else
      kind=file
      size=$(stat -c %s "$item")
      digest=$(sha256sum "$item" | awk '{print $1}')
    fi
    printf '%s\t%s\t%s\t%s\n' "$relative" "$kind" "$size" "$digest" >>"$destination"
  done < <(find "$out_abs" \
    -path "$out_abs/.mainline-port-evidence" -prune -o \
    \( -type f -o -type l \) -print0 | LC_ALL=C sort -z)
}

run_logged() {
  printf '\n$ ' | tee -a "$log_file"
  printf '%q ' "$@" | tee -a "$log_file"
  printf '\n' | tee -a "$log_file"
  "$@" 2>&1 | tee -a "$log_file"
}

inventory_output "$pre_inventory"
config_cmd_text=$(command_string "${config_command[@]}")
build_cmd_text=$(command_string "${build_command[@]}")
{
  printf 'format_version=2\n'
  printf 'source_captured_utc=%s\n' "$capture_utc"
  printf 'source_tree=%s\n' "$tree_abs"
  printf 'source_kind=%s\n' "$source_kind"
  printf 'source_repo_root=%s\n' "${repo_root:-unavailable}"
  printf 'source_pathspec=%s\n' "$tree_pathspec"
  printf 'source_branch=%s\n' "$source_branch"
  printf 'source_commit=%s\n' "$source_commit"
  printf 'source_dirty=%s\n' "$source_dirty"
  printf 'untracked_source_files_copied=%d\n' "$untracked_copied"
  printf 'architecture=%s\n' "$arch"
  printf 'llvm=%s\n' "${llvm:-unset}"
  printf 'cross_compile=%s\n' "${cross_compile:-unset}"
  printf 'reuse_output=%s\n' "$reuse_output"
  printf 'config_command=%s\n' "$config_cmd_text"
  printf 'build_command=%s\n' "$build_cmd_text"
  printf 'requested_target_count=%d\n' "${#targets[@]}"
  index=0
  for target in "${targets[@]}"; do
    printf 'requested_target_%d=%s\n' "$index" "$target"
    ((index += 1))
  done
  printf 'artifact_hash_basis=all new or content-changed regular files under OUT; symlinks are inventoried; .mainline-port-evidence is excluded\n'
  printf 'output_inventory_before=%s\n' "$pre_inventory"
  printf 'build_log=%s\n' "$log_file"
} >"$manifest_file"

if [[ -n $config_file ]]; then
  run_logged install -m 0644 -- "$config_file" "$out_abs/.config"
fi
run_logged "${config_command[@]}"
run_logged "${build_command[@]}"

inventory_output "$post_inventory"
awk -F '\t' '
  FILENAME == ARGV[1] { before[$1] = $4; next }
  FILENAME == ARGV[2] {
    after[$1] = 1
    if ($2 == "file" && (!($1 in before) || before[$1] != $4)) print $4 "  " $1
  }
' "$pre_inventory" "$post_inventory" >"$artifact_hashes"
awk -F '\t' '
  FILENAME == ARGV[1] { before[$1] = 1; order[++count] = $1; next }
  FILENAME == ARGV[2] { after[$1] = 1; next }
  END { for (i = 1; i <= count; i++) if (!(order[i] in after)) print order[i] }
' "$pre_inventory" "$post_inventory" >"$deleted_outputs"

llvm_tool_name() {
  local base=$1
  if [[ $llvm == 1 ]]; then
    printf '%s' "$base"
  elif [[ $llvm == */ ]]; then
    printf '%s%s' "$llvm" "$base"
  else
    printf '%s%s' "$base" "$llvm"
  fi
}

make_value_or() {
  local name=$1 fallback=$2
  if [[ -v make_values[$name] ]]; then printf '%s' "${make_values[$name]}"; else printf '%s' "$fallback"; fi
}

record_tool() {
  local label=$1 specification=$2 token resolved version version_output digest index=0
  printf '%s_spec=%q\n' "$label" "$specification" >>"$toolchain_file"
  local old_ifs=$IFS
  IFS=' ' read -r -a components <<<"$specification"
  IFS=$old_ifs
  for token in "${components[@]}"; do
    [[ -n $token && $token != -* && $token != *=* ]] || continue
    resolved=$(command -v "$token" 2>/dev/null || true)
    [[ -n $resolved ]] || continue
    resolved=$(realpath "$resolved")
    if version_output=$("$resolved" --version 2>&1); then
      version=$(printf '%s\n' "$version_output" | sed -n '1p')
    else
      version=unavailable
    fi
    digest=unavailable
    [[ -f $resolved ]] && digest=$(sha256sum "$resolved" | awk '{print $1}')
    printf '%s_component_%d_path=%s\n' "$label" "$index" "$resolved" >>"$toolchain_file"
    printf '%s_component_%d_version=%s\n' "$label" "$index" "${version:-unavailable}" >>"$toolchain_file"
    printf '%s_component_%d_sha256=%s\n' "$label" "$index" "$digest" >>"$toolchain_file"
    ((index += 1))
  done
  [[ $index -gt 0 ]] || printf '%s_resolution=unavailable\n' "$label" >>"$toolchain_file"
}

{
  printf 'format_version=1\n'
  printf 'captured_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'claim_limit=resolved configured tools after the build; this does not prove every executable was invoked unless the build log shows it\n'
} >"$toolchain_file"
if [[ -n $llvm ]]; then
  default_cc=$(llvm_tool_name clang)
  default_ld=$(llvm_tool_name ld.lld)
  default_ar=$(llvm_tool_name llvm-ar)
  default_nm=$(llvm_tool_name llvm-nm)
  default_strip=$(llvm_tool_name llvm-strip)
  default_objcopy=$(llvm_tool_name llvm-objcopy)
  default_objdump=$(llvm_tool_name llvm-objdump)
  default_readelf=$(llvm_tool_name llvm-readelf)
else
  default_cc=${cross_compile}gcc
  default_ld=${cross_compile}ld
  default_ar=${cross_compile}ar
  default_nm=${cross_compile}nm
  default_strip=${cross_compile}strip
  default_objcopy=${cross_compile}objcopy
  default_objdump=${cross_compile}objdump
  default_readelf=${cross_compile}readelf
fi
record_tool make make
record_tool cc "$(make_value_or CC "$default_cc")"
record_tool ld "$(make_value_or LD "$default_ld")"
record_tool ar "$(make_value_or AR "$default_ar")"
record_tool nm "$(make_value_or NM "$default_nm")"
record_tool strip "$(make_value_or STRIP "$default_strip")"
record_tool objcopy "$(make_value_or OBJCOPY "$default_objcopy")"
record_tool objdump "$(make_value_or OBJDUMP "$default_objdump")"
record_tool readelf "$(make_value_or READELF "$default_readelf")"
record_tool hostcc "$(make_value_or HOSTCC gcc)"

if [[ -v make_values[DTC] ]]; then
  dtc_spec=${make_values[DTC]}
elif [[ -x $out_abs/scripts/dtc/dtc ]]; then
  dtc_spec=$out_abs/scripts/dtc/dtc
else
  dtc_spec=dtc
fi
record_tool dtc "$dtc_spec"
record_tool pahole "$(make_value_or PAHOLE pahole)"

source_state_changed=not-applicable
if [[ -n $repo_root ]]; then
  git -C "$repo_root" status --porcelain=v1 -uall -- "$tree_pathspec" >"$run_dir/source-status-after"
  git -C "$repo_root" submodule status --recursive -- "$tree_pathspec" >"$run_dir/source-submodules-after" 2>&1 || true
  git -C "$repo_root" submodule foreach --recursive --quiet \
    'printf "submodule=%s\n" "$displaypath"; git rev-parse HEAD; git status --porcelain=v1 -uall' \
    >"$run_dir/source-submodule-worktrees-after" 2>&1 || true
  source_commit_after=$(git -C "$repo_root" rev-parse HEAD)
  if cmp -s "$run_dir/source-status-before" "$run_dir/source-status-after" && \
     cmp -s "$run_dir/source-submodules-before" "$run_dir/source-submodules-after" && \
     cmp -s "$run_dir/source-submodule-worktrees-before" "$run_dir/source-submodule-worktrees-after" && \
     [[ $source_commit == "$source_commit_after" ]]; then
    source_state_changed=no
  else
    source_state_changed=yes
  fi
fi

artifact_count=$(wc -l <"$artifact_hashes")
deleted_count=$(wc -l <"$deleted_outputs")
if ((artifact_count == 0)); then
  printf 'warning: build succeeded but no output file content changed\n' | tee -a "$log_file" >&2
fi
{
  printf 'completed_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'source_state_changed_during_build=%s\n' "$source_state_changed"
  printf 'output_inventory_after=%s\n' "$post_inventory"
  printf 'new_or_changed_output_count=%d\n' "$artifact_count"
  printf 'new_or_changed_output_hashes=%s\n' "$artifact_hashes"
  printf 'deleted_output_count=%d\n' "$deleted_count"
  printf 'deleted_outputs=%s\n' "$deleted_outputs"
  printf 'toolchain_manifest=%s\n' "$toolchain_file"
  printf 'build_result=success\n'
} >>"$manifest_file"
build_finished=true
printf 'Build completed. Evidence directory: %s\n' "$run_dir"
