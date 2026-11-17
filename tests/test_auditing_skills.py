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

GOOD_EVALS = json.dumps([{'query': q, 'expected_behavior': ['x']} for q in 'abc'])


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

    def skill(self, name, description='Does a thing. Use when the user asks for the thing.', body='# Thing\n', evals=True):
        self.write(f'{name}/SKILL.md', f'---\nname: {Path(name).name}\ndescription: {description}\n---\n\n{body}')
        if evals:
            self.write(f'{name}/evals/evals.json', GOOD_EVALS)
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
        self.write('main/references/a.md', 'Then read [b](b.md).\n')
        self.write('main/references/b.md', '# B\n')
        self.write('main/references/orphan.md', '# Orphan\n')
        code, findings = run(self.root / 'main')
        self.assertEqual(code, 1)
        text = ' '.join(self.messages(findings))
        self.assertIn('broken link to references/gone.md', text)
        self.assertNotIn('also-gone', text)
        self.assertIn('reaches into the "other" skill', text)
        self.assertIn('chained reference: sends the reader on to references/b.md', text)
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

    def test_evals_and_duplicates(self):
        self.skill('one', evals=False, body='Use [the template](assets/t.md).\n')
        self.skill('two', body='Use [the template](assets/t.md).\n')
        self.write('one/assets/t.md', 'same\n')
        self.write('two/assets/t.md', 'same\n')
        self.write('two/evals/evals.json', json.dumps({'evals': [{'query': 'a'}]}))
        _, findings = run(self.root)
        by_skill = {}
        for f in findings:
            by_skill.setdefault(f['skill'], []).append(f['message'])
        self.assertIn('no evaluation scenarios', ' '.join(by_skill['one']))
        self.assertIn('1 evaluation scenarios', ' '.join(by_skill['two']))
        self.assertIn('identical to two/assets/t.md', ' '.join(by_skill['one']))

    def test_finds_project_skills_from_repository_root(self):
        self.skill('repo/.claude/skills/deploy', body='See [the runbook](../../../docs/runbook.md) and [the URL](URL).\n')
        self.write('repo/docs/runbook.md', '# Runbook\n')
        self.skill('repo/packages/web/.agents/skills/lint')
        self.skill('repo/node_modules/pkg/skills/vendored')
        self.skill('repo/.claude/worktrees/copy/.claude/skills/deploy')
        self.skill('repo/.claude/skills/deploy/assets/example')  # a skill's own example, not a skill
        (self.root / 'linked').symlink_to(self.root / 'repo/.claude/skills/deploy')
        code, findings = run(self.root / 'repo')
        self.assertEqual(code, 0, findings)
        self.assertEqual(sorted({f['skill'] for f in findings}), ['.claude/skills/deploy', 'packages/web/.agents/skills/lint'])
        self.assertEqual([f['level'] for f in findings if f['level'] != 'NOTE'], [])
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
