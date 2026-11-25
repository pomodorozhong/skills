"""Fixture tests for skills/applying-github-repo-defaults/scripts/check_repo.py.

Each test feeds stored API responses to the check instead of calling GitHub,
so nothing touches the network. Run from the repo root:
python3 -m unittest discover tests
"""
import copy
import importlib.util
import subprocess
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

    def test_unreadable_repo_raises(self):
        with self.assertRaises(RuntimeError):
            run({})

    def test_bad_argument_exits_2(self):
        self.assertEqual(check_repo.main(['not-a-repo']), 2)


if __name__ == '__main__':
    unittest.main()
