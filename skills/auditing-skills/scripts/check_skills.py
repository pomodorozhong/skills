#!/usr/bin/env python3
"""Check Agent Skills for the best-practice rules a script can decide.

Usage: python3 check_skills.py [--json] PATH [PATH ...]

PATH is a skill folder (one that holds SKILL.md), or any folder to search for
skills, such as a repository root (finds .claude/skills/*, skills/*, and the
like) or ~/.claude/skills. Prints one finding per line as
`LEVEL skill file:line message`, where skill is the skill's folder relative to
PATH, then a summary.
Levels: ERROR breaks a hard rule, WARN goes against the guide, NOTE is worth a
look. Exits 1 when there is any ERROR, 2 when PATH holds no skill, else 0.

Standard library only, so it runs wherever Python 3.8 or later runs.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

# Limits from Anthropic's skill authoring guide.
NAME_MAX = 64
DESCRIPTION_MAX = 1024
BODY_MAX_LINES = 500
# Reference files longer than this need a table of contents near the top, so
# a partial read (such as `head -100`) still shows everything the file covers.
TOC_MIN_LINES = 100
TOC_SEARCH_LINES = 30
# The guide asks for at least three evaluation scenarios per skill.
MIN_EVALS = 3
RESERVED_WORDS = ('anthropic', 'claude')
# Folders never searched for skills: version control, dependencies, build
# output, and agent worktrees, which hold copies of the same skills. A folder
# with one of these names that holds SKILL.md is still a skill.
SKIP_DIRS = {'.git', '.hg', '.svn', 'node_modules', '.venv', 'venv', '__pycache__',
             '.tox', '.mypy_cache', '.pytest_cache', 'dist', 'build', '.next', 'target', 'worktrees',
             '.trash', '.Trash'}
# Files an agent or tool finds by convention, so nothing needs to link to them,
# and copies across skills are expected: evals, agent metadata such as Codex
# agents/openai.yaml, licenses, and dotfiles.
CONVENTION_DIRS = {'evals', 'agents'}
LICENSE_FILE = re.compile(r'^(LICEN[CS]E|COPYING|NOTICE)\b', re.I)
# Fields that mark an item in evals/*.json as a scenario: `query` in the
# guide's format, `prompt` in skill-creator's.
EVAL_QUERY_FIELDS = ('query', 'prompt')
# Link targets such as `URL` or `LINK` are template placeholders, not files.
PLACEHOLDER = re.compile(r'^[A-Z][A-Z0-9_-]*$')
# Bundled scripts meant to be run. Files deeper in scripts/, or named with a
# leading underscore, are helpers the scripts import, so nothing links to them.
RUNNABLE = {'.py', '.sh', '.bash', '.js', '.mjs', '.cjs', '.ts', '.rb', '.pl'}

NAME_PATTERN = re.compile(r'^[a-z0-9-]+$')
XML_TAG = re.compile(r'</?[A-Za-z][^>]*>')
LINK = re.compile(r'\]\(<?([^)\s>]+)>?(?:\s+"[^"]*")?\)')
FENCE = re.compile(r'^\s*(`{3,}|~{3,})(.*)$')
FIRST_OR_SECOND_PERSON = re.compile(r"\b(I can|I will|I'll|I help|you can|you'll|you will)\b", re.I)
WHEN_CLAUSE = re.compile(r'\b((use|read|load|invoke|apply) (it |this skill |this )?(when|whenever|for|if|before|after)|when the user|triggers?)\b', re.I)
WINDOWS_PATH = re.compile(r'\b[\w.-]+(\\[\w.-]+)+\.(md|py|sh|js|ts|json|ya?ml|txt|csv)\b')
MONTHS = 'January|February|March|April|May|June|July|August|September|October|November|December'
DATED_PHRASE = re.compile(rf'\b(before|after|until|since|as of|by)\s+((early|mid|late)[- ])?(({MONTHS})\s+)?(Q[1-4]\s+)?20\d\d\b', re.I)
CONTENTS_HEADING = re.compile(r'^#{1,6}\s*(table of )?contents\b', re.I)
ANCHOR_LIST_ITEM = re.compile(r'^\s*[-*\d.]+\s.*\]\(#')


class Finding:
    def __init__(self, level, skill, path, line, message):
        self.level, self.skill, self.path, self.line, self.message = level, skill, path, line, message

    def as_dict(self):
        return {'level': self.level, 'skill': self.skill, 'file': self.path, 'line': self.line, 'message': self.message}

    def __str__(self):
        where = f'{self.path}:{self.line}' if self.line else self.path
        return f'{self.level:<5} {self.skill}  {where}  {self.message}'


def find_skills(paths):
    """Return (label, real folder, installed name) for each skill under the given paths.

    The installed name is the folder name as found, before following any
    symlink, since that is the name the agent sees.

    A path that holds SKILL.md is one skill. Any other folder is searched at
    every depth, hidden folders included, so a repository root finds
    `.claude/skills/*`, `.agents/skills/*`, `skills/*`, plugin folders, and
    symlinked skills. The search does not look inside a skill (its assets may
    hold example SKILL.md files) or inside SKIP_DIRS.
    """
    skills, seen_skills = [], set()

    def add(label, folder):
        real = folder.resolve()
        if real not in seen_skills:
            seen_skills.add(real)
            skills.append((label, real, installed_name(folder)))

    for raw in paths:
        root = Path(raw).expanduser()
        if (root / 'SKILL.md').is_file():
            add(installed_name(root), root)
            continue
        if not root.is_dir():
            continue
        visited = set()
        for directory, dirnames, filenames in os.walk(root, followlinks=True):
            real = os.path.realpath(directory)
            if real in visited:
                dirnames[:] = []
                continue
            visited.add(real)
            if 'SKILL.md' in filenames:
                add(Path(directory).relative_to(root).as_posix(), Path(directory))
                dirnames[:] = []
                continue
            dirnames[:] = sorted(d for d in dirnames
                                 if d not in SKIP_DIRS or (Path(directory) / d / 'SKILL.md').is_file())
    return skills


def installed_name(folder):
    """The folder's own name, with `.` and `..` worked out but symlinks kept."""
    return Path(os.path.abspath(folder)).name


