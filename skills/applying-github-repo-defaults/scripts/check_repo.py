#!/usr/bin/env python3
"""Compare a GitHub repo's settings with the defaults in ../assets/.

Usage: check_repo.py <owner>/<repo> [--json]

Reads settings with `gh api` and changes nothing. When an existing ruleset
needs rules added, the update it would send is written to a temporary file.
For each setting it reports
one of three states:

  ok           matches the default
  differs      doesn't match; the line after it is the command that fixes it
  unavailable  GitHub doesn't offer it for this repo (plan, visibility, access)

Exit status: 0 when nothing differs, 1 when something differs, 2 on an error
such as a repo that can't be read.
"""
import copy
import json
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / 'assets'
DEFAULT_BRANCH_REFS = {'~DEFAULT_BRANCH', '~ALL'}


def gh_fetch(path, paginate=False):
    """Return (HTTP status, parsed body) for a GET through `gh api`.

    With paginate, the path must return a JSON array; every page is read and
    the pages are joined into one list.
    """
    command = ['gh', 'api', path] + (['--paginate', '--slurp'] if paginate else [])
    result = subprocess.run(command, capture_output=True, text=True)
    try:
        body = json.loads(result.stdout) if result.stdout.strip() else None
    except json.JSONDecodeError:
        body = None
    if result.returncode == 0:
        if paginate and isinstance(body, list):
            body = [item for page in body for item in (page or [])]
        return 200, body
    match = re.search(r'HTTP (\d{3})', result.stderr)
    status = int(match.group(1)) if match else 0
    if isinstance(body, list):
        # --slurp wraps the error body in a list, as it does each page.
        body = body[0] if body and isinstance(body[0], dict) else None
    if body is None:
        body = {'message': result.stderr.strip() or 'gh api failed'}
    return status, body


def load_defaults(assets=ASSETS):
    defaults = json.loads((assets / 'defaults.json').read_text())
    ruleset_path = assets / defaults['ruleset']['file']
    return defaults, json.loads(ruleset_path.read_text()), ruleset_path


def shown(value):
    return json.dumps(value) if not isinstance(value, str) else value


def result(setting, state, now=None, want=None, why='', fix=None, note=None, loosens=None):
    return {'setting': setting, 'state': state, 'now': now, 'want': want,
            'why': why, 'fix': fix, 'note': note, 'loosens': loosens or []}


def field_arg(name, value):
    """Return a quoted `gh api` field flag: -f keeps a string as is, -F types booleans and numbers."""
    if isinstance(value, str):
        return '-f ' + shlex.quote(f'{name}={value}')
    return '-F ' + shlex.quote(f'{name}={json.dumps(value)}')


def hidden_note(data, need, otherwise):
    """Say why GitHub left a field out: missing access if the user lacks it, else `otherwise`."""
    if not (data.get('permissions') or {}).get(need, True):
        return f'GitHub shows it only to people with {need} access to the repo, and you have none'
    return otherwise


def message(body):
    return body.get('message', 'no details') if isinstance(body, dict) else 'no details'


def check_repo_fields(repo, data, defaults):
    out = []
    # GitHub refuses to turn off every merge method at once, so squash is fixed first.
    fields = sorted(defaults['repo'].items(), key=lambda item: item[0] != 'allow_squash_merge')
    for field, spec in fields:
        if field not in data:
            note = hidden_note(data, 'push', 'GitHub did not return it; check the field name in assets/defaults.json')
            out.append(result(field, 'unavailable', want=spec['want'], why=spec['why'], note=note))
            continue
        now = data[field]
        if now == spec['want']:
            out.append(result(field, 'ok', now, spec['want'], spec['why']))
        else:
            fix = f"gh api -X PATCH repos/{repo} {field_arg(field, spec['want'])}"
            out.append(result(field, 'differs', now, spec['want'], spec['why'], fix))
    return out


def check_security(repo, data, defaults):
    out = []
    current = data.get('security_and_analysis') or {}
    for feature, spec in defaults['security_and_analysis'].items():
        name = f'security_and_analysis.{feature}'
        if feature not in current:
            note = hidden_note(data, 'admin', 'not offered for this repo; private repos need GitHub Advanced Security')
            out.append(result(name, 'unavailable', want=spec['want'], why=spec['why'], note=note))
            continue
        now = current[feature].get('status')
        if now == spec['want']:
            out.append(result(name, 'ok', now, spec['want'], spec['why']))
        else:
            field = f"security_and_analysis[{feature}][status]={spec['want']}"
            fix = f'gh api -X PATCH repos/{repo} -f {shlex.quote(field)}'
            out.append(result(name, 'differs', now, spec['want'], spec['why'], fix))
    return out


