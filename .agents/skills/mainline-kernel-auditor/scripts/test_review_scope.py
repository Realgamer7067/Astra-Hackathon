#!/usr/bin/env python3
"""End-to-end tests for the audit helper: runs only on disposable temp Git repos."""
import csv
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('review_scope.py')


def run(*cmd, cwd=None, ok=True):
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if ok and proc.returncode:
        raise AssertionError(f"{' '.join(map(str, cmd))}: {proc.stderr}\n{proc.stdout}")
    return proc


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'linux'
        self.repo.mkdir()
        self.out = self.root / 'audit'
        run('git', 'init', '-q', str(self.repo))
        run('git', 'config', 'user.email', 'test@example.invalid', cwd=self.repo)
        run('git', 'config', 'user.name', 'Test', cwd=self.repo)
        (self.repo / '.gitignore').write_text('scratch/\n', encoding='utf-8')
        (self.repo / 'main.c').write_text('int main(void) {\n  return 0;\n}\n')
        (self.repo / 'to-delete.c').write_text('int legacy = 1;\n')
        (self.repo / 'blob.bin').write_bytes(b'\0\x99\x01')
        run('git', 'add', '.', cwd=self.repo)
        run('git', 'commit', '-qm', 'base', cwd=self.repo)
        self.base = run('git', 'rev-parse', 'HEAD', cwd=self.repo).stdout.strip()

    def inventory(self):
        return run(sys.executable, str(SCRIPT), 'inventory', '--repo', str(self.repo), '--base', self.base, '--out', str(self.out), ok=False)

    def test_history_and_drift_and_binary(self):
        (self.repo / 'main.c').write_text('int main(void) {\n  return 22;\n}\n')
        (self.repo / 'to-delete.c').unlink()
        (self.repo / 'blob.bin').write_bytes(b'\0\x88\x09')
        run('git', 'add', '.', cwd=self.repo)
        run('git', 'commit', '-qm', 'first', cwd=self.repo)
        (self.repo / 'main.c').write_text('int main(void) {\n  return 0;\n}\n')  # History-only change on revert
        run('git', 'add', '.', cwd=self.repo)
        run('git', 'commit', '-qm', 'revert portion', cwd=self.repo)
        (self.repo / 'staged.c').write_text('int staged = 1;\n')
        run('git', 'add', 'staged.c', cwd=self.repo)
        (self.repo / 'main.c').write_text('int main(void) {\n  return 0;\n  /* uncommitted */\n}\n')
        (self.repo / 'untracked with spaces.c').write_text('int added = 42;\n')
        (self.repo / 'scratch').mkdir()
        (self.repo / 'scratch' / 'hidden.c').write_text('int hidden = 1;\n')
        p = self.inventory()
        self.assertEqual(p.returncode, 0, p.stderr)
        with (self.out / 'ledger.csv').open(newline='') as f:
            rows = list(csv.DictReader(f))
        self.assertTrue(any(x['phase'].startswith('commit-') and x['change'] == '-' and 'return 22;' in x['excerpt'] for x in rows))
        self.assertTrue(any(x['kind'] == 'binary' for x in rows))
        self.assertTrue(any(x['path'] == 'untracked with spaces.c' and x['kind'] == 'line' for x in rows))
        self.assertTrue(any(x['path'] == 'scratch/hidden.c' and x['kind'] == 'ignored-source' for x in rows))
        with (self.out / 'ledger.csv').open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            for item in rows:
                item.update(verdict='PASS', evidence_a='Source: local pinned git patch:lines', evidence_b='Target-v kernel API ref: symbol', rationale='This item was reviewed in the disposable test.')
                w.writerow(item)
        verified = run(sys.executable, str(SCRIPT), 'verify', '--repo', str(self.repo), '--out', str(self.out), ok=False)
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertIn('DISPOSITIONS COMPLETE', verified.stdout)
        (self.repo / 'main.c').write_text('int main(void) { return 99; }\n')
        changed = run(sys.executable, str(SCRIPT), 'verify', '--repo', str(self.repo), '--out', str(self.out), ok=False)
        self.assertNotEqual(changed.returncode, 0)
        self.assertIn('SCOPE DRIFT', changed.stderr)

    def test_fail_closed_missing_evidence(self):
        (self.repo / 'main.c').write_text('int main(void) { return 3; }\n')
        result = self.inventory()
        self.assertEqual(result.returncode, 0, result.stderr)
        result = run(sys.executable, str(SCRIPT), 'verify', '--repo', str(self.repo), '--out', str(self.out), ok=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Incomplete evidence', result.stderr)

    def test_ignored_contents_change_invalidates_scope(self):
        (self.repo / 'scratch').mkdir()
        ignored_file = self.repo / 'scratch' / 'hidden.c'
        ignored_file.write_text('int hidden = 1;\n')
        result = self.inventory()
        self.assertEqual(result.returncode, 0, result.stderr)
        ignored_file.write_text('int hidden = 2;\n')
        result = run(sys.executable, str(SCRIPT), 'verify', '--repo', str(self.repo), '--out', str(self.out), ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SCOPE DRIFT', result.stderr)

    def test_unicode_quoted_binary_and_source_lines(self):
        (self.repo / 'é.bin').write_bytes(b'\x00\xff\x01')
        run('git', 'add', 'é.bin', cwd=self.repo)
        run('git', 'commit', '-qm', 'add UTF8 binary', cwd=self.repo)
        (self.repo / 'é.bin').write_bytes(b'\x00\xfe\x01')
        (self.repo / 'main.c').write_text('+++ leading pluses\n--- leading minuses\n')
        result = self.inventory()
        self.assertEqual(result.returncode, 0, result.stderr)
        with (self.out / 'ledger.csv').open(newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        self.assertTrue(any(row['path'] == 'é.bin' and row['kind'] == 'binary' for row in rows))
        self.assertTrue(any(row['path'] == 'main.c' and row['kind'] == 'line' and '+++ leading pluses' in row['excerpt'] for row in rows))
        self.assertTrue(any(row['path'] == 'main.c' and row['kind'] == 'line' and '--- leading minuses' in row['excerpt'] for row in rows))

    def test_no_out_inside_repo(self):
        result = run(sys.executable, str(SCRIPT), 'inventory', '--repo', str(self.repo), '--base', self.base, '--out', str(self.repo / 'bad'), ok=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('outside', result.stderr.lower())


    def verify(self):
        return run(sys.executable, str(SCRIPT), 'verify', '--repo', str(self.repo), '--out', str(self.out), ok=False)

    def rows(self):
        return json.loads((self.out / 'inventory.json').read_text())

    def disposition(self, verdict='UNKNOWN'):
        with (self.out / 'ledger.csv').open(newline='') as f:
            reader = csv.DictReader(f)
            fields, rows = reader.fieldnames, list(reader)
        for row in rows:
            row.update(verdict=verdict, evidence_a='fixture:source', rationale='Synthetic validation only', follow_up='Review actual semantics')
        with (self.out / 'ledger.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_skip_worktree_is_rejected_without_index_mutation(self):
        run('git', 'update-index', '--skip-worktree', 'main.c', cwd=self.repo)
        (self.repo / 'main.c').write_text('int hidden = 2;\n')
        index = (self.repo / '.git/index').read_bytes()
        result = self.inventory()
        self.assertEqual(result.returncode, 2)
        self.assertIn('skip-worktree', result.stderr)
        self.assertFalse(self.out.exists())
        self.assertEqual(index, (self.repo / '.git/index').read_bytes())

    def test_assume_unchanged_is_rejected(self):
        run('git', 'update-index', '--assume-unchanged', 'main.c', cwd=self.repo)
        self.assertIn('assume-unchanged', self.inventory().stderr)

    def test_formfeed_cr_vt_and_unicode_separator_preserve_lf_lines(self):
        content = 'int value =\f2;\nint other =\v3;\n/* cr\r unicode\u2028 */\n'
        (self.repo / 'main.c').write_bytes(content.encode())
        result = self.inventory()
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [r for r in self.rows() if r['phase'] == 'final-tree' and r['kind'] == 'line' and r['change'] == '+']
        self.assertEqual([r['new_line'] for r in lines], ['1', '2', '3'])
        self.assertEqual(lines[0]['excerpt'], 'int value =\f2;')
        self.assertIn('int other =\v3;', lines[1]['excerpt'])

    def test_noprefix_and_custom_prefixes_are_overridden(self):
        for key, val in [('diff.noprefix', 'true'), ('diff.mnemonicPrefix', 'true'),
                         ('diff.srcPrefix', 'old/'), ('diff.dstPrefix', 'new/')]:
            run('git', 'config', key, val, cwd=self.repo)
        (self.repo / 'main.c').write_text('int changed = 4;\n')
        result = self.inventory()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any(r['path'] == 'main.c' and r['kind'] == 'line' for r in self.rows()))
        self.assertFalse(any('UNPARSED' in r['path'] for r in self.rows()))

    def test_fsmonitor_and_external_diff_never_execute(self):
        marker = self.root / 'hook-executed'
        hook = self.root / 'hook'
        hook.write_text(f'#!/bin/sh\nprintf ran > "{marker}"\nexit 0\n')
        hook.chmod(0o755)
        for key in ['core.fsmonitor', 'diff.external', 'diff.custom.command', 'diff.custom.textconv']:
            run('git', 'config', key, str(hook), cwd=self.repo)
        (self.repo / '.gitattributes').write_text('*.c diff=custom\n')
        (self.repo / 'main.c').write_text('int changed = 8;\n')
        result = self.inventory()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(marker.exists())

    def test_clean_filter_rejected_without_execution(self):
        marker = self.root / 'filter-executed'
        hook = self.root / 'filter-hook'
        hook.write_text(f'#!/bin/sh\nprintf ran > "{marker}"\ncat\n')
        hook.chmod(0o755)
        run('git', 'config', 'filter.custom.clean', str(hook), cwd=self.repo)
        (self.repo / '.gitattributes').write_text('*.c filter=custom\n')
        (self.repo / 'main.c').write_text('int changed = 8;\n')
        result = self.inventory()
        self.assertEqual(result.returncode, 2)
        self.assertIn('filters', result.stderr)
        self.assertFalse(marker.exists())

    def test_transforming_attributes_fail_closed(self):
        (self.repo / '.gitattributes').write_text('*.c text eol=lf\n')
        result = self.inventory()
        self.assertEqual(result.returncode, 2)
        self.assertIn('Content-transforming', result.stderr)

    def add_submodule(self):
        child = self.root / 'child-source'
        child.mkdir()
        run('git', 'init', '-q', str(child))
        run('git', 'config', 'user.name', 'Test', cwd=child)
        run('git', 'config', 'user.email', 'test@example.invalid', cwd=child)
        (child / 'driver.c').write_text('int value = 1;\n')
        (child / '.gitignore').write_text('ignored.dat\n')
        run('git', 'add', '.', cwd=child)
        run('git', 'commit', '-qm', 'base', cwd=child)
        run('git', '-c', 'protocol.file.allow=always', 'submodule', 'add', '-q', str(child), 'sub', cwd=self.repo)
        run('git', 'commit', '-qam', 'add submodule', cwd=self.repo)
        self.base = run('git', 'rev-parse', 'HEAD', cwd=self.repo).stdout.strip()
        return self.repo / 'sub'

    def test_already_dirty_submodule_content_drift(self):
        sub = self.add_submodule()
        (sub / 'driver.c').write_text('int value = 2;\n')
        self.assertEqual(self.inventory().returncode, 0)
        self.disposition()
        (sub / 'driver.c').write_text('int value = 3;\n')
        result = self.verify()
        self.assertEqual(result.returncode, 2)
        self.assertIn('SCOPE DRIFT', result.stderr)

    def test_submodule_ignored_content_drift(self):
        sub = self.add_submodule()
        (sub / 'ignored.dat').write_text('one')
        self.assertEqual(self.inventory().returncode, 0)
        self.disposition()
        (sub / 'ignored.dat').write_text('two')
        self.assertIn('SCOPE DRIFT', self.verify().stderr)

    def test_raw_file_permissions_drift(self):
        result = self.inventory()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.disposition()
        (self.repo / 'main.c').chmod(0o600)
        self.assertIn('SCOPE DRIFT', self.verify().stderr)

    def test_unknown_dispositions_are_not_approval(self):
        self.assertEqual(self.inventory().returncode, 0)
        self.disposition()
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('DISPOSITIONS COMPLETE', result.stdout)
        self.assertIn('NOT CLEARED', result.stdout)
        self.assertIn('bookkeeping only', result.stdout)

    def test_duplicate_citations_rejected(self):
        self.assertEqual(self.inventory().returncode, 0)
        self.disposition('PASS')
        ledger = self.out / 'ledger.csv'
        with ledger.open(newline='') as f:
            reader = csv.DictReader(f)
            fields, rows = reader.fieldnames, list(reader)
        for row in rows:
            row['evidence_b'] = row['evidence_a']
        with ledger.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        self.assertIn('Incomplete', self.verify().stderr)

    def test_inventory_and_patch_tampering_rejected(self):
        (self.repo / 'main.c').write_text('int changed = 2;\n')
        self.assertEqual(self.inventory().returncode, 0)
        self.disposition()
        patch = self.out / 'patches/final-tree.patch'
        patch.write_bytes(patch.read_bytes() + b'corrupt\n')
        self.assertIn('Stored patch changed', self.verify().stderr)

    def test_old_format_rejected(self):
        self.assertEqual(self.inventory().returncode, 0)
        p = self.out / 'scope.json'
        scope = json.loads(p.read_text())
        scope['format_version'] = 1
        p.write_text(json.dumps(scope))
        self.assertIn('Unsupported audit format', self.verify().stderr)

    def test_ignored_files_all_get_line_coverage(self):
        (self.repo / 'scratch').mkdir()
        (self.repo / 'scratch/startup.custom').write_text('line one\nline two\n')
        self.assertEqual(self.inventory().returncode, 0)
        rows = [r for r in self.rows() if r['phase'] == 'ignored' and r['kind'] == 'line']
        self.assertEqual(len(rows), 2)

    def test_untracked_non_lf_characters(self):
        (self.repo / 'new.c').write_text('one\ftwo\nthree\vfour')
        self.assertEqual(self.inventory().returncode, 0)
        rows = [r for r in self.rows() if r['phase'] == 'untracked' and r['kind'] == 'line']
        self.assertEqual(len(rows), 2)

    def test_no_newline_and_tricky_paths(self):
        for name in ['line\nbreak.c', 'tab\tfile.c', 'dir b/space.c', 'quote".c']:
            p = self.repo / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b'int value = 1;')
            run('git', 'add', '--', name, cwd=self.repo)
        result = self.inventory()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any(r['kind'] == 'file-ending' for r in self.rows()))
        self.assertTrue(any(r['path'] == 'dir b/space.c' for r in self.rows()))

    def test_output_in_linked_worktree_git_metadata_rejected(self):
        linked = self.root / 'linked'
        run('git', 'worktree', 'add', '-q', '--detach', str(linked), cwd=self.repo)
        out = self.repo / '.git/worktrees/linked/new-audit'
        result = run(sys.executable, str(SCRIPT), 'inventory', '--repo', str(linked),
                     '--base', self.base, '--out', str(out), ok=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('outside', result.stderr)

    def test_source_and_git_metadata_unchanged(self):
        (self.repo / 'main.c').write_text('int changed = 7;\n')
        def digest_files():
            return {str(p.relative_to(self.repo)): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        before = digest_files()
        self.assertEqual(self.inventory().returncode, 0)
        self.disposition()
        self.assertEqual(self.verify().returncode, 0)
        self.assertEqual(before, digest_files())

    def test_parser_rejects_truncated_hunk(self):
        spec = importlib.util.spec_from_file_location('scope_helper', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        patch = b'diff --git a/main.c b/main.c\n--- a/main.c\n+++ b/main.c\n@@ -0,0 +1,2 @@\n+one\n'
        with self.assertRaises(ValueError):
            module.parse_patch('fixture', patch)

    def test_missing_ledger_rows_rejected(self):
        self.assertEqual(self.inventory().returncode, 0)
        self.disposition()
        p = self.out / 'ledger.csv'
        lines = p.read_text().splitlines(keepends=True)
        p.write_text(''.join(lines[:-1]))
        self.assertIn('Missing ledger entries', self.verify().stderr)


    def test_case_sensitive_untracked_contents_and_drift(self):
        run('git', 'config', 'core.ignoreCase', 'true', cwd=self.repo)
        (self.repo / 'MAIN.C').write_text('int hidden = 1;\n')
        result = self.inventory()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any(r['path'] == 'MAIN.C' for r in self.rows()))
        self.disposition()
        (self.repo / 'MAIN.C').write_text('int hidden = 2;\n')
        self.assertIn('SCOPE DRIFT', self.verify().stderr)

    def test_stat_cache_cannot_silently_hide_changed_bytes(self):
        run('git', 'config', 'core.trustctime', 'false', cwd=self.repo)
        run('git', 'config', 'core.checkStat', 'minimal', cwd=self.repo)
        run('git', 'update-index', '--refresh', cwd=self.repo)
        p = self.repo / 'main.c'
        before = p.stat()
        p.write_text(p.read_text().replace('return 0', 'return 9'))
        os.utime(p, ns=(before.st_atime_ns, before.st_mtime_ns))
        result = self.inventory()
        # Either exact inventory or an explicit raw-content coverage blocker.
        if result.returncode == 0:
            self.assertTrue(any(r['path'] == 'main.c' and r['kind'] == 'line' and 'return 9' in r['excerpt'] for r in self.rows()))
        else:
            self.assertIn('Raw working file differs', result.stderr)

    def test_split_index_rejected_without_timestamp_writes(self):
        run('git', 'update-index', '--split-index', cwd=self.repo)
        paths = list((self.repo / '.git').glob('sharedindex.*'))
        self.assertTrue(paths)
        before = {str(p): (p.stat().st_mtime_ns, p.stat().st_ctime_ns, p.read_bytes()) for p in paths}
        result = self.inventory()
        self.assertEqual(result.returncode, 2)
        self.assertIn('Split-index', result.stderr)
        after = {str(p): (p.stat().st_mtime_ns, p.stat().st_ctime_ns, p.read_bytes()) for p in paths}
        self.assertEqual(before, after)
        self.assertFalse(self.out.exists())

    def test_regular_to_symlink_transition(self):
        p = self.repo / 'main.c'
        p.unlink()
        p.symlink_to('to-delete.c')
        result = self.inventory()
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [r for r in self.rows() if r['path'] == 'main.c' and r['phase'] == 'final-tree']
        self.assertEqual(sum(r['kind'] == 'file-delta' for r in rows), 2)
        self.assertTrue(any(r['change'] == '-' for r in rows))
        self.assertTrue(any(r['change'] == '+' for r in rows))

    def test_staged_space_filename(self):
        (self.repo / 'space name.c').write_text('int okay = 1;\n')
        run('git', 'add', 'space name.c', cwd=self.repo)
        result = self.inventory()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any(r['path'] == 'space name.c' for r in self.rows()))


    def test_large_and_binary_untracked_are_explicit(self):
        (self.repo / 'large.c').write_bytes(b'x' * (4 * 1024 * 1024 + 1))
        (self.repo / 'extra.bin').write_bytes(b'\0\xff')
        result = self.inventory()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any(r['path'] == 'large.c' and r['kind'] == 'unexpanded' for r in self.rows()))
        self.assertTrue(any(r['path'] == 'extra.bin' and r['kind'] == 'binary' for r in self.rows()))

    def test_source_drift_during_collection_fails(self):
        spec = importlib.util.spec_from_file_location('scope_drift', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_git = module.git
        changed = False
        def mutate_once(repo, *args, **kwargs):
            nonlocal changed
            if args[0] == 'diff' and not changed:
                changed = True
                (self.repo / 'main.c').write_text('int during = 8;\n')
            return original_git(repo, *args, **kwargs)
        module.git = mutate_once
        with self.assertRaisesRegex(RuntimeError, 'SCOPE DRIFT'):
            module.collect(self.repo, self.base)

    def test_fifo_never_read_as_regular_file(self):
        os.mkfifo(self.repo / 'pipe.c')
        result = self.inventory()
        self.assertEqual(result.returncode, 2)
        self.assertIn('special file', result.stderr)

    def test_corrupted_inventory_rejected(self):
        self.assertEqual(self.inventory().returncode, 0)
        self.disposition()
        p = self.out / 'inventory.json'
        items = json.loads(p.read_text())
        items[0]['excerpt'] = 'changed'
        p.write_text(json.dumps(items))
        self.assertIn('Inventory changed', self.verify().stderr)


if __name__ == '__main__':
    unittest.main()
