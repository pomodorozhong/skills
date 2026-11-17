# Handoff

## In progress

### fix/import-review

- Task: #11 Clarify import review wording
- PR: none yet
- Code checkpoint: 1a2b3c4
- State: wording changed; regression test still needed
- Verification: `npm test -- import-review` passed; integration tests not run
- Next action: add a regression test for an unchanged import
- Avoid: changing the label alone missed the empty-result case
- Pending: **P-02** push this branch and open a PR closing #11. Why: pushing needs approval. Blocks: review of #11.

## Ranked work

1. #11 Finish the regression test and review
2. #8 Decide the redesign direction (blocks #9–#15)
3. #1 First run on the real data folder

## Pending

- **P-01** File issue: "Show skipped rows after import". Labels: `enhancement`. Body: …
  Why: filing issues needs approval. Blocks: nothing else.
