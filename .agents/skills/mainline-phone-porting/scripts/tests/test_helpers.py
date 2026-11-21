#!/usr/bin/env python3
"""Regression tests for the skill's deterministic evidence helpers."""

from __future__ import annotations

import os
import hashlib
import json
import pathlib
import stat
import subprocess
import tempfile
import textwrap
import unittest


SCRIPTS = pathlib.Path(__file__).resolve().parents[1]
BUILD = SCRIPTS / "build-kernel-artifacts.sh"
INDEX = SCRIPTS / "index-kernel-evidence.py"
APPLY_OVERLAYS = SCRIPTS / "apply-and-verify-dt-overlays.sh"
PACK_DTBO = SCRIPTS / "pack-dtbo-image.sh"


MOCK_MAKEFILE = """\
.PHONY: test_defconfig olddefconfig zImage Image dtbs modules

test_defconfig:
\t@mkdir -p "$(O)"
\t@printf '%s\\n' 'CONFIG_TEST=y' > "$(O)/.config"

olddefconfig:
\t@test -f "$(O)/.config"

zImage:
\t@mkdir -p "$(O)/arch/$(ARCH)/boot"
\t@printf '%s\\n' 'zImage $(BUILD_MARK)' > "$(O)/arch/$(ARCH)/boot/zImage"

Image:
\t@mkdir -p "$(O)/arch/$(ARCH)/boot"
\t@printf '%s\\n' 'Image $(BUILD_MARK)' > "$(O)/arch/$(ARCH)/boot/Image"

dtbs:
\t@mkdir -p "$(O)/arch/$(ARCH)/boot/dts/test"
\t@printf '%s\\n' 'dtb $(BUILD_MARK)' > "$(O)/arch/$(ARCH)/boot/dts/test/board.dtb"

modules:
\t@mkdir -p "$(O)/drivers/test"
\t@printf '%s\\n' 'module $(BUILD_MARK)' > "$(O)/drivers/test/test.ko"
"""


