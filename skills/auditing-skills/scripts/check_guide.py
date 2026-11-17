#!/usr/bin/env python3
"""Check whether Anthropic's skill authoring guide changed since the checklist.

Usage: python3 check_guide.py [--show] [--update]

Fetches the Markdown version of the guide (about 40 KB; the page has no
Last-Modified or ETag header to compare instead), hashes it whole and per
section, and compares the hashes with references/guide-snapshot.json.

  exit 0  up to date: the whole-page hash matches the snapshot
  exit 1  changed: prints the sections added, removed, or changed;
          --show also prints the current text of those sections
  exit 2  could not fetch the guide; audit with the snapshot
  exit 3  the snapshot is missing or unreadable, so changes cannot be listed

--update rewrites the snapshot from the current guide. Run it only after the
checklist has been brought up to date with every changed section.

Standard library only, so it runs wherever Python 3.8 or later runs.
"""
import argparse
import datetime
import hashlib
import http.client
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

GUIDE_URL = 'https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices.md'
SNAPSHOT = Path(__file__).resolve().parent.parent / 'references' / 'guide-snapshot.json'
# Long enough for a slow connection, short enough not to stall an audit.
TIMEOUT_SECONDS = 20
HEADING = re.compile(r'^(#{2,3})\s+(.+?)\s*$')
FENCE = re.compile(r'^\s*(`{3,}|~{3,})(.*)$')
SNAPSHOT_KEYS = ('checked', 'sha256', 'sections')


def sha256(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def normalize(text):
    """Collapse whitespace so reflowed lines alone do not count as a change."""
    return re.sub(r'\s+', ' ', text).strip()


def code_flags(lines):
    """Yield (line, whether it is in a fenced code block); fence lines count as code.

    As in CommonMark, a fence closes only on the same character, at least as
    long and with nothing after it, so a ``` line inside a ~~~ or ```` block
    stays code. check_skills.py has the same function.
    """
    fence = None
    for line in lines:
        match = FENCE.match(line)
        if fence is None:
            if match and not (match.group(1)[0] == '`' and '`' in match.group(2)):
                fence = match.group(1)
                yield line, True
            else:
                yield line, False
        else:
            if (match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence)
                    and not match.group(2).strip()):
                fence = None
            yield line, True


def sections(markdown):
    """Map 'Section > Subsection' to its text. Headings in code blocks are content.

    A heading path that occurs more than once gets its content's short hash as
    a suffix, such as 'Key findings [0c13ffde]', rather than a number by
    position, so adding or moving one copy does not rename the others.
    """
    parts, parent = [('(intro)', [])], None
    for line, in_code in code_flags(markdown.splitlines()):
        match = None if in_code else HEADING.match(line)
        if match:
            level, title = len(match.group(1)), match.group(2)
            if level == 2:
                parent, name = title, title
            else:
                name = f'{parent} > {title}' if parent else title
            parts.append((name, []))
        parts[-1][1].append(line)
    counts = {}
    for name, _ in parts:
        counts[name] = counts.get(name, 0) + 1
    result = {}
    for name, lines in parts:
        text = '\n'.join(lines).strip()
        if counts[name] > 1:
            name = f'{name} [{sha256(normalize(text))[:8]}]'
        while name in result:  # identical copies
            name += '+'
        result[name] = text
    return result


def fetch():
    request = urllib.request.Request(GUIDE_URL, headers={'User-Agent': 'auditing-skills-check-guide'})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read().decode('utf-8')


def load_snapshot():
    """Return (snapshot or None, why it is missing or unreadable)."""
    if not SNAPSHOT.is_file():
        return None, f'No snapshot at {SNAPSHOT}'
    try:
        snapshot = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    except (ValueError, OSError) as error:
        return None, f'The snapshot at {SNAPSHOT} is unreadable ({error})'
    if not isinstance(snapshot, dict) or any(key not in snapshot for key in SNAPSHOT_KEYS):
        return None, f'The snapshot at {SNAPSHOT} lacks one of {", ".join(SNAPSHOT_KEYS)}'
    sections = snapshot['sections']
    if (not isinstance(snapshot['checked'], str) or not isinstance(snapshot['sha256'], str)
            or not isinstance(sections, dict)
            or not all(isinstance(value, str) for value in sections.values())):
        return None, f'The snapshot at {SNAPSHOT} has a field of the wrong type'
    return snapshot, None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--show', action='store_true', help='print the current text of changed and added sections')
    parser.add_argument('--update', action='store_true', help='rewrite the snapshot from the current guide')
    args = parser.parse_args(argv)

    snapshot, problem = load_snapshot()
    try:
        markdown = fetch()
    # HTTPException covers a cut-off response (IncompleteRead), which is not an OSError.
    except (urllib.error.URLError, OSError, http.client.HTTPException, UnicodeDecodeError) as error:
        when = f'snapshot of {snapshot["checked"]}' if snapshot else f'{problem.lower()}; date unknown'
        print(f'Could not fetch {GUIDE_URL}: {error}. Audit with the checklist ({when}) and say so.')
        return 2

    current = {name: sha256(normalize(text)) for name, text in sections(markdown).items()}
    page_hash = sha256(normalize(markdown))

    if args.update:
        SNAPSHOT.write_text(json.dumps({
            'url': GUIDE_URL,
            'checked': datetime.date.today().isoformat(),
            'sha256': page_hash,
            'sections': current,
        }, indent=2) + '\n', encoding='utf-8')
        print(f'Snapshot updated: {len(current)} sections, sha256 {page_hash[:12]}.')
        return 0

    if snapshot is None:
        print(f'{problem}, so changes cannot be listed. Compare the whole guide with the checklist, then run with --update.')
        return 3
    if snapshot['sha256'] == page_hash:
        print(f'Up to date: the guide matches the checklist snapshot of {snapshot["checked"]}.')
        return 0

    old = snapshot['sections']
    added = [n for n in current if n not in old]
    removed = [n for n in old if n not in current]
    changed = [n for n in current if n in old and current[n] != old[n]]
    print(f'The guide changed since the checklist snapshot of {snapshot["checked"]}.')
    for label, names in (('Added', added), ('Removed', removed), ('Changed', changed)):
        for name in names:
            print(f'  {label}: {name}')
    if not (added or removed or changed):
        print('  Only the order of sections changed.')
    if args.show:
        text = sections(markdown)
        for name in added + changed:
            print(f'\n===== {name}\n{text[name]}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
