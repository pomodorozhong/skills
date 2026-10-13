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
    def test_imports_into_shared_and_agent_folders(self):
        self.skill(self.codex, 'codex-first')
        self.skill(self.legacy, 'legacy-only')
        self.skill(self.claude, 'claude-first')
        shared = self.skill(self.codex, 'shared')
        self.skill(self.legacy, 'shared')
        self.skill(self.claude, 'shared')
        self.skill(self.codex, 'different', 'codex version')
        self.skill(self.claude, 'different', 'claude version')
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

        out = self.run_script('import.sh')

        for name in ['codex-first', 'legacy-only', 'claude-first', 'shared', 'linked-source']:
            self.assertTrue((self.repo / 'skills' / name / 'SKILL.md').is_file(), name)
        self.assertFalse((self.repo / 'skills/linked-source').is_symlink())
        self.assertTrue((self.repo / 'skills/shared/helper.sh').stat().st_mode & 0o111)
        self.assertTrue((self.repo / 'codex-only/different/SKILL.md').read_text().endswith('codex version'))
        self.assertTrue((self.repo / 'claude-only/different/SKILL.md').read_text().endswith('claude version'))
        self.assertIn('DIFFERENT in each agent', out)
        for excluded in ['skills/.system', 'skills/synced', '.import', 'scripts/skills']:
            self.assertFalse((self.repo / excluded).exists(), excluded)

    def test_rerun_never_overwrites_repo(self):
        self.skill(self.codex, 'codex-first')
        self.skill(self.codex, 'different', 'codex version')
        self.skill(self.claude, 'different', 'claude version')
        self.run_script('import.sh')
        imported = snapshot(self.repo)
        (self.codex / 'codex-first/SKILL.md').write_text('changed installed source')
        self.assertIn('not overwritten', self.run_script('import.sh'))
        self.assertEqual(snapshot(self.repo), imported)

    def test_conflicting_codex_versions_stop_before_import(self):
        self.skill(self.codex, 'conflict', 'new')
        self.skill(self.legacy, 'conflict', 'old')
        self.skill(self.codex, 'other')
        before = snapshot(self.root)
        self.assertIn('Nothing imported', self.run_script('import.sh', expected=1))
        self.assertEqual(snapshot(self.root), before)

    def test_absent_source_folders(self):
        self.run_script('import.sh')
        for name in ['skills', 'codex-only', 'claude-only']:
            self.assertTrue((self.repo / name).is_dir(), name)


class LinkTests(Fixture):
    def test_rejects_bad_arguments_without_changes(self):
        self.skill(self.repo / 'skills', 'example')
        for args in [('--undo',), ('--dry-run', '--undo'), ('', '--dry-run'), ('',), ('--dry-run', '--dry-run')]:
            before = snapshot(self.home)
            self.assertIn('Usage:', self.run_script('link.sh', *args, expected=2), args)
            self.assertEqual(snapshot(self.home), before, args)

    def test_links_backs_up_and_is_idempotent(self):
        shared = self.skill(self.repo / 'skills', 'shared')
        codex = self.skill(self.repo / 'codex-only', 'codex-skill')
        claude = self.skill(self.repo / 'claude-only', 'claude-skill')
        self.skill(self.codex, 'shared', 'old codex')
        self.skill(self.claude, 'shared', 'old claude')
        self.skill(self.legacy, 'shared', 'legacy')
        self.skill(self.legacy, '.system')
        synced = self.skill(self.claude, 'synced')
        unrelated = self.skill(self.codex, 'unrelated')
        old_target = self.skill(self.root / 'elsewhere', 'old-target')
        (self.codex / 'codex-skill').symlink_to(old_target)

        before = snapshot(self.root)
        self.assertIn('Dry run: nothing changed.', self.run_script('link.sh', '--dry-run'))
        self.assertEqual(snapshot(self.root), before)

        out = self.run_script('link.sh')
        self.assertIn('Linked skills from ' + str(self.repo), out)
        self.assertIn('was -> ' + str(old_target), out)
        self.assertLinks(self.codex / 'shared', shared)
        self.assertLinks(self.claude / 'shared', shared)
        self.assertLinks(self.codex / 'codex-skill', codex)
        self.assertLinks(self.claude / 'claude-skill', claude)
        self.assertFalse((self.claude / 'codex-skill').exists())
        self.assertFalse((self.codex / 'claude-skill').exists())
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

    def test_moved_and_deleted_skills_are_unlinked(self):
        shared = self.skill(self.repo / 'skills', 'shared')
        claude = self.skill(self.repo / 'claude-only', 'claude-skill')
        self.run_script('link.sh')

        (self.repo / 'codex-only').mkdir()
        shared.rename(self.repo / 'codex-only/shared')
        preview = self.run_script('link.sh', '--dry-run')
        real = self.run_script('link.sh')
        changes = lambda text: [line for line in text.splitlines() if line.startswith(('+ ', 'replacing link'))]
        self.assertEqual(changes(preview), changes(real))
        self.assertLinks(self.codex / 'shared', self.repo / 'codex-only/shared')
        self.assertFalse((self.claude / 'shared').is_symlink())

        shutil.rmtree(claude)
        self.run_script('link.sh')
        self.assertFalse((self.claude / 'claude-skill').is_symlink())

    def test_duplicate_and_reserved_names_stop_before_changes(self):
        for folder, name in [('codex-only', 'same'), ('claude-only', 'SyNcEd')]:
            with self.subTest(name=name):
                shutil.rmtree(self.repo / 'skills', ignore_errors=True)
                self.skill(self.repo / folder, name)
                if folder == 'codex-only':
                    self.skill(self.repo / 'skills', name)
                before = snapshot(self.home)
                self.assertIn('Nothing changed', self.run_script('link.sh', expected=1))
                self.assertEqual(snapshot(self.home), before)
                shutil.rmtree(self.repo / folder)

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

    def test_same_second_runs_keep_separate_backups(self):
        self.skill(self.repo / 'codex-only', 'example')
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
