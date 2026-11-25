#!/usr/bin/env python3
"""Compare a GitHub repo's settings with the defaults in ../assets/.

Usage: check_repo.py <owner>/<repo> [--json]

Reads settings with `gh api` and changes nothing. For each setting it reports
one of three states:

  ok           matches the default
  differs      doesn't match; the line after it is the command that fixes it
  unavailable  GitHub doesn't offer it for this repo (plan, visibility, access)

Exit status: 0 when nothing differs, 1 when something differs, 2 on an error
such as a repo that can't be read.
"""
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / 'assets'
DEFAULT_BRANCH_REFS = {'~DEFAULT_BRANCH', '~ALL'}


def gh_fetch(path):
    """Return (HTTP status, parsed body) for a GET through `gh api`."""
    result = subprocess.run(['gh', 'api', path], capture_output=True, text=True)
    try:
        body = json.loads(result.stdout) if result.stdout.strip() else None
    except json.JSONDecodeError:
        body = None
    if result.returncode == 0:
        return 200, body
    match = re.search(r'HTTP (\d{3})', result.stderr)
    status = int(match.group(1)) if match else 0
    if body is None:
        body = {'message': result.stderr.strip() or 'gh api failed'}
    return status, body


def load_defaults(assets=ASSETS):
    defaults = json.loads((assets / 'defaults.json').read_text())
    ruleset_path = assets / defaults['ruleset']['file']
    return defaults, json.loads(ruleset_path.read_text()), ruleset_path


def shown(value):
    return json.dumps(value) if not isinstance(value, str) else value


def result(setting, state, now=None, want=None, why='', fix=None, note=None):
    return {'setting': setting, 'state': state, 'now': now, 'want': want,
            'why': why, 'fix': fix, 'note': note}


def message(body):
    return (body or {}).get('message', 'no details')


def check_repo_fields(repo, data, defaults):
    out = []
    for field, spec in defaults['repo'].items():
        if field not in data:
            out.append(result(field, 'unavailable', want=spec['want'], why=spec['why'],
                              note='GitHub did not return it; it is shown only to people with push access'))
            continue
        now = data[field]
        if now == spec['want']:
            out.append(result(field, 'ok', now, spec['want'], spec['why']))
        else:
            fix = f"gh api -X PATCH repos/{repo} -F {field}={shown(spec['want'])}"
            out.append(result(field, 'differs', now, spec['want'], spec['why'], fix))
    return out


def check_security(repo, data, defaults):
    out = []
    current = data.get('security_and_analysis') or {}
    for feature, spec in defaults['security_and_analysis'].items():
        name = f'security_and_analysis.{feature}'
        if feature not in current:
            out.append(result(name, 'unavailable', want=spec['want'], why=spec['why'],
                              note='not offered for this repo; private repos need GitHub Advanced Security'))
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
            flag = '-f' if isinstance(spec['want'], str) else '-F'
            fix = (f"gh api -X PUT repos/{repo}/actions/permissions/workflow "
                   f"{flag} {field}={shown(spec['want'])}")
            out.append(result(name, 'differs', now, spec['want'], spec['why'], fix))
    return out


def check_description(repo, data, defaults):
    spec = defaults['description']
    now = (data.get('description') or '').strip()
    if now:
        return [result('description', 'ok', now, spec['want'], spec['why'])]
    fix = f'gh repo edit {repo} --description "<one line on what the repo is for>"'
    return [result('description', 'differs', '(empty)', spec['want'], spec['why'], fix,
                   note='needs the text from the user')]


def rule_matches(want, have):
    if want['type'] != have.get('type'):
        return False
    params = have.get('parameters') or {}
    for key, value in (want.get('parameters') or {}).items():
        current = params.get(key)
        if isinstance(value, list):
            if sorted(current or []) != sorted(value):
                return False
        elif current != value:
            return False
    return True


def covers_default_branch(ruleset, default_branch):
    include = set(((ruleset.get('conditions') or {}).get('ref_name') or {}).get('include') or [])
    return bool(include & (DEFAULT_BRANCH_REFS | {f'refs/heads/{default_branch}'}))


def check_ruleset(repo, data, fetch, defaults, wanted, wanted_path):
    spec = defaults['ruleset']
    name = 'ruleset'
    want = f"{wanted['name']}: " + ', '.join(r['type'] for r in wanted['rules'])
    status, listing = fetch(f'repos/{repo}/rulesets')
    if status != 200:
        return [result(name, 'unavailable', want=want, why=spec['why'],
                       note=f'rulesets are not available here (HTTP {status}: {message(listing)})')]
    rules, same_name_id = [], None
    for summary in listing or []:
        status, ruleset = fetch(f"repos/{repo}/rulesets/{summary['id']}")
        if status != 200:
            return [result(name, 'unavailable', want=want, why=spec['why'],
                           note=f"could not read ruleset {summary['id']} (HTTP {status}: {message(ruleset)})")]
        if ruleset.get('name') == wanted['name'] and ruleset.get('source_type', 'Repository') == 'Repository':
            same_name_id = ruleset['id']
        if (ruleset.get('target') == 'branch' and ruleset.get('enforcement') == 'active'
                and covers_default_branch(ruleset, data.get('default_branch', ''))):
            rules.extend(ruleset.get('rules') or [])
    missing = [w['type'] for w in wanted['rules'] if not any(rule_matches(w, h) for h in rules)]
    if not missing:
        return [result(name, 'ok', 'all rules present', want, spec['why'])]
    path = shlex.quote(str(wanted_path))
    if same_name_id is not None:
        fix = f'gh api -X PUT repos/{repo}/rulesets/{same_name_id} --input {path}'
    else:
        fix = f'gh api -X POST repos/{repo}/rulesets --input {path}'
    now = 'these rules missing or different: ' + ', '.join(missing)
    return [result(name, 'differs', now, want, spec['why'], fix)]


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
