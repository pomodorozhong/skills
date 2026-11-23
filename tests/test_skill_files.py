"""Static checks on the skill files themselves.

These read the Markdown under skills/ and run no agent. They catch broken
links between skill files and drift between template copies shared by
several skills.

Run from the repo root: python3 -m unittest discover tests
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / 'skills'

# Relative Markdown link targets; web links and same-file anchors are skipped.
RELATIVE_LINK = re.compile(r'\]\((?!https?://|#)([^)#\s]+)')

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

    def test_shared_templates_match(self):
        for copies in SHARED_TEMPLATES:
            first = (SKILLS / copies[0]).read_text()
            for other in copies[1:]:
                with self.subTest(template=copies[0], copy=other):
                    self.assertEqual((SKILLS / other).read_text(), first)


if __name__ == '__main__':
    unittest.main()