def check_actions(repo, fetch, defaults):
    out = []
    status, body = fetch(f'repos/{repo}/actions/permissions/workflow')
    for field, spec in defaults['actions_workflow_permissions'].items():
        name = f'actions.{field}'
        if status != 200:
            out.append(result(name, 'unavailable', want=spec['want'], why=spec['why'],
                              note=f'could not read it (HTTP {status}: {message(body)})'))
            continue
        now = body.get(field)
        if now == spec['want']:
            out.append(result(name, 'ok', now, spec['want'], spec['why']))
        else:
            fix = (f"gh api -X PUT repos/{repo}/actions/permissions/workflow "
                   f"{field_arg(field, spec['want'])}")
            out.append(result(name, 'differs', now, spec['want'], spec['why'], fix))
    return out


def check_description(repo, data, defaults):
    spec = defaults['description']
    now = (data.get('description') or '').strip()
    if now:
        return [result('description', 'ok', now, spec['want'], spec['why'])]
    fix = f"gh repo edit {repo} --description '<one line on what the repo is for>'"
    return [result('description', 'differs', '(empty)', spec['want'], spec['why'], fix,
                   note='needs the text from the user')]


def same_items(a, b):
    """Compare two lists in any order; items may be objects, which can't be sorted directly."""
    def key(item):
        return json.dumps(item, sort_keys=True)
    return sorted(map(key, a)) == sorted(map(key, b))


def rule_matches(want, have):
    if want['type'] != have.get('type'):
        return False
    params = have.get('parameters') or {}
    for key, value in (want.get('parameters') or {}).items():
        current = params.get(key)
        if isinstance(value, list):
            if not same_items(current or [], value):
                return False
        elif current != value:
            return False
    return True


def ref_pattern_matches(pattern, ref):
    """Match a ruleset ref pattern the way GitHub does: `*` stops at `/`, `**` doesn't."""
    if pattern in DEFAULT_BRANCH_REFS:
        return True
    regex = ''
    for part in re.split(r'(\*\*|\*|\?)', pattern):
        regex += {'**': '.*', '*': '[^/]*', '?': '[^/]'}.get(part, re.escape(part))
    return re.fullmatch(regex, ref) is not None


def covers_default_branch(ruleset, default_branch):
    ref_name = (ruleset.get('conditions') or {}).get('ref_name') or {}
    ref = f'refs/heads/{default_branch}'
    included = any(ref_pattern_matches(p, ref) for p in ref_name.get('include') or [])
    excluded = any(ref_pattern_matches(p, ref) for p in ref_name.get('exclude') or [])
    return included and not excluded


def merged_ruleset(existing, wanted, default_branch):
    """Return existing with the wanted rules added, so an update in place loses nothing.

    Rules of a type the wanted ruleset has are merged parameter by parameter;
    every other rule, the bypass actors, and the branches it already covers stay.
    """
    rules = [copy.deepcopy(r) for r in existing.get('rules') or []]
    for want in wanted['rules']:
        have = next((r for r in rules if r.get('type') == want['type']), None)
        if have is None:
            rules.append(copy.deepcopy(want))
        elif want.get('parameters'):
            have['parameters'] = {**(have.get('parameters') or {}), **want['parameters']}
    ref_name = (existing.get('conditions') or {}).get('ref_name') or {}
    ref = f'refs/heads/{default_branch}'
    include = list(ref_name.get('include') or [])
    include += [p for p in wanted['conditions']['ref_name']['include'] if p not in include]
    exclude = [p for p in ref_name.get('exclude') or [] if not ref_pattern_matches(p, ref)]
    return {
        'name': existing['name'],
        'target': wanted['target'],
        'enforcement': wanted['enforcement'],
        'conditions': {'ref_name': {'include': include, 'exclude': exclude}},
        'rules': rules,
        'bypass_actors': existing.get('bypass_actors') or [],
    }


def loosened_parameters(existing, wanted):
    """Return the parameters the update would make less strict, as 'name now -> want' strings.

    A parameter loosens when a true setting would become false or a number
    (such as the required approval count) would go down.
    """
    out = []
    for want in wanted['rules']:
        have = next((r for r in existing.get('rules') or [] if r.get('type') == want['type']), None)
        params = (have or {}).get('parameters') or {}
        for key, value in (want.get('parameters') or {}).items():
            current = params.get(key)
            if isinstance(value, bool) or isinstance(current, bool):
                looser = current is True and value is False
            elif isinstance(value, (int, float)) and isinstance(current, (int, float)):
                looser = current > value
            else:
                looser = False
            if looser:
                out.append(f'{key} {json.dumps(current)} -> {json.dumps(value)}')
    return out


