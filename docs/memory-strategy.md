# Project Knowledge and Memory Strategy

This project does not claim to use a Copilot memory feature. The repository
artifacts below are durable project knowledge that a future agent or reviewer
can read; they are ordinary versioned files, not hidden model memory.

## Task context

Task context is the current user request, active conversation, current diff,
test output, and files explicitly supplied to an agent. It is temporary and
should not be treated as a durable decision unless recorded in an artifact.

## Project knowledge

Stable usage and scope knowledge is kept in `README.md`, including CLI commands,
the default data path, categories, JSON shape, and limitations.

## Architectural decisions

`docs/design.md` records the Expense model, Decimal-as-string JSON, category
normalization, missing-file policy, atomic-ish replacement, module boundaries,
and rejected complexity. These decisions are separate from requirements.

## SDLC artifacts

- `docs/requirements-analysis.md` — user story, requirements, acceptance criteria, and edge cases
- `docs/implementation-plan.md` — dependency order and validation plan
- `docs/qa-report.md` — test and CLI evidence plus known gaps
- `docs/agent-execution-map.md` — configured agent/skill/prompt handoffs
- `docs/agent-evaluation.md` — evaluation rubrics for agent outputs
- `docs/delegation-evidence.md` — honest boundary around runtime delegation evidence
- `docs/final-handoff.md` — reviewer-oriented summary

These files provide persistence of project knowledge across sessions and
contributors. They do not prove that a particular Copilot model remembered a
previous conversation.
