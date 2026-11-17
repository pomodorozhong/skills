"""Fixture tests for skills/auditing-skills/scripts/check_skills.py.

Each test writes throwaway skills to a temporary folder and runs the script on
them. Run from the repo root: python3 -m unittest discover tests
"""
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / 'skills' / 'auditing-skills' / 'scripts' / 'check_skills.py'

def run(*paths):
    result = subprocess.run([sys.executable, str(SCRIPT), '--json', *map(str, paths)],
                            capture_output=True, text=True)
    findings = json.loads(result.stdout) if result.stdout.strip() else []
    return result.returncode, findings


class CheckSkillsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='auditing-skills-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text).lstrip())
        return path

    def skill(self, name, description='Does a thing. Use when the user asks for the thing.', body='# Thing\n'):
        self.write(f'{name}/SKILL.md', f'---\nname: {Path(name).name}\ndescription: {description}\n---\n\n{body}')
        return self.root / name

    def messages(self, findings, level=None):
        return [f['message'] for f in findings if level is None or f['level'] == level]

    def test_clean_skill_has_no_findings(self):
        self.skill('clean', body='# Clean\n\nSee [the guide](references/guide.md).\n')
        self.write('clean/references/guide.md', '# Guide\n')
        code, findings = run(self.root / 'clean')
        self.assertEqual(code, 0)
        self.assertEqual(findings, [])

    def test_frontmatter_errors_fail(self):
        self.skill('bad', description='I can help with <b>things</b>.')
        (self.root / 'bad/SKILL.md').write_text('---\nname: Claude_Helper\ndescription: I can help with <b>things</b>.\n---\n')
        code, findings = run(self.root / 'bad')
        self.assertEqual(code, 1)
        errors = ' '.join(self.messages(findings, 'ERROR'))
        self.assertIn('lowercase', errors)
        self.assertIn('reserved word', errors)
        self.assertIn('XML tag', errors)
        warnings = ' '.join(self.messages(findings, 'WARN'))
        self.assertIn('"I" or "you"', warnings)
        self.assertIn('when-to-use', warnings)

    def test_missing_frontmatter_fails(self):
        self.write('none/SKILL.md', '# No frontmatter\n')
        code, findings = run(self.root / 'none')
        self.assertEqual(code, 1)
        self.assertIn('no YAML frontmatter', ' '.join(self.messages(findings)))

    def test_links_and_nesting(self):
        self.skill('other')
        self.skill('main', body=textwrap.dedent('''
            # Main

            Read [a](references/a.md). Use the [other skill](../other/SKILL.md). See [gone](references/gone.md).

            ```
            [not a link](references/also-gone.md)
            ```
        '''))
        self.write('main/references/a.md', 'Then read [b](b.md).\n\nSee [its steps](b.md#steps).\n')
        self.write('main/references/b.md', '# B\n')
        self.write('main/references/orphan.md', '# Orphan\n')
        code, findings = run(self.root / 'main')
        self.assertEqual(code, 1)
        text = ' '.join(self.messages(findings))
        self.assertIn('broken link to references/gone.md', text)
        self.assertNotIn('also-gone', text)
        self.assertIn('reaches into the "other" skill', text)
        chained = [f for f in findings if 'chained reference' in f['message']]
        self.assertEqual(len(chained), 1, chained)
        self.assertEqual(chained[0]['line'], 1)
        self.assertIn('sends the reader on to references/b.md (lines 1, 3)', chained[0]['message'])
        self.assertIn('reachable only through references/a.md', text)
        self.assertIn('nothing points to this file', text)

    def test_long_reference_needs_contents(self):
        self.skill('long', body='See [ref](ref.md) and [ok](ok.md).\n')
        self.write('long/ref.md', '# Ref\n' + 'line\n' * 120)
        self.write('long/ok.md', '# Ok\n\n## Contents\n\n- A\n' + 'line\n' * 120)
        _, findings = run(self.root / 'long')
        flagged = [f['file'] for f in findings if 'table of contents' in f['message']]
        self.assertEqual(flagged, ['ref.md'])

    def test_wording_checks(self):
        self.skill('words', body='Run `scripts\\tool.py`. If you are doing this before August 2025, use v1.\n')
        _, findings = run(self.root / 'words')
        text = ' '.join(self.messages(findings, 'WARN'))
        self.assertIn('Windows-style path', text)
        self.assertIn('time-sensitive wording "before August 2025"', text)

    def test_duplicates(self):
        self.skill('one', body='Use [the template](assets/t.md).\n')
        self.skill('two', body='Use [the template](assets/t.md).\n')
        self.write('one/assets/t.md', 'same\n')
        self.write('two/assets/t.md', 'same\n')
        _, findings = run(self.root)
        by_skill = {}
        for f in findings:
            by_skill.setdefault(f['skill'], []).append(f['message'])
        self.assertIn('identical to two/assets/t.md', ' '.join(by_skill['one']))

    def test_finds_project_skills_from_repository_root(self):
        self.skill('repo/.claude/skills/deploy', body='See [the runbook](../../../docs/runbook.md), [the URL](URL), and [the template](assets/t.md).\n')
        self.write('repo/docs/runbook.md', '# Runbook\n')
        # A shared template gives lint a NOTE, so the findings show it was found.
        self.skill('repo/packages/web/.agents/skills/lint', body='Use [the template](assets/t.md).\n')
        self.write('repo/packages/web/.agents/skills/lint/assets/t.md', 'same\n')
        self.write('repo/.claude/skills/deploy/assets/t.md', 'same\n')
        self.skill('repo/node_modules/pkg/skills/vendored')
        self.skill('repo/.claude/worktrees/copy/.claude/skills/deploy')
        self.skill('repo/.claude/skills/deploy/assets/example')  # a skill's own example, not a skill
        (self.root / 'linked').symlink_to(self.root / 'repo/.claude/skills/deploy')
        code, findings = run(self.root / 'repo')
        self.assertEqual(code, 0, findings)
        self.assertEqual(sorted({f['skill'] for f in findings}), ['.claude/skills/deploy', 'packages/web/.agents/skills/lint'])
        self.assertEqual([f for f in findings if f['level'] != 'NOTE'], [])
        outside = [f for f in findings if 'fine for a project skill' in f['message']]
        self.assertEqual(len(outside), 1)
        code, findings = run(self.root / 'linked')
        self.assertEqual(code, 0, findings)

    def test_scripts_must_be_named_somewhere(self):
        self.skill('tools', body='Run `python scripts/used.py`. Details in [ref](ref.md).\n')
        self.write('tools/ref.md', 'Or run `python scripts/from_ref` with no extension.\n')
        self.write('tools/scripts/used.py', 'import helper\n')
        self.write('tools/scripts/helper.py', 'X = 1\n')
        self.write('tools/scripts/from_ref.py', '\n')
        self.write('tools/scripts/_private.py', '\n')
        self.write('tools/scripts/unused.py', '\n')
        _, findings = run(self.root / 'tools')
        flagged = [f['file'] for f in findings if 'never be run' in f['message']]
        self.assertEqual(flagged, ['scripts/unused.py'])

    def test_script_name_must_match_whole(self):
        self.skill('stem', body='Run the checks.\n')
        self.write('stem/scripts/check.py', '\n')
        _, findings = run(self.root / 'stem')
        self.assertIn('scripts/check.py', [f['file'] for f in findings if 'never be run' in f['message']])

    def test_skill_named_like_a_skipped_folder_is_found(self):
        self.skill('repo/skills/build')
        self.skill('repo/build/skills/copy')  # build output, still skipped
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.root / 'repo')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('in 1 skills', result.stdout)

    def test_unclosed_frontmatter_fails(self):
        self.write('open/SKILL.md', '---\nname: open\ndescription: Does x. Use when asked.\n' + 'line\n' * 600)
        code, findings = run(self.root / 'open')
        self.assertEqual(code, 1)
        text = ' '.join(self.messages(findings))
        self.assertIn('no closing `---`', text)
        self.assertIn('body is', text)

    def test_symlinked_skill_uses_installed_name(self):
        self.skill('real/foo-dev')
        (self.root / 'real/foo-dev/SKILL.md').write_text('---\nname: foo\ndescription: Does x. Use when asked.\n---\n')
        (self.root / 'installed').mkdir()
        (self.root / 'installed/foo').symlink_to(self.root / 'real/foo-dev')
        _, findings = run(self.root / 'installed')
        self.assertNotIn('differs from its folder', ' '.join(self.messages(findings)))
        _, findings = run(self.root / 'installed/foo')
        self.assertNotIn('differs from its folder', ' '.join(self.messages(findings)))

    def test_byte_order_mark_is_ignored(self):
        path = self.skill('bom')
        skill_md = path / 'SKILL.md'
        skill_md.write_bytes(b'\xef\xbb\xbf' + skill_md.read_bytes())
        code, findings = run(path)
        self.assertEqual(code, 0, findings)

    def test_unlinked_data_files(self):
        self.skill('data', body='Run `scripts/load.py`. Fill in `assets/form.yaml`.\n')
        self.write('data/scripts/load.py', "open('references/table.json')\n")
        self.write('data/references/table.json', '{}\n')
        self.write('data/assets/form.yaml', 'a: 1\n')
        self.write('data/assets/orphan.yaml', 'a: 1\n')
        self.write('data/LICENSE.txt', 'MIT\n')
        self.write('data/agents/openai.yaml', 'a: 1\n')
        _, findings = run(self.root / 'data')
        flagged = [f['file'] for f in findings if 'nothing points' in f['message']]
        self.assertEqual(flagged, ['assets/orphan.yaml'])

    def test_duplicates_skip_licenses_and_evals(self):
        for name in ('one', 'two'):
            self.skill(name)
            self.write(f'{name}/LICENSE.txt', 'MIT\n')
        _, findings = run(self.root)
        self.assertNotIn('identical', ' '.join(self.messages(findings)))

    def test_encoded_and_root_relative_links(self):
        self.skill('links', body='See [a](references/my%20file.md) and [docs](/README.md).\n')
        self.write('links/references/my file.md', '# A\n')
        code, findings = run(self.root / 'links')
        self.assertEqual(code, 0, findings)
        self.assertEqual([f['level'] for f in findings], ['NOTE'])
        self.assertIn('repository root', findings[0]['message'])

    def test_links_in_inline_code_are_examples(self):
        self.skill('code', body='Write links as `[text](path.md)` or ``[a](`b`.md)``, not [real](missing.md).\n')
        code, findings = run(self.root / 'code')
        self.assertEqual(code, 1, findings)
        self.assertEqual(self.messages(findings), ['broken link to missing.md'])

    def test_file_names_match_whole(self):
        self.skill('names', body='Read [data](references/data.md).\n')
        self.write('names/references/data.md', '# Data\n')
        self.write('names/references/a.md', '# A\n')
        _, findings = run(self.root / 'names')
        flagged = [f['file'] for f in findings if 'nothing points' in f['message']]
        self.assertEqual(flagged, ['references/a.md'])

    def test_skips_dependency_folders_inside_a_skill(self):
        self.skill('node', body='Run `scripts/run.js`.\n')
        self.write('node/scripts/run.js', 'require("x")\n')
        self.write('node/scripts/node_modules/x/README.md', '[gone](missing.md)\n')
        _, findings = run(self.root / 'node')
        self.assertEqual(findings, [])

    def test_empty_files_are_not_duplicates(self):
        for name in ('one', 'two'):
            self.skill(name, body='Run `scripts/run.py`.\n')
            self.write(f'{name}/scripts/run.py', f'print("{name}")\n')
            self.write(f'{name}/scripts/__init__.py', '')
        _, findings = run(self.root)
        self.assertNotIn('identical', ' '.join(self.messages(findings)))

    def test_parent_path_uses_folder_name(self):
        self.skill('named')
        scripts = self.root / 'named' / 'scripts'
        scripts.mkdir()
        result = subprocess.run([sys.executable, str(SCRIPT), '--json', '..'], cwd=scripts, capture_output=True, text=True)
        findings = json.loads(result.stdout)
        self.assertEqual(findings, [])

    def test_no_skills_exits_2(self):
        code, _ = run(self.root)
        self.assertEqual(code, 2)

    def test_repository_skills_have_no_errors(self):
        code, findings = run(ROOT / 'skills')
        self.assertEqual(code, 0, [f for f in findings if f['level'] == 'ERROR'])
        audit = [f for f in findings if f['skill'] == 'auditing-skills' and f['level'] != 'NOTE']
        self.assertEqual(audit, [], 'auditing-skills should pass its own checks')


if __name__ == '__main__':
    unittest.main()
