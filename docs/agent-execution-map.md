# Expense Tracker Agent Execution Map

This document maps the configured custom agent, skill, prompt, artifacts, and
handoff gate for each SDLC stage. It is repository evidence of the intended
workflow and artifact contracts; it is not a fabricated runtime transcript.

## Requirements

- **Agent:** `requirements-agent` — `.github/agents/requirements-agent.md`
- **Skill:** `.github/skills/requirements-analysis/SKILL.md`
- **Prompt:** `.github/prompts/analyze-requirement.prompt.md`
- **Input:** User story, `README.md`, current Expense Tracker source/tests
- **Output artifact:** `docs/requirements-analysis.md`
- **Validation gate:** Every requested capability has testable acceptance criteria and explicit edge-case/error policy.
- **Handoff to next stage:** Design-agent reads the approved requirements artifact.

## Design

- **Agent:** `design-agent` — `.github/agents/design-agent.md`
- **Skill:** `.github/skills/software-design/SKILL.md`
- **Prompt:** `.github/prompts/design-review.prompt.md`
- **Input:** `docs/requirements-analysis.md`, source, tests, repository instructions
- **Output artifact:** `docs/design.md`
- **Validation gate:** Model, JSON schema, Decimal policy, category normalization, missing-file behavior, and failure safety are explicit.
- **Handoff to next stage:** Implementation-plan prompt produces the dependency-ordered plan for development-agent.

## Implementation planning

- **Agent:** `design-agent` — `.github/agents/design-agent.md`
- **Skill:** `.github/skills/software-design/SKILL.md`
- **Prompt:** `.github/prompts/implementation-plan.prompt.md`
- **Input:** `docs/requirements-analysis.md` and `docs/design.md`
- **Output artifact:** `docs/implementation-plan.md`
- **Validation gate:** Each acceptance criterion maps to an implementation task and a test/verification gate.
- **Handoff to next stage:** Development-agent uses the approved plan without changing requirements to fit code.

## Development

- **Agent:** `development-agent` — `.github/agents/development-agent.md`
- **Skill:** `.github/skills/python-development/SKILL.md` and `.github/skills/testing/SKILL.md`
- **Prompt:** `.github/prompts/implement-feature.prompt.md`
- **Input:** Requirements, design, implementation plan, repository instructions
- **Output artifact:** `src/expense_tracker.py` and `tests/test_expense_tracker.py`
- **Validation gate:** Focused tests and full pytest suite pass; persistence and Decimal acceptance criteria are verified.
- **Handoff to next stage:** QA-agent receives the implementation and test output.

## QA

- **Agent:** `qa-agent` — `.github/agents/qa-agent.md`
- **Skill:** `.github/skills/testing/SKILL.md`
- **Prompt:** `.github/prompts/verify-release.prompt.md`
- **Input:** Requirements, design, implementation, tests, and development evidence
- **Output artifact:** `docs/qa-report.md`
- **Validation gate:** Focused/full test results, CLI smoke checks, acceptance coverage, defects, and remaining gaps are recorded.
- **Handoff to next stage:** Code-review-agent reviews the implementation with QA evidence.

## Code review

- **Agent:** `code-review-agent` — `.github/agents/code-review-agent.md`
- **Skill:** `.github/skills/code-review/SKILL.md`
- **Prompt:** `.github/prompts/review-release.prompt.md`
- **Input:** Current diff, requirements, design, QA report, source, and tests
- **Output artifact:** Review findings and dispositions; the repository preserves the resulting QA/design evidence rather than a separate review transcript.
- **Validation gate:** Findings are severity/location based, tied to requirements, and high-confidence defects are resolved or explicitly accepted.
- **Handoff to next stage:** Documentation-agent receives the reviewed implementation and evidence.

## Documentation

- **Agent:** `documentation-agent` — `.github/agents/documentation-agent.md`
- **Skill:** `.github/skills/documentation/SKILL.md`
- **Prompt:** `.github/prompts/pr-description.prompt.md`
- **Input:** Final source/tests, all SDLC artifacts, customization files, and validation output
- **Output artifact:** `README.md`, `docs/final-handoff.md`, and the evidence documents in this directory
- **Validation gate:** Commands, paths, agent claims, limitations, and hooks/MCP decisions match the repository.
- **Handoff:** Reviewer-ready capstone documentation; no application changes are implied by this stage.

## QA re-check

- **Agent:** `qa-agent` — `.github/agents/qa-agent.md`
- **Skill:** `.github/skills/testing/SKILL.md`
- **Prompt:** No separate re-check prompt was recorded; this was a follow-up
  validation request against `docs/code-review.md`.
- **Input:** Code Review findings, updated source/tests, requirements, design,
  and prior QA evidence
- **Output artifact:** Updated `docs/qa-report.md`
- **Validation gate:** Confirm both review fixes, run targeted/full tests, and
  run Python compilation.
- **Result:** Both findings verified; 37 focused tests and 39 full-suite tests
  passed; compilation passed.
- **Handoff:** Documentation-agent updates release-facing documentation without
  modifying application source or tests.

## Evidence boundary

The repository stores configuration and artifacts, not Copilot chat transcripts.
Therefore this map must not be presented as proof that every prompt was invoked
at runtime; it is the auditable agent/skill/prompt contract for reproducing the
workflow.