def check_ruleset(repo, data, fetch, defaults, wanted, wanted_path):
    spec = defaults['ruleset']
    name = 'ruleset'
    want = f"{wanted['name']}: " + ', '.join(r['type'] for r in wanted['rules'])
    status, listing = fetch(f'repos/{repo}/rulesets', paginate=True)
    if status != 200:
        return [result(name, 'unavailable', want=want, why=spec['why'],
                       note=f'rulesets are not available here (HTTP {status}: {message(listing)})')]
    rules, same_name = [], None
    default_branch = data.get('default_branch', '')
    for summary in listing or []:
        status, ruleset = fetch(f"repos/{repo}/rulesets/{summary['id']}")
        if status != 200:
            return [result(name, 'unavailable', want=want, why=spec['why'],
                           note=f"could not read ruleset {summary['id']} (HTTP {status}: {message(ruleset)})")]
        if ruleset.get('name') == wanted['name'] and ruleset.get('source_type', 'Repository') == 'Repository':
            same_name = ruleset
        if (ruleset.get('target') == 'branch' and ruleset.get('enforcement') == 'active'
                and covers_default_branch(ruleset, default_branch)):
            rules.extend(ruleset.get('rules') or [])
    missing = [w['type'] for w in wanted['rules'] if not any(rule_matches(w, h) for h in rules)]
    if not missing:
        return [result(name, 'ok', 'all rules present', want, spec['why'])]
    now = 'these rules missing or different: ' + ', '.join(missing)
    if same_name is None:
        fix = f'gh api -X POST repos/{repo}/rulesets --input {shlex.quote(str(wanted_path))}'
        return [result(name, 'differs', now, want, spec['why'], fix)]
    update = merged_ruleset(same_name, wanted, default_branch)
    path = Path(tempfile.gettempdir()) / 'applying-github-repo-defaults' / (
        f"{repo.replace('/', '-')}-ruleset-{same_name['id']}.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(update, indent=2) + '\n')
    fix = f"gh api -X PUT repos/{repo}/rulesets/{same_name['id']} --input {shlex.quote(str(path))}"
    kept = len(update['rules']) - len(wanted['rules'])
    note = (f"updates the existing {wanted['name']} ruleset in place; keeps its {kept} other rule(s), "
            f"{len(update['bypass_actors'])} bypass actor(s), and the branches it covers")
    loosened = loosened_parameters(same_name, wanted)
    if loosened:
        note += ('. WARNING: this lowers protection the ruleset has now: ' + ', '.join(loosened)
                 + f"; to keep them, edit {path} before running the fix")
    return [result(name, 'differs', now, want, spec['why'], fix, note=note, loosens=loosened)]


def check(repo, fetch=gh_fetch, assets=ASSETS):
    """Return the list of results for repo, or raise RuntimeError if it can't be read."""
    defaults, wanted, wanted_path = load_defaults(assets)
    status, data = fetch(f'repos/{repo}')
    if status != 200:
        raise RuntimeError(f'cannot read {repo} (HTTP {status}: {message(data)})')
    return (check_repo_fields(repo, data, defaults)
            + check_security(repo, data, defaults)
            + check_actions(repo, fetch, defaults)
            + check_description(repo, data, defaults)
            + check_ruleset(repo, data, fetch, defaults, wanted, wanted_path))


def report(repo, results):
    counts = {s: sum(r['state'] == s for r in results) for s in ('ok', 'differs', 'unavailable')}
    lines = [f"{repo}: {counts['differs']} differ, {counts['ok']} ok, {counts['unavailable']} unavailable"]
    for r in results:
        if r['state'] == 'ok':
            continue
        if r['state'] == 'differs':
            lines.append(f"\ndiffers  {r['setting']}: now {shown(r['now'])}, want {shown(r['want'])}")
        else:
            lines.append(f"\nunavailable  {r['setting']}: {r['note']}")
        lines.append(f"  why: {r['why']}")
        if r['state'] == 'differs' and r['note']:
            lines.append(f"  note: {r['note']}")
        if r['fix']:
            lines.append(f"  fix: {r['fix']}")
    return '\n'.join(lines)


def main(argv):
    args = [a for a in argv if a != '--json']
    if len(args) != 1 or not re.fullmatch(r'[\w.-]+/[\w.-]+', args[0]):
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    repo = args[0]
    try:
        results = check(repo)
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 2
    if '--json' in argv:
        print(json.dumps({'repo': repo, 'results': results}, indent=2))
    else:
        print(report(repo, results))
    return 1 if any(r['state'] == 'differs' for r in results) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
