"""Fixture tests for skills/applying-github-repo-defaults/scripts/check_repo.py.

Each test feeds stored API responses to the check instead of calling GitHub,
so nothing touches the network. Run from the repo root:
python3 -m unittest discover tests
"""
import copy
import importlib.util
import json
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / 'skills' / 'applying-github-repo-defaults' / 'scripts' / 'check_repo.py'

spec = importlib.util.spec_from_file_location('check_repo', SCRIPT)
check_repo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_repo)

REPO = 'octo/demo'

MATCHING_RULESET = {
    'id': 7, 'name': 'main-protection', 'target': 'branch', 'enforcement': 'active',
    'source_type': 'Repository',
    'conditions': {'ref_name': {'include': ['~DEFAULT_BRANCH'], 'exclude': []}},
    'rules': [
        {'type': 'deletion'},
        {'type': 'non_fast_forward'},
        {'type': 'pull_request', 'parameters': {
            'allowed_merge_methods': ['squash'], 'dismiss_stale_reviews_on_push': False,
            'require_code_owner_review': False, 'require_last_push_approval': False,
            'required_approving_review_count': 0, 'required_review_thread_resolution': False,
            'required_reviewers': []}},
    ],
}

MATCHING = {
    f'repos/{REPO}': (200, {
        'default_branch': 'main', 'description': 'A demo repo',
        'delete_branch_on_merge': True, 'allow_squash_merge': True,
        'allow_merge_commit': False, 'allow_rebase_merge': False,
        'security_and_analysis': {
            'secret_scanning': {'status': 'enabled'},
            'secret_scanning_push_protection': {'status': 'enabled'},
        },
    }),
    f'repos/{REPO}/actions/permissions/workflow': (200, {
        'default_workflow_permissions': 'read', 'can_approve_pull_request_reviews': False}),
    f'repos/{REPO}/rulesets': (200, [{'id': 7, 'name': 'main-protection'}]),
    f'repos/{REPO}/rulesets/7': (200, MATCHING_RULESET),
}


def run(responses):
    def fetch(path, paginate=False):
        return responses.get(path, (404, {'message': 'Not Found'}))
    return {r['setting']: r for r in check_repo.check(REPO, fetch)}


