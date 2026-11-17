"""Static checks on the skill files themselves.

These read the Markdown under skills/ and run no agent. They catch broken
links between skill files, growth of the always-loaded AGENTS.md block, and
drift between template copies shared by several skills.

Run from the repo root: python3 -m unittest discover tests
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / 'skills'
AGENTS_BLOCK = SKILLS / 'writing-handoffs' / 'assets' / 'agents-handoff.md'

# Relative Markdown link targets; web links and same-file anchors are skipped.
RELATIVE_LINK = re.compile(r'\]\((?!https?://|#)([^)#\s]+)')

# The block is copied into every handoff repo's AGENTS.md and loaded in every
# session there. Raise this only deliberately; situational rules belong in
# references/working-rules.md.
AGENTS_BLOCK_WORD_LIMIT = 300

# Templates copied into more than one skill, because each skill installs on its
# own. Every copy must stay identical; edit them together.
SHARED_TEMPLATES = [
    ('opening-prs/assets/pr-body.md', 'proposing-stacks/assets/pr-body.md'),
]


class SkillFileTests(unittest.TestCase):
    def test_relative_links_resolve(self):
        for md in sorted(SKILLS.rglob('*.md')):
            for target in RELATIVE_LINK.findall(md.read_text()):
                with self.subTest(file=str(md.relative_to(SKILLS)), link=target):
                    self.assertTrue((md.parent / target).exists())

    def test_agents_block_markers_and_budget(self):
        text = AGENTS_BLOCK.read_text()
        self.assertEqual(text.count('<!-- handoff:start'), 1)
        self.assertEqual(text.count('<!-- handoff:end -->'), 1)
        self.assertLess(text.index('<!-- handoff:start'), text.index('<!-- handoff:end -->'))
        self.assertLessEqual(len(text.split()), AGENTS_BLOCK_WORD_LIMIT)

    def test_shared_templates_match(self):
        for copies in SHARED_TEMPLATES:
            first = (SKILLS / copies[0]).read_text()
            for other in copies[1:]:
                with self.subTest(template=copies[0], copy=other):
                    self.assertEqual((SKILLS / other).read_text(), first)


if __name__ == '__main__':
    unittest.main()
