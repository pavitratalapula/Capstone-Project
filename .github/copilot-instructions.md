# Copilot Instructions: Expense Tracker Capstone

## Project purpose

This repository demonstrates an Agentic SDLC around a small Python 3.11+ Expense Tracker. The older Documentation Sync utility remains as a separate regression-tested example.

## Architecture

- `src/expense_tracker.py` contains the `Expense` model, validation, JSON repository functions, tracker service, formatting, and CLI.
- `tests/test_expense_tracker.py` covers persistence, filtering, totals, validation, malformed data, and CLI behavior.
- `data/expenses.json` is the default local ledger path, created on first successful save.
- `docs/requirements-analysis.md`, `docs/design.md`, `docs/implementation-plan.md`, `docs/qa-report.md`, and `docs/final-handoff.md` are Expense Tracker evidence.
- `src/documentation_sync.py`, `tests/test_documentation_sync.py`, `demo_repo/`, and the root `requirements.md`/`architecture.md` records remain a separate legacy utility scope.

Keep Expense Tracker domain validation, JSON persistence, service orchestration, formatting, and CLI parsing separable. Use local JSON only; do not introduce a database, web framework, remote API, or third-party dependency without an approved requirement.

## Coding standards

- Use Python 3.11+ type hints, `pathlib`, dataclasses, and standard-library modules.
- Use `Decimal`, never binary floating point, for monetary values; serialize amounts as JSON strings.
- Normalize expense categories against `Food`, `Travel`, `Shopping`, `Bills`, and `Other`.
- Treat a missing ledger as empty, but surface malformed JSON, invalid records, and filesystem errors.
- Keep functions small and names explicit. Add comments only for non-obvious decisions.
- Preserve the Expense Tracker CLI contract: `--data PATH` before `add`, `list`, or `total`.

## Testing standards

- Add focused pytest tests for every behavior change.
- Cover add/list/total/filter, JSON round-trip, insertion order, invalid values, malformed data, failed writes, and CLI exit behavior.
- Run targeted tests first, then the full `pytest` suite before handoff.
- Do not weaken assertions or skip failures to make a change pass.

## SDLC rules for Copilot

1. Start by inspecting the repository and the applicable Expense Tracker artifact.
2. Move through requirements, design, planning, development, QA, code review, and documentation in that order.
3. Before significant edits, state the files and rationale; do not blindly modify files.
4. Use the matching custom agent, skill, and prompt; record the mapping in `docs/agent-execution-map.md`.
5. Treat the approved Expense Tracker requirements and design as the implementation boundary.
6. Leave stage evidence and report exact validation commands/results.
7. Distinguish application tests from agent-output evaluations.
8. Do not claim runtime subagent delegation, Copilot memory, hooks, or MCP usage unless evidence exists.

## Customization relationships

- These instructions are always-on repository guidance.
- Agents are role-specific workflows with tools, handoffs, and gates.
- Skills are reusable procedures loaded by relevant agents.
- Prompts are manually invoked task templates that provide role, context, constraints, and output structure.
