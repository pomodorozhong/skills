"""Tests for skills/auditing-skills/scripts/check_guide.py.

The guide is never fetched: each test swaps in its own Markdown and snapshot
path. Run from the repo root: python3 -m unittest discover tests
"""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / 'skills' / 'auditing-skills' / 'scripts' / 'check_guide.py'

spec = importlib.util.spec_from_file_location('check_guide', SCRIPT)
check_guide = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_guide)

GUIDE = '''Intro.

## Core principles

### Concise is key

Be brief.

```markdown
## Not a section
```

### Degrees of freedom

Match the risk.
'''


class CheckGuideTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='check-guide-test-')
        self.addCleanup(temp.cleanup)
        self.snapshot = Path(temp.name) / 'guide-snapshot.json'
        patcher = mock.patch.object(check_guide, 'SNAPSHOT', self.snapshot)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_with(self, markdown, *args):
        out = io.StringIO()
        fetch = mock.Mock(side_effect=markdown) if isinstance(markdown, Exception) else mock.Mock(return_value=markdown)
        with mock.patch.object(check_guide, 'fetch', fetch), contextlib.redirect_stdout(out):
            code = check_guide.main(list(args))
        return code, out.getvalue()

    def test_sections_skip_headings_in_code(self):
        names = list(check_guide.sections(GUIDE))
        self.assertEqual(names, ['(intro)', 'Core principles', 'Core principles > Concise is key', 'Core principles > Degrees of freedom'])

    def test_up_to_date_after_update_and_whitespace_changes(self):
        self.assertEqual(self.run_with(GUIDE, '--update')[0], 0)
        code, out = self.run_with(GUIDE.replace('Be brief.', 'Be\n   brief.'))
        self.assertEqual(code, 0)
        self.assertIn('Up to date', out)

    def test_changed_lists_sections_and_show_prints_them(self):
        self.run_with(GUIDE, '--update')
        new = GUIDE.replace('Match the risk.', 'Match the risk and the model.') + '\n### Use scripts\n\nRun them.\n'
        new = new.replace('### Concise is key\n\nBe brief.\n', '')
        code, out = self.run_with(new, '--show')
        self.assertEqual(code, 1)
        self.assertIn('Added: Core principles > Use scripts', out)
        self.assertIn('Removed: Core principles > Concise is key', out)
        self.assertIn('Changed: Core principles > Degrees of freedom', out)
        self.assertIn('Match the risk and the model.', out)
        self.assertNotIn('Be brief', out)

    def test_fetch_failure_exits_2(self):
        self.run_with(GUIDE, '--update')
        code, out = self.run_with(urllib.error.URLError('offline'))
        self.assertEqual(code, 2)
        self.assertIn('Audit with the checklist snapshot', out)

    def test_bundled_snapshot_is_valid(self):
        data = json.loads((SCRIPT.parent.parent / 'references' / 'guide-snapshot.json').read_text())
        self.assertEqual(data['url'], check_guide.GUIDE_URL)
        self.assertRegex(data['sha256'], r'^[0-9a-f]{64}$')
        self.assertGreater(len(data['sections']), 20)


if __name__ == '__main__':
    unittest.main()