def skill_files(skill):
    """Every file in the skill, leaving out SKIP_DIRS such as node_modules."""
    files = []
    for directory, dirnames, filenames in os.walk(skill):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        files.extend(Path(directory) / name for name in filenames if name != '.DS_Store')
    return sorted(files)


def mentions(text, path):
    """Whether text names the file as a whole word, so `a.md` is not found in `data.md`."""
    return re.search(rf'(?<![\w.-]){re.escape(path.name)}(?![\w-])', text) is not None


def enclosing_skill(path, own):
    """The folder of the skill that holds path, other than own, or None."""
    for folder in [path] + list(path.parents):
        if folder == own:
            return None
        if (folder / 'SKILL.md').is_file():
            return folder
    return None


def parse_frontmatter(text):
    """Return (fields, body start line) from simple YAML frontmatter.

    Returns (None, 1) when there is no opening `---`, and (fields, None) when
    there is no closing one.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        return None, 1
    fields, key, i = {}, None, 1
    while i < len(lines) and lines[i].strip() != '---':
        line = lines[i]
        match = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', line)
        if match:
            key, value = match.group(1), match.group(2).strip()
            if value in ('>', '|', '>-', '|-', '>+', '|+'):
                value = ''
            fields[key] = value[1:-1] if len(value) > 1 and value[0] == value[-1] and value[0] in '"\'' else value
        elif key and line.startswith((' ', '\t')):
            fields[key] = (fields[key] + ' ' + line.strip()).strip()
        i += 1
    if i == len(lines):
        return fields, None
    return fields, i + 2


def code_flags(lines):
    """Yield (line, whether it is in a fenced code block); fence lines count as code.

    As in CommonMark, a fence closes only on the same character, at least as
    long and with nothing after it, so a ``` line inside a ~~~ or ```` block
    stays code. check_guide.py has the same function.
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


def prose_lines(text):
    """Yield (line number, line) outside fenced code blocks."""
    for number, (line, in_code) in enumerate(code_flags(text.splitlines()), 1):
        if not in_code:
            yield number, line


def local_links(text):
    """Yield (line number, target path without anchor) for relative links.

    Targets are percent-decoded, so `my%20file.md` names `my file.md`.
    """
    for number, line in prose_lines(text):
        for target in LINK.findall(line):
            if re.match(r'^[a-z][a-z0-9+.-]*:', target, re.I) or target.startswith('#'):
                continue
            target = urllib.parse.unquote(target.split('#', 1)[0])
            if target and not PLACEHOLDER.match(target):
                yield number, target


def inside(path, folder):
    try:
        path.relative_to(folder)
        return True
    except ValueError:
        return False


def check_frontmatter(folder_name, text, add):
    fields, body_start = parse_frontmatter(text)
    if fields is None:
        add('ERROR', 'SKILL.md', 1, 'no YAML frontmatter; it needs `name` and `description`')
        return 1
    if body_start is None:
        add('ERROR', 'SKILL.md', 1, 'frontmatter has no closing `---`, so agents cannot read it')
        return 1
    name = fields.get('name', '')
    if not name:
        add('ERROR', 'SKILL.md', 1, 'frontmatter has no `name`')
    else:
        if len(name) > NAME_MAX:
            add('ERROR', 'SKILL.md', 1, f'name is {len(name)} characters; the limit is {NAME_MAX}')
        if not NAME_PATTERN.match(name):
            add('ERROR', 'SKILL.md', 1, 'name may use only lowercase letters, numbers, and hyphens')
        for word in RESERVED_WORDS:
            if word in name.lower():
                add('ERROR', 'SKILL.md', 1, f'name contains the reserved word "{word}"')
        if name != folder_name:
            add('WARN', 'SKILL.md', 1, f'name "{name}" differs from its folder "{folder_name}"')
    description = fields.get('description', '')
    if not description:
        add('ERROR', 'SKILL.md', 1, 'frontmatter has no `description`')
    else:
        if len(description) > DESCRIPTION_MAX:
            add('ERROR', 'SKILL.md', 1, f'description is {len(description)} characters; the limit is {DESCRIPTION_MAX}')
        if XML_TAG.search(description):
            add('ERROR', 'SKILL.md', 1, 'description contains an XML tag')
        if FIRST_OR_SECOND_PERSON.search(description):
            add('WARN', 'SKILL.md', 1, 'description speaks as "I" or "you"; write it in third person or as a plain statement')
        if not WHEN_CLAUSE.search(description):
            add('WARN', 'SKILL.md', 1, 'description has no when-to-use clause such as "Use when ..."')
    return body_start


def by_convention(parts):
    """Whether a file (as path parts inside its skill) is found by convention."""
    return parts[0] in CONVENTION_DIRS or parts[-1].startswith('.') or bool(LICENSE_FILE.match(parts[-1]))


def read_text(path):
    # utf-8-sig drops a byte order mark, which would hide the frontmatter.
    return path.read_text(encoding='utf-8-sig', errors='replace')


def check_skill(skill, add, folder_name):
    skill_md = skill / 'SKILL.md'
    text = read_text(skill_md)
    body_start = check_frontmatter(folder_name, text, add)
    body_lines = len(text.splitlines()) - body_start + 1
    if body_lines > BODY_MAX_LINES:
        add('WARN', 'SKILL.md', None, f'body is {body_lines} lines; keep it under {BODY_MAX_LINES} and move details into reference files')

    files = skill_files(skill)
    markdown = [p for p in files if p.suffix == '.md']
    texts = {p: read_text(p) for p in markdown}
    linked_from = {}  # target path -> set of files that link to it

    for md in markdown:
        rel = md.relative_to(skill).as_posix()
        for number, target in local_links(texts[md]):
            if target.startswith('/'):
                # Relative to the repository root on GitHub; the root is unknown here.
                add('NOTE', rel, number, f'link to {target} is relative to the repository root, so it leaves the skill folder; fine for a project skill that stays in its repository, but it breaks if the skill is installed elsewhere')
                continue
            resolved = (md.parent / target).resolve()
            if not resolved.exists():
                add('ERROR', rel, number, f'broken link to {target}')
            elif not inside(resolved, skill):
                other = enclosing_skill(resolved if resolved.is_dir() else resolved.parent, skill)
                if other:
                    add('WARN', rel, number, f'link to {target} reaches into the "{other.name}" skill and breaks when the skills are installed separately; name the skill instead')
                else:
                    add('NOTE', rel, number, f'link to {target} leaves the skill folder; fine for a project skill that stays in its repository, but it breaks if the skill is installed elsewhere')
            else:
                linked_from.setdefault(resolved, set()).add(md)
                if md != skill_md and resolved.suffix == '.md' and resolved != skill_md.resolve() and 'assets' not in resolved.relative_to(skill).parts:
                    add('NOTE', rel, number, f'chained reference: sends the reader on to {resolved.relative_to(skill).as_posix()}; make each reference complete on its own')
        for number, line in prose_lines(texts[md]):
            if WINDOWS_PATH.search(line):
                add('WARN', rel, number, 'Windows-style path; use forward slashes')
            match = DATED_PHRASE.search(line)
            if match:
                add('WARN', rel, number, f'time-sensitive wording "{match.group(0)}"; move it to an "Old patterns" section or drop the date')

    # One level deep: every bundled reference, asset, and script should be
    # reachable straight from SKILL.md, by link or by naming its path.
    skill_text = texts[skill_md]
    script_texts = {p: read_text(p) for p in files if p.suffix in RUNNABLE}
    for path in files:
        rel = path.relative_to(skill).as_posix()
        parts = path.relative_to(skill).parts
        # Skip SKILL.md, convention files, and the inside of an example skill
        # bundled as an asset (it is used as a whole).
        if path == skill_md or by_convention(parts) or enclosing_skill(path.parent, skill):
            continue
        if parts[0] == 'scripts' and path.suffix in RUNNABLE:
            if len(parts) > 2 or path.name.startswith('_'):
                continue  # a helper the scripts import
            # Scripts are run, not read, so naming one in any instruction file
            # is enough; another script calling or importing it is too.
            # Match whole names, so `check.py` is not named by "checks".
            named = re.compile(rf'\bscripts/{re.escape(path.stem)}\b')
            imported = re.compile(rf'\b(import|from)\s+{re.escape(path.stem)}\b')
            if any(mentions(t, path) or named.search(t) for t in texts.values()) or any(
                    mentions(t, path) or named.search(t) or imported.search(t) for p, t in script_texts.items() if p != path):
                continue
            add('WARN', rel, None, 'no instruction names this script, so it will never be run')
            continue
        sources = linked_from.get(path.resolve(), set())
        if skill_md in sources or mentions(skill_text, path):
            continue
        if path.suffix != '.md' and any(mentions(t, path) for t in script_texts.values()):
            continue  # data a script loads
        mentioned_by = sorted(p.relative_to(skill).as_posix() for p in sources) or [
            m.relative_to(skill).as_posix() for m in markdown if m != path and mentions(texts[m], path)]
        if mentioned_by:
            add('WARN', rel, None, f'reachable only through {", ".join(mentioned_by)}; link it from SKILL.md so references stay one level deep')
        else:
            add('WARN', rel, None, 'nothing points to this file, so it will never be read or run')

    for md in markdown:
        if md == skill_md:
            continue
        lines = texts[md].splitlines()
        if len(lines) > TOC_MIN_LINES:
            head = lines[:TOC_SEARCH_LINES]
            if not any(CONTENTS_HEADING.match(l) for l in head) and sum(bool(ANCHOR_LIST_ITEM.match(l)) for l in head) < 3:
                add('WARN', md.relative_to(skill).as_posix(), None, f'{len(lines)} lines with no table of contents in its first {TOC_SEARCH_LINES} lines')

    check_evals(skill, add)
    return files


def check_evals(skill, add):
    count = 0
    for path in sorted((skill / 'evals').glob('*.json')) if (skill / 'evals').is_dir() else []:
        rel = path.relative_to(skill).as_posix()
        try:
            data = json.loads(path.read_text(encoding='utf-8-sig'))
        except (ValueError, UnicodeDecodeError) as error:
            add('ERROR', rel, None, f'not valid JSON: {error}')
            continue
        items = data.get('evals', []) if isinstance(data, dict) else data
        found = sum(1 for item in items if isinstance(item, dict) and any(
            isinstance(item.get(field), str) and item[field].strip() for field in EVAL_QUERY_FIELDS)) if isinstance(items, list) else 0
        if not found:
            add('NOTE', rel, None, f'no scenarios found; expected a list of objects with {" or ".join(EVAL_QUERY_FIELDS)}')
        count += found
    if count == 0:
        add('WARN', 'evals/', None, f'no evaluation scenarios; the guide asks for at least {MIN_EVALS}')
    elif count < MIN_EVALS:
        add('WARN', 'evals/', None, f'{count} evaluation scenarios; the guide asks for at least {MIN_EVALS}')


def check_duplicates(all_files, adder):
    """all_files holds (label, skill folder, file); adder(label) gives that skill's add.

    Empty files (such as `__init__.py`) are left out: they match without being copies.
    """
    by_hash = {}
    for label, skill, path in all_files:
        if by_convention(path.relative_to(skill).parts) or path.stat().st_size == 0:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        by_hash.setdefault(digest, []).append((label, skill, path))
    for copies in by_hash.values():
        if len({label for label, _, _ in copies}) < 2:
            continue
        names = [f'{label}/{p.relative_to(s).as_posix()}' for label, s, p in copies]
        for (label, skill, path), name in zip(copies, names):
            others = [n for n in names if n != name]
            adder(label)('NOTE', path.relative_to(skill).as_posix(), None, f'identical to {", ".join(others)}; keep the copies in sync')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('paths', nargs='+', metavar='PATH', help='a skill folder, or a folder to search for skills (such as a repository root)')
    parser.add_argument('--json', action='store_true', help='print findings as a JSON list')
    args = parser.parse_args(argv)

    skills = find_skills(args.paths)
    if not skills:
        print(f'No SKILL.md found in {", ".join(args.paths)}', file=sys.stderr)
        return 2

    findings, all_files = [], []

    def adder(label):
        return lambda level, path, line, message: findings.append(Finding(level, label, path, line, message))

    for label, skill, folder_name in skills:
        files = check_skill(skill, adder(label), folder_name)
        all_files.extend((label, skill, f) for f in files if f.name != 'SKILL.md')
    check_duplicates(all_files, adder)

    order = {'ERROR': 0, 'WARN': 1, 'NOTE': 2}
    findings.sort(key=lambda f: (f.skill, order[f.level], f.path, f.line or 0))
    if args.json:
        print(json.dumps([f.as_dict() for f in findings], indent=2))
    else:
        for finding in findings:
            print(finding)
        totals = {level: sum(f.level == level for f in findings) for level in order}
        print(f'\n{totals["ERROR"]} errors, {totals["WARN"]} warnings, {totals["NOTE"]} notes in {len(skills)} skills')
    return 1 if any(f.level == 'ERROR' for f in findings) else 0


if __name__ == '__main__':
    sys.exit(main())