def run(
    *argv: object,
    cwd: pathlib.Path | None = None,
    check: bool = True,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    if extra_env:
        environment.update(extra_env)
    result = subprocess.run(
        [str(item) for item in argv],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {' '.join(map(str, argv))}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def write_executable(path: pathlib.Path, content: str) -> None:
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class HelperRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="mainline-phone-porting-tests-")
        self.root = pathlib.Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def make_repo(self) -> pathlib.Path:
        repo = self.root / "kernel"
        repo.mkdir()
        (repo / "Makefile").write_text(MOCK_MAKEFILE, encoding="utf-8")
        (repo / "drivers").mkdir()
        (repo / "drivers" / "base.c").write_text("int base_driver;\n", encoding="utf-8")
        run("git", "init", "-q", repo)
        run("git", "-C", repo, "config", "user.name", "Regression Test")
        run("git", "-C", repo, "config", "user.email", "test@example.invalid")
        run("git", "-C", repo, "add", "Makefile", "drivers/base.c")
        run("git", "-C", repo, "commit", "-qm", "baseline")
        return repo

    @staticmethod
    def new_run_dir(output: pathlib.Path, before: set[pathlib.Path] | None = None) -> pathlib.Path:
        runs = set((output / ".mainline-port-evidence").glob("run.*"))
        if before is not None:
            runs -= before
        if len(runs) != 1:
            raise AssertionError(f"expected one evidence run, found {sorted(runs)}")
        return runs.pop()

    def test_build_hashes_arm_zimage_module_and_untracked_source(self) -> None:
        repo = self.make_repo()
        new_dts = repo / "arch" / "arm" / "boot" / "dts" / "test" / "new-board.dts"
        new_dts.parent.mkdir(parents=True)
        new_dts.write_text('/dts-v1/; / { model = "test"; };\n', encoding="utf-8")
        output = self.root / "out-arm"

        run(
            BUILD,
            "--tree", repo,
            "--out", output,
            "--arch", "arm",
            "--config-target", "test_defconfig",
            "--target", "zImage",
            "--target", "modules",
            "--jobs", "1",
        )
        evidence = self.new_run_dir(output)
        hashes = (evidence / "artifacts-new-or-changed.sha256").read_text(encoding="utf-8")
        self.assertIn("arch/arm/boot/zImage", hashes)
        self.assertIn("drivers/test/test.ko", hashes)
        verified = run("sha256sum", "-c", evidence / "artifacts-new-or-changed.sha256", cwd=output)
        self.assertIn("arch/arm/boot/zImage: OK", verified.stdout)
        self.assertIn("drivers/test/test.ko: OK", verified.stdout)
        self.assertTrue((evidence / "untracked-sources" / new_dts.relative_to(repo)).is_file())
        status_before = (evidence / "source-status-before").read_text(encoding="utf-8")
        self.assertIn("new-board.dts", status_before)
        self.assertNotIn(str(output), status_before)

    def test_reuse_does_not_attribute_unchanged_stale_dtb(self) -> None:
        repo = self.make_repo()
        output = self.root / "out-reuse"
        run(
            BUILD,
            "--tree", repo,
            "--out", output,
            "--config-target", "test_defconfig",
            "--target", "dtbs",
            "--make-arg", "BUILD_MARK=first",
            "--jobs", "1",
        )
        existing_runs = set((output / ".mainline-port-evidence").glob("run.*"))
        run(
            BUILD,
            "--tree", repo,
            "--out", output,
            "--reuse-output",
            "--config-target", "test_defconfig",
            "--target", "Image",
            "--make-arg", "BUILD_MARK=second",
            "--jobs", "1",
        )
        evidence = self.new_run_dir(output, existing_runs)
        hashes = (evidence / "artifacts-new-or-changed.sha256").read_text(encoding="utf-8")
        inventory = (evidence / "output-after.tsv").read_text(encoding="utf-8")
        self.assertIn("arch/arm64/boot/Image", hashes)
        self.assertNotIn("board.dtb", hashes)
        self.assertIn("board.dtb", inventory)

    def test_nonempty_and_in_tree_outputs_are_refused(self) -> None:
        repo = self.make_repo()
        nonempty = self.root / "nonempty"
        nonempty.mkdir()
        (nonempty / "stale").write_text("stale\n", encoding="utf-8")
        result = run(
            BUILD,
            "--tree", repo,
            "--out", nonempty,
            "--config-target", "test_defconfig",
            "--target", "Image",
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("non-empty", result.stderr)

        result = run(
            BUILD,
            "--tree", repo,
            "--out", repo / "out",
            "--config-target", "test_defconfig",
            "--target", "Image",
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside", result.stderr)

        in_tree_tmp = repo / "tmp"
        in_tree_tmp.mkdir()
        result = run(
            BUILD,
            "--tree", repo,
            "--out", self.root / "outside-output",
            "--config-target", "test_defconfig",
            "--target", "Image",
            extra_env={"TMPDIR": str(in_tree_tmp)},
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("TMPDIR must be outside", result.stderr)

    def test_llvm_suffix_is_recorded_as_resolved_tool_names(self) -> None:
        repo = self.make_repo()
        output = self.root / "out-llvm"
        run(
            BUILD,
            "--tree", repo,
            "--out", output,
            "--llvm", "-14",
            "--config-target", "test_defconfig",
            "--target", "Image",
            "--jobs", "1",
        )
        evidence = self.new_run_dir(output)
        tools = (evidence / "toolchain.manifest").read_text(encoding="utf-8")
        self.assertIn("cc_spec=clang-14", tools)
        self.assertIn("ld_spec=ld.lld-14", tools)

    def test_index_defaults_to_head_and_worktree_mode_preserves_changes(self) -> None:
        repo = self.make_repo()
        tracked = repo / "drivers" / "base.c"
        tracked.write_text("int dirty_only_term;\n", encoding="utf-8")
        untracked = repo / "arch" / "arm64" / "boot" / "dts" / "test" / "new.dts"
        untracked.parent.mkdir(parents=True)
        untracked.write_text('/dts-v1/; / { model = "untracked_only_term"; };\n', encoding="utf-8")
        unpreserved = repo / "notes.txt"
        unpreserved.write_text("non_source_untracked_term\n", encoding="utf-8")

        committed_report = self.root / "committed.md"
        run(INDEX, "--tree", repo, "--term", "dirty_only_term", "--output", committed_report)
        committed = committed_report.read_text(encoding="utf-8")
        self.assertIn("committed tree object", committed)
        self.assertIn("No matches in the selected source snapshot", committed)

        working_report = self.root / "working.md"
        run(
            INDEX,
            "--tree", repo,
            "--working-tree",
            "--term", "dirty_only_term",
            "--term", "untracked_only_term",
            "--term", "non_source_untracked_term",
            "--output", working_report,
        )
        working = working_report.read_text(encoding="utf-8")
        evidence = pathlib.Path(f"{working_report}.evidence")
        self.assertIn("drivers/base.c", working)
        self.assertIn("new.dts", working)
        non_source_section = working.split(
            "## Literal term: non_source_untracked_term", 1
        )[1].split("## Manual follow-up", 1)[0]
        self.assertIn("No matches in the selected source snapshot", non_source_section)
        self.assertFalse((evidence / "untracked-sources" / unpreserved.relative_to(repo)).exists())
        self.assertIn("dirty_only_term", (evidence / "tracked.patch").read_text(encoding="utf-8"))
        self.assertTrue((evidence / "untracked-sources" / untracked.relative_to(repo)).is_file())
        metadata = json.loads((evidence / "manifest.json").read_text(encoding="utf-8"))
        for name, expected in metadata["sidecar_sha256"].items():
            actual = hashlib.sha256((evidence / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected)

    def test_index_rejects_empty_terms_and_output_clobber(self) -> None:
        repo = self.make_repo()
        blank = run(INDEX, "--tree", repo, "--term", "   ", check=False)
        self.assertNotEqual(blank.returncode, 0)
        self.assertIn("must not be empty", blank.stderr)

        output = self.root / "report.md"
        output.write_text("keep\n", encoding="utf-8")
        result = run(INDEX, "--tree", repo, "--term", "base", "--output", output, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_text(encoding="utf-8"), "keep\n")

        in_tree = run(
            INDEX,
            "--tree", repo,
            "--working-tree",
            "--term", "base",
            "--output", repo / "report.md",
            check=False,
        )
        self.assertNotEqual(in_tree.returncode, 0)
        self.assertIn("evidence must be outside", in_tree.stderr)

    def test_dt_helpers_record_tool_fingerprints(self) -> None:
        tools = self.root / "tools"
        tools.mkdir()
        fdtoverlay = tools / "fdtoverlay"
        dtc = tools / "dtc"
        mkdtimg = tools / "mkdtimg"
        write_executable(
            fdtoverlay,
            """
            #!/usr/bin/env python3
            import pathlib, shutil, sys
            if "--version" in sys.argv:
                print("mock-fdtoverlay 1")
                raise SystemExit(0)
            source = pathlib.Path(sys.argv[sys.argv.index("-i") + 1])
            output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
            shutil.copyfile(source, output)
            """,
        )
        write_executable(
            dtc,
            """
            #!/usr/bin/env python3
            import pathlib, sys
            if "--version" in sys.argv:
                print("mock-dtc 1")
                raise SystemExit(0)
            output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
            output.write_text('/dts-v1/; / { compatible = "test,test"; };\\n')
            """,
        )
        write_executable(
            mkdtimg,
            """
            #!/usr/bin/env python3
            import pathlib, sys
            if "--version" in sys.argv:
                print("mock-mkdtimg 1")
            elif sys.argv[1] == "cfg_create":
                pathlib.Path(sys.argv[2]).write_bytes(bytes.fromhex("d7b7ab1e") + b"\\0" * 60)
            elif sys.argv[1] == "dump":
                print("magic = d7b7ab1e")
            else:
                raise SystemExit(2)
            """,
        )
        base = self.root / "base.dtb"
        overlay = self.root / "overlay.dtbo"
        base.write_bytes(bytes.fromhex("d00dfeed") + b"\0" * 12)
        overlay.write_bytes(bytes.fromhex("d00dfeed") + b"\0" * 12)
        merged = self.root / "merged.dtb"
        run(
            APPLY_OVERLAYS,
            "--base", base,
            "--overlay", overlay,
            "--output", merged,
            "--fdtoverlay", fdtoverlay,
            "--dtc", dtc,
        )
        overlay_manifest = pathlib.Path(f"{merged}.manifest").read_text(encoding="utf-8")
        self.assertIn("fdtoverlay_version=mock-fdtoverlay 1", overlay_manifest)
        self.assertIn("fdtoverlay_sha256=", overlay_manifest)
        self.assertIn("dtc_sha256=", overlay_manifest)

        config = self.root / "dtboimg.cfg"
        config.write_text("  page_size=4096\n\noverlay.dtbo\n  id=0x1\n", encoding="utf-8")
        image = self.root / "dtbo.img"
        run(PACK_DTBO, "--config", config, "--output", image, "--mkdtimg", mkdtimg)
        pack_manifest = pathlib.Path(f"{image}.manifest").read_text(encoding="utf-8")
        self.assertIn("mkdtimg_version=mock-mkdtimg 1", pack_manifest)
        self.assertIn("mkdtimg_sha256=", pack_manifest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
