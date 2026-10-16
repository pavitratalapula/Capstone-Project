# Agent Evaluation Rubric

Application tests measure the Expense Tracker. They are not evaluations of
agent quality. The rubrics below evaluate whether each agent produces the
required artifact and reasoning evidence.

## Requirements agent

- **Expected output:** Complete `docs/requirements-analysis.md`.
- **Evaluation criteria:** Scope is specific; acceptance criteria are testable; edge cases and out-of-scope items are explicit.
- **Pass:** No requested capability lacks an observable criterion and ambiguity is escalated.
- **Fail:** Requirements are generic, contradictory, or silently assume behavior.
- **Evidence:** `docs/requirements-analysis.md`.

## Design agent

- **Expected output:** `docs/design.md` and a dependency-ordered plan.
- **Evaluation criteria:** Data model, JSON schema, Decimal policy, validation, error handling, responsibilities, and risks are covered.
- **Pass:** A developer can implement without inventing persistence or CLI rules.
- **Fail:** Design omits data-loss/error behavior or introduces unsupported infrastructure.
- **Evidence:** `docs/design.md`, `docs/implementation-plan.md`.

## Development agent

- **Expected output:** Minimal source/test diff implementing approved requirements.
- **Evaluation criteria:** Scope adherence, readable Python, shared validation, persistence safety, and focused tests.
- **Pass:** Relevant tests and full suite pass with exact commands recorded.
- **Fail:** Requirements are changed to fit code, tests are weakened, or failures are hidden.
- **Evidence:** `src/expense_tracker.py`, `tests/test_expense_tracker.py`, and test output referenced by `docs/qa-report.md`.

## QA agent

- **Expected output:** `docs/qa-report.md`.
- **Evaluation criteria:** Acceptance coverage, normal/error scenarios, CLI checks, reproducible commands, defects, and honest gaps.
- **Pass:** Evidence distinguishes passed scenarios from untested limitations.
- **Fail:** QA reports only a green test count or calls application tests agent evaluations.
- **Evidence:** `docs/qa-report.md`.

## Code review agent

- **Expected output:** Read-only severity-ordered findings or an explicit no-findings result.
- **Evaluation criteria:** Findings cite locations, requirements/design rationale, impact, and recommendation.
- **Pass:** High-confidence correctness, security, data-loss, and compatibility risks are addressed.
- **Fail:** Review is generic, stylistic only, or edits code while claiming read-only review.
- **Evidence:** Review result is not preserved as a standalone transcript; the repository must not claim more than the available review record.

## Documentation agent

- **Expected output:** Accurate README and final handoff.
- **Evaluation criteria:** Commands, paths, schema, tests, limitations, agent mapping, and hooks/MCP decisions match the repository.
- **Pass:** A reviewer can reproduce the application and understand the SDLC without fabricated claims.
- **Fail:** Documentation is stale, contradictory, or claims runtime memory/delegation without evidence.
- **Evidence:** `README.md`, `docs/final-handoff.md`, and this rubric.

## Evaluation boundary

These are review rubrics, not automated agent benchmark results. No numeric agent
score is claimed because no separate evaluation harness or recorded agent-output
dataset exists in this repository.
