# Capstone Project

This repository contains two separate local, standard-library Python utilities:

1. **Expense Tracker** — the primary Agentic SDLC capstone application.
2. **Documentation Sync** — an older regression-tested example retained separately.

## Expense Tracker

The Expense Tracker adds, edits, lists, totals, filters, and persists expenses.
Each expense has an immutable UUID. Supported categories are `Food`, `Travel`,
`Shopping`, `Bills`, and `Other`. Category input is trimmed and case-insensitive.
Amounts use `Decimal`; JSON stores them as strings to preserve precision.

```bash
python -m src.expense_tracker add "Coffee" 4.50 --category Food
python -m src.expense_tracker list --category food
python -m src.expense_tracker total
```

Use `--data PATH` before the command to select a ledger. The default is
`data/expenses.json`. Missing storage is an empty ledger; malformed JSON,
invalid records, unsupported categories, blank descriptions, and invalid amounts
produce clear errors and non-zero CLI status.

List output includes each expense ID. Edit an expense with one or more fields:

```bash
python -m src.expense_tracker --data data/expenses.json edit EXPENSE_ID --description "Updated description"
python -m src.expense_tracker --data data/expenses.json edit EXPENSE_ID --amount 12.50 --category Travel
```

The CLI rejects an edit without `--description`, `--amount`, or `--category`.
Legacy three-field JSON records are readable and receive deterministic UUID5 IDs;
the first successful write migrates the complete ledger to the four-field schema.

```json
[
  {
    "id": "2f4f8a3f-7b8c-4f5e-9f7d-0e4c2a1b6d90",
    "amount": "4.50",
    "category": "Food",
    "description": "Groceries"
  }
]
```

## Agentic SDLC evidence

The Expense Tracker workflow is documented in:

- `docs/requirements-analysis.md`
- `docs/design.md`
- `docs/implementation-plan.md`
- `docs/qa-report.md`
- `docs/agent-execution-map.md`
- `docs/memory-strategy.md`
- `docs/agent-evaluation.md`
- `docs/delegation-evidence.md`
- `docs/final-handoff.md`

The `.github` directory contains project instructions, six custom agents, six
skills, and reusable prompts. Instructions are always-on guidance; agents define
roles and handoffs; skills define repeatable procedures; prompts are manually
invoked templates with context and constraints.

## Tests

Install the test-only dependency if needed:

```bash
python -m pip install "pytest>=8"
```

Run the complete suite:

```bash
python -m pytest -q
```

Latest local validation: 45 Expense Tracker tests, 11 Documentation Sync tests,
and 56 tests total passed; Python compilation, module imports, and the Expense
Tracker CLI smoke test passed.

Application tests are runtime tests, not agent evaluations; agent-output rubrics are in
`docs/agent-evaluation.md`.

## Legacy Documentation Sync utility

This separate utility scans a local repository and writes a Markdown report:

```bash
python src/documentation_sync.py --repo demo_repo --output docs/demo_sync_report.md
```

Hooks and MCP were evaluated and intentionally excluded because this local
application has no genuine lifecycle automation or external-system requirement.
