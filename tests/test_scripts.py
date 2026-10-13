"""Fixture tests for scripts/import.sh and scripts/link.sh.

Each test builds a throwaway repo and home folder, copies the scripts into the
repo's scripts/ folder, and runs them with macOS's /bin/bash. Nothing touches
your real home folder.

Run from the repo root: python3 -m unittest discover tests
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / 'scripts'


def snapshot(root):
    """Every path under root with its link target, or file bytes and mode."""
    result = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            key = str(path.relative_to(root))
            if path.is_symlink():
                result[key] = ('link', os.readlink(path))
            elif path.is_dir():
                result[key] = ('dir',)
            else:
                result[key] = ('file', path.read_bytes(), path.stat().st_mode)
    return result


class Fixture(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='skills-scripts-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.repo = self.root / 'repository with spaces'
        self.home = self.root / 'home'
        (self.repo / 'scripts').mkdir(parents=True)
        self.home.mkdir()
        for name in ['import.sh', 'link.sh']:
            shutil.copy2(SCRIPTS / name, self.repo / 'scripts' / name)
        self.env = dict(os.environ, HOME=str(self.home))
        self.env.pop('CODEX_HOME', None)
        self.env.pop('CLAUDE_CONFIG_DIR', None)
        self.codex = self.home / '.agents/skills'
        self.legacy = self.home / '.codex/skills'
        self.claude = self.home / '.claude/skills'
        self.backups = self.home / 'skills-link-backup'

    def skill(self, folder, name, body='sample'):
        path = folder / name
        path.mkdir(parents=True, exist_ok=True)
        (path / 'SKILL.md').write_text('---\nname: ' + name + '\ndescription: Fixture\n---\n' + body)
        return path

    def run_script(self, script, *args, expected=0):
        # Run from outside the repo: the scripts must find it from their own location.
        result = subprocess.run(['/bin/bash', str(self.repo / 'scripts' / script), *args],
                                env=self.env, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def assertLinks(self, path, target):
        self.assertTrue(path.is_symlink(), path)
        self.assertEqual(os.readlink(path), str(target))


class ImportTests(Fixture):
    def test_imports_identical_copies_into_skills(self):
        self.skill(self.codex, 'codex-first')
        self.skill(self.legacy, 'legacy-only')
        self.skill(self.claude, 'claude-first')
        shared = self.skill(self.codex, 'shared')
        self.skill(self.legacy, 'shared')
        self.skill(self.claude, 'shared')
        self.skill(self.legacy, '.system')
        self.skill(self.claude, 'synced')
        helper = shared / 'helper.sh'
        helper.write_text('#!/bin/sh\nexit 0\n')
        helper.chmod(0o755)
        for folder in [self.legacy, self.claude]:  # identical copies, supporting files included
            copy = folder / 'shared/helper.sh'
            copy.write_text(helper.read_text())
            copy.chmod(0o755)
        outside = self.skill(self.root / 'external', 'linked-source')
        (self.codex / 'linked-source').symlink_to(outside)

        self.run_script('import.sh')

        for name in ['codex-first', 'legacy-only', 'claude-first', 'shared', 'linked-source']:
            self.assertTrue((self.repo / 'skills' / name / 'SKILL.md').is_file(), name)
        self.assertFalse((self.repo / 'skills/linked-source').is_symlink())
        self.assertTrue((self.repo / 'skills/shared/helper.sh').stat().st_mode & 0o111)
        for excluded in ['skills/.system', 'skills/synced', '.import', 'scripts/skills', 'codex-only', 'claude-only']:
            self.assertFalse((self.repo / excluded).exists(), excluded)

    def test_differing_copies_are_skipped_and_listed(self):
        cases = [('codex-vs-claude', self.codex, self.claude), ('codex-folders', self.codex, self.legacy),
                 ('legacy-vs-claude', self.legacy, self.claude)]
        for name, first, second in cases:
            self.skill(first, name, 'one version')
            self.skill(second, name, 'another version')
        self.skill(self.codex, 'other')
        out = self.run_script('import.sh')
        self.assertIn('Not imported, installed copies differ: codex-folders codex-vs-claude legacy-vs-claude', out)
        for name, _, _ in cases:
            self.assertFalse((self.repo / 'skills' / name).exists(), name)
        self.assertTrue((self.repo / 'skills/other/SKILL.md').is_file())

    def test_executable_bit_difference_is_a_difference(self):
        for folder, mode in [(self.codex, 0o644), (self.claude, 0o755)]:
            helper = self.skill(folder, 'tool') / 'helper.sh'
            helper.write_text('#!/bin/sh\nexit 0\n')
            helper.chmod(mode)
        self.assertIn('copies differ: tool', self.run_script('import.sh'))
        self.assertFalse((self.repo / 'skills/tool').exists())

    def test_rerun_never_overwrites_repo(self):
        self.skill(self.codex, 'codex-first')
        self.run_script('import.sh')
        imported = snapshot(self.repo)
        (self.codex / 'codex-first/SKILL.md').write_text('changed installed source')
        self.assertIn('not overwritten: skills/codex-first', self.run_script('import.sh'))
        self.assertEqual(snapshot(self.repo), imported)

    def test_linked_skills_are_not_imported_again(self):
        mine = self.skill(self.repo / 'skills', 'mine')
        self.run_script('link.sh')
        before = snapshot(self.repo)
        self.assertIn('not overwritten: skills/mine', self.run_script('import.sh'))
        self.assertEqual(snapshot(self.repo), before)
        self.assertLinks(self.claude / 'mine', mine)

    def test_absent_source_folders(self):
        self.run_script('import.sh')
        self.assertTrue((self.repo / 'skills').is_dir())


class LinkTests(Fixture):
    def test_rejects_bad_arguments_without_changes(self):
        self.skill(self.repo / 'skills', 'example')
        for args in [('--undo',), ('--dry-run', '--undo'), ('', '--dry-run'), ('',), ('--dry-run', '--dry-run')]:
            before = snapshot(self.home)
            self.assertIn('Usage:', self.run_script('link.sh', *args, expected=2), args)
            self.assertEqual(snapshot(self.home), before, args)

    def test_links_backs_up_and_is_idempotent(self):
        shared = self.skill(self.repo / 'skills', 'shared')
        other = self.skill(self.repo / 'skills', 'other')
        self.skill(self.codex, 'shared', 'old codex')
        self.skill(self.claude, 'shared', 'old claude')
        self.skill(self.legacy, 'shared', 'legacy')
        self.skill(self.legacy, '.system')
        synced = self.skill(self.claude, 'synced')
        unrelated = self.skill(self.codex, 'unrelated')
        old_target = self.skill(self.root / 'elsewhere', 'old-target')
        self.codex.mkdir(parents=True, exist_ok=True)
        (self.codex / 'other').symlink_to(old_target)

        before = snapshot(self.root)
        self.assertIn('Dry run: nothing changed.', self.run_script('link.sh', '--dry-run'))
        self.assertEqual(snapshot(self.root), before)

        out = self.run_script('link.sh')
        self.assertIn('Linked skills from ' + str(self.repo), out)
        self.assertIn('was -> ' + str(old_target), out)
        for folder in [self.codex, self.claude]:
            self.assertLinks(folder / 'shared', shared)
            self.assertLinks(folder / 'other', other)
        self.assertFalse((self.legacy / 'shared').exists())
        self.assertTrue((self.legacy / '.system/SKILL.md').exists())
        self.assertTrue(synced.is_dir() and unrelated.is_dir())
        backups = list(self.backups.iterdir())
        self.assertEqual(len(backups), 1)
        for label, body in [('codex', 'old codex'), ('claude', 'old claude'), ('codex-legacy', 'legacy')]:
            self.assertTrue((backups[0] / label / 'shared/SKILL.md').read_text().endswith(body), label)

        before = snapshot(self.root)
        self.assertNotIn('+ ', self.run_script('link.sh'))
        self.assertEqual(snapshot(self.root), before)

    def test_manual_recovery_of_folder_and_relative_link(self):
        self.skill(self.repo / 'skills', 'example')
        self.skill(self.codex, 'example', 'original current')
        external = self.skill(self.home / 'external', 'example', 'external')
        self.claude.mkdir(parents=True)
        (self.claude / 'example').symlink_to('../../external/example')
        self.assertIn('was -> ../../external/example', self.run_script('link.sh'))

        backup = next(self.backups.iterdir())
        (self.claude / 'example').unlink()
        (self.claude / 'example').symlink_to('../../external/example')
        self.assertEqual((self.claude / 'example').resolve(), external.resolve())
        (self.codex / 'example').unlink()
        shutil.move(str(backup / 'codex/example'), str(self.codex / 'example'))
        self.assertTrue((self.codex / 'example/SKILL.md').read_text().endswith('original current'))

    def test_deleted_skills_and_stale_links_are_unlinked(self):
        self.skill(self.repo / 'skills', 'kept')
        deleted = self.skill(self.repo / 'skills', 'deleted')
        self.run_script('link.sh')
        # A link into the repo that no skill plans, such as one left from an old codex-only/ folder.
        (self.claude / 'stale').symlink_to(self.repo / 'codex-only/stale')
        shutil.rmtree(deleted)
        preview = self.run_script('link.sh', '--dry-run')
        real = self.run_script('link.sh')
        changes = lambda text: [line for line in text.splitlines() if line.startswith(('+ ', 'replacing link'))]
        self.assertEqual(changes(preview), changes(real))
        for folder in [self.codex, self.claude]:
            self.assertFalse((folder / 'deleted').is_symlink())
            self.assertTrue((folder / 'kept').is_symlink())
        self.assertFalse((self.claude / 'stale').is_symlink())

    def test_reserved_name_stops_before_changes(self):
        self.skill(self.repo / 'skills', 'SyNcEd')
        before = snapshot(self.home)
        self.assertIn('Nothing changed', self.run_script('link.sh', expected=1))
        self.assertEqual(snapshot(self.home), before)

    def test_missing_and_empty_folders(self):
        self.run_script('link.sh')
        (self.repo / 'skills/not-a-skill').mkdir(parents=True)
        self.run_script('link.sh')
        self.assertFalse(self.codex.exists())
        self.assertFalse(self.claude.exists())

    def test_configured_agent_folders(self):
        self.env['CODEX_HOME'] = str(self.home / 'custom-codex')
        self.env['CLAUDE_CONFIG_DIR'] = str(self.home / 'custom-claude')
        skill = self.skill(self.repo / 'skills', 'custom')
        self.skill(self.home / 'custom-codex/skills', 'custom')
        self.run_script('link.sh')
        self.assertLinks(self.codex / 'custom', skill)
        self.assertLinks(self.home / 'custom-claude/skills/custom', skill)
        self.assertFalse((self.home / 'custom-codex/skills/custom').exists())
        self.assertFalse(self.claude.exists())

    def test_legacy_folder_that_is_the_agents_folder_keeps_links(self):
        for setup in ['symlink', 'CODEX_HOME']:
            with self.subTest(setup=setup):
                self.setUp()
                skill = self.skill(self.repo / 'skills', 'shared')
                self.codex.mkdir(parents=True)
                if setup == 'symlink':
                    self.legacy.parent.mkdir(parents=True)
                    self.legacy.symlink_to(self.codex)
                else:
                    self.env['CODEX_HOME'] = str(self.home / '.agents')
                out = self.run_script('link.sh')
                self.assertLinks(self.codex / 'shared', skill)
                self.assertNotIn('codex-legacy', out)
                self.assertFalse(self.backups.exists())

    def test_same_second_runs_keep_separate_backups(self):
        self.skill(self.repo / 'skills', 'example')
        fake_bin = self.root / 'bin'
        fake_bin.mkdir()
        (fake_bin / 'date').write_text('#!/bin/sh\nprintf 20261013-000000\n')
        (fake_bin / 'date').chmod(0o755)
        self.env['PATH'] = str(fake_bin) + ':' + self.env['PATH']
        for body in ['first original', 'second original']:
            if (self.codex / 'example').is_symlink():
                (self.codex / 'example').unlink()
            self.skill(self.codex, 'example', body)
            self.run_script('link.sh')
        backups = list(self.backups.iterdir())
        self.assertEqual(len(backups), 2)
        bodies = {(b / 'codex/example/SKILL.md').read_text().rsplit('\n', 1)[-1] for b in backups}
        self.assertEqual(bodies, {'first original', 'second original'})


class DocsTests(unittest.TestCase):
    def test_bash_blocks_parse(self):
        for doc in [ROOT / 'README.md', ROOT / 'docs/maintaining.md']:
            blocks = re.findall(r'^ *```bash\n(.*?)^ *```', doc.read_text(), re.MULTILINE | re.DOTALL)
            self.assertTrue(blocks, doc)
            for block in blocks:
                result = subprocess.run(['/bin/bash', '-n'], input=block, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, (doc.name, block, result.stderr))


if __name__ == '__main__':
    unittest.main()