class CheckRepoTests(unittest.TestCase):
    def setUp(self):
        self.responses = copy.deepcopy(MATCHING)
        self.repo = self.responses[f'repos/{REPO}'][1]
        # A ruleset update writes the file it sends; keep it out of the real temp folder.
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        patcher = mock.patch.object(check_repo.tempfile, 'gettempdir', return_value=folder.name)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_matching_repo_has_nothing_to_fix(self):
        results = run(self.responses)
        self.assertEqual({r['state'] for r in results.values()}, {'ok'})

    def test_differing_repo_field_gets_a_patch_command(self):
        self.repo['allow_merge_commit'] = True
        result = run(self.responses)['allow_merge_commit']
        self.assertEqual(result['state'], 'differs')
        self.assertEqual(result['fix'], f'gh api -X PATCH repos/{REPO} -F allow_merge_commit=false')

    def test_squash_setting_is_fixed_before_the_other_merge_settings(self):
        self.repo.update(allow_squash_merge=False, allow_merge_commit=True, allow_rebase_merge=True)
        settings = [r['setting'] for r in run(self.responses).values() if r['state'] == 'differs']
        self.assertEqual(settings[0], 'allow_squash_merge')

    def test_field_hidden_from_non_admins_is_unavailable(self):
        del self.repo['delete_branch_on_merge']
        self.assertEqual(run(self.responses)['delete_branch_on_merge']['state'], 'unavailable')

    def test_private_repo_without_secret_scanning_is_unavailable(self):
        del self.repo['security_and_analysis']
        result = run(self.responses)['security_and_analysis.secret_scanning']
        self.assertEqual(result['state'], 'unavailable')
        self.assertIsNone(result['fix'])

    def test_disabled_push_protection_gets_a_quoted_patch_command(self):
        self.repo['security_and_analysis']['secret_scanning_push_protection']['status'] = 'disabled'
        result = run(self.responses)['security_and_analysis.secret_scanning_push_protection']
        self.assertEqual(result['fix'], f"gh api -X PATCH repos/{REPO} "
                         "-f 'security_and_analysis[secret_scanning_push_protection][status]=enabled'")

    def test_write_token_gets_a_put_command(self):
        self.responses[f'repos/{REPO}/actions/permissions/workflow'][1]['default_workflow_permissions'] = 'write'
        result = run(self.responses)['actions.default_workflow_permissions']
        self.assertEqual(result['fix'], f'gh api -X PUT repos/{REPO}/actions/permissions/workflow '
                         '-f default_workflow_permissions=read')

    def test_empty_description_asks_for_text(self):
        self.repo['description'] = None
        result = run(self.responses)['description']
        self.assertEqual(result['state'], 'differs')
        self.assertIn('--description', result['fix'])
        self.assertEqual(result['note'], 'needs the text from the user')

    def test_missing_ruleset_is_created(self):
        self.responses[f'repos/{REPO}/rulesets'] = (200, [])
        result = run(self.responses)['ruleset']
        self.assertEqual(result['state'], 'differs')
        self.assertTrue(result['fix'].startswith(f'gh api -X POST repos/{REPO}/rulesets --input '))

    def test_ruleset_with_the_same_name_is_updated_in_place(self):
        self.responses[f'repos/{REPO}/rulesets/7'][1]['rules'][2]['parameters']['allowed_merge_methods'] = [
            'squash', 'merge']
        result = run(self.responses)['ruleset']
        self.assertEqual(result['state'], 'differs')
        self.assertIn('pull_request', result['now'])
        self.assertTrue(result['fix'].startswith(f'gh api -X PUT repos/{REPO}/rulesets/7 --input '))
        sent = json.loads(Path(shlex.split(result['fix'])[-1]).read_text())
        pull_request = next(r for r in sent['rules'] if r['type'] == 'pull_request')
        self.assertEqual(pull_request['parameters']['allowed_merge_methods'], ['squash'])

    def test_update_in_place_keeps_other_rules_and_bypass_actors(self):
        existing = copy.deepcopy(MATCHING_RULESET)
        existing['rules'] = [
            {'type': 'required_status_checks', 'parameters': {'required_status_checks': [{'context': 'test'}]}},
            {'type': 'pull_request', 'parameters': {'required_approving_review_count': 1,
                                                    'required_reviewers': [], 'allowed_merge_methods': ['merge']}},
        ]
        existing['bypass_actors'] = [{'actor_id': 5, 'actor_type': 'RepositoryRole', 'bypass_mode': 'always'}]
        existing['conditions']['ref_name'] = {'include': ['refs/heads/release/*'], 'exclude': ['refs/heads/main']}
        _, wanted, _ = check_repo.load_defaults()
        merged = check_repo.merged_ruleset(existing, wanted, 'main')
        types = [r['type'] for r in merged['rules']]
        self.assertEqual(sorted(types), ['deletion', 'non_fast_forward', 'pull_request', 'required_status_checks'])
        pull_request = next(r for r in merged['rules'] if r['type'] == 'pull_request')
        self.assertEqual(pull_request['parameters']['allowed_merge_methods'], ['squash'])
        self.assertEqual(pull_request['parameters']['required_approving_review_count'], 0)
        self.assertIn('required_reviewers', pull_request['parameters'])
        self.assertEqual(merged['bypass_actors'], existing['bypass_actors'])
        self.assertEqual(merged['conditions']['ref_name'],
                         {'include': ['refs/heads/release/*', '~DEFAULT_BRANCH'], 'exclude': []})
        self.assertTrue(check_repo.covers_default_branch(merged, 'main'))

    def test_update_note_says_what_is_kept(self):
        ruleset = self.responses[f'repos/{REPO}/rulesets/7'][1]
        ruleset['rules'] = [{'type': 'creation'}]
        note = run(self.responses)['ruleset']['note']
        self.assertIn('keeps its 1 other rule(s)', note)

    def test_update_that_loosens_the_ruleset_warns(self):
        params = self.responses[f'repos/{REPO}/rulesets/7'][1]['rules'][2]['parameters']
        params.update(required_approving_review_count=1, require_code_owner_review=True)
        result = run(self.responses)['ruleset']
        self.assertEqual(result['state'], 'differs')
        self.assertEqual(result['loosens'], ['require_code_owner_review true -> false',
                                             'required_approving_review_count 1 -> 0'])
        self.assertIn('WARNING: this lowers protection', result['note'])
        self.assertIn('required_approving_review_count 1 -> 0', check_repo.report(REPO, [result]))

    def test_update_that_only_tightens_does_not_warn(self):
        params = self.responses[f'repos/{REPO}/rulesets/7'][1]['rules'][2]['parameters']
        params['allowed_merge_methods'] = ['squash', 'merge']
        result = run(self.responses)['ruleset']
        self.assertEqual(result['loosens'], [])
        self.assertNotIn('WARNING', result['note'])

    def test_rules_split_across_rulesets_count_together(self):
        ruleset = self.responses[f'repos/{REPO}/rulesets/7'][1]
        other = copy.deepcopy(ruleset)
        other.update(id=8, name='no-force-push', rules=[ruleset['rules'].pop(1)])
        self.responses[f'repos/{REPO}/rulesets'][1].append({'id': 8, 'name': 'no-force-push'})
        self.responses[f'repos/{REPO}/rulesets/8'] = (200, other)
        self.assertEqual(run(self.responses)['ruleset']['state'], 'ok')

    def test_inactive_ruleset_does_not_count(self):
        self.responses[f'repos/{REPO}/rulesets/7'][1]['enforcement'] = 'disabled'
        self.assertEqual(run(self.responses)['ruleset']['state'], 'differs')

    def test_rulesets_on_a_free_private_repo_are_unavailable(self):
        self.responses[f'repos/{REPO}/rulesets'] = (403, {'message': 'Upgrade to GitHub Pro'})
        result = run(self.responses)['ruleset']
        self.assertEqual(result['state'], 'unavailable')
        self.assertIn('HTTP 403', result['note'])

    def test_string_fields_are_quoted_raw_fields(self):
        self.assertEqual(check_repo.field_arg('title', 'two words'), "-f 'title=two words'")
        self.assertEqual(check_repo.field_arg('title', '@file'), '-f title=@file')
        self.assertEqual(check_repo.field_arg('has_wiki', False), '-F has_wiki=false')

    def test_squash_is_fixed_first_whatever_the_order_in_defaults(self):
        defaults, _, _ = check_repo.load_defaults()
        defaults['repo'] = dict(reversed(list(defaults['repo'].items())))
        self.repo.update(allow_squash_merge=False, allow_merge_commit=True)
        results = check_repo.check_repo_fields(REPO, self.repo, defaults)
        self.assertEqual(results[0]['setting'], 'allow_squash_merge')

    def test_hidden_security_settings_say_admin_access_is_missing(self):
        del self.repo['security_and_analysis']
        self.repo['permissions'] = {'admin': False, 'push': True}
        note = run(self.responses)['security_and_analysis.secret_scanning']['note']
        self.assertIn('admin access', note)

    def test_unknown_field_for_an_admin_points_at_defaults(self):
        del self.repo['delete_branch_on_merge']
        self.repo['permissions'] = {'admin': True, 'push': True}
        self.assertIn('defaults.json', run(self.responses)['delete_branch_on_merge']['note'])

    def test_ruleset_that_excludes_the_default_branch_does_not_count(self):
        self.responses[f'repos/{REPO}/rulesets/7'][1]['conditions']['ref_name'] = {
            'include': ['~ALL'], 'exclude': ['refs/heads/main']}
        self.assertEqual(run(self.responses)['ruleset']['state'], 'differs')

    def test_ref_patterns_match_like_github(self):
        match = check_repo.ref_pattern_matches
        self.assertTrue(match('refs/heads/ma*', 'refs/heads/main'))
        self.assertFalse(match('refs/heads/*', 'refs/heads/release/1'))
        self.assertTrue(match('refs/heads/**', 'refs/heads/release/1'))
        self.assertFalse(match('refs/heads/m.in', 'refs/heads/main'))

    def test_rule_parameters_that_list_objects_compare_in_any_order(self):
        checks = [{'context': 'test'}, {'context': 'lint', 'integration_id': 1}]
        want = {'type': 'required_status_checks', 'parameters': {'required_status_checks': checks}}
        have = copy.deepcopy(want)
        have['parameters']['required_status_checks'].reverse()
        self.assertTrue(check_repo.rule_matches(want, have))
        have['parameters']['required_status_checks'].pop()
        self.assertFalse(check_repo.rule_matches(want, have))

    def test_ruleset_listing_is_paginated(self):
        seen = []

        def fetch(path, paginate=False):
            seen.append((path, paginate))
            return MATCHING.get(path, (404, {'message': 'Not Found'}))
        check_repo.check(REPO, fetch)
        self.assertIn((f'repos/{REPO}/rulesets', True), seen)

    def test_paginated_pages_are_joined(self):
        completed = subprocess.CompletedProcess([], 0, stdout='[[{"id": 1}], [{"id": 2}]]', stderr='')
        with mock.patch.object(check_repo.subprocess, 'run', return_value=completed) as run_gh:
            status, body = check_repo.gh_fetch(f'repos/{REPO}/rulesets', paginate=True)
        self.assertEqual((status, body), (200, [{'id': 1}, {'id': 2}]))
        self.assertEqual(run_gh.call_args[0][0][-2:], ['--paginate', '--slurp'])

    def test_paginated_error_body_is_unwrapped(self):
        # What `gh api --paginate --slurp` really prints for a free private repo.
        stdout = ('[{"message":"Upgrade to GitHub Pro or make this repository public to enable this feature.",'
                  '"status":"403"}\n]')
        stderr = 'gh: Upgrade to GitHub Pro or make this repository public to enable this feature. (HTTP 403)\n'
        failed = subprocess.CompletedProcess([], 1, stdout=stdout, stderr=stderr)
        with mock.patch.object(check_repo.subprocess, 'run', return_value=failed):
            status, body = check_repo.gh_fetch(f'repos/{REPO}/rulesets', paginate=True)
        self.assertEqual(status, 403)
        self.assertIn('Upgrade to GitHub Pro', check_repo.message(body))

    def test_message_tolerates_a_list_body(self):
        self.assertEqual(check_repo.message([{'message': 'x'}]), 'no details')

    def test_description_placeholder_is_single_quoted(self):
        self.repo['description'] = ''
        fix = run(self.responses)['description']['fix']
        self.assertTrue(fix.endswith("--description '<one line on what the repo is for>'"))

    def test_unreadable_repo_raises(self):
        with self.assertRaises(RuntimeError):
            run({})

    def test_bad_argument_exits_2(self):
        self.assertEqual(check_repo.main(['not-a-repo']), 2)


if __name__ == '__main__':
    unittest.main()
