# Expense Tracker Design

## Scope and principles

The Expense Tracker is a small, local ledger. It has no service, database, network
dependency, or third-party runtime dependency. The existing
`src/expense_tracker.py` and `tests/test_expense_tracker.py` implement the
approved requirements recorded in this document and
`docs/requirements-analysis.md`. New changes must continue to follow those
contracts.

The design favors explicit validation, deterministic JSON, insertion-order
preservation, and pure calculation/filtering logic where practical.

## Proposed design

Extend the existing single-module application with stable expense identity and
one replacement-style edit operation. Keep the current validation helpers,
JSON repository functions, `ExpenseTracker` service, and `argparse` CLI
boundaries. An edit loads the complete ordered ledger, resolves one ID, builds
and validates a complete replacement `Expense`, replaces the matching list
element at the same index, and saves the complete ledger using the existing
atomic-ish write path.

The design deliberately avoids a database, a separate migration command,
global state, or a second repository. It supports partial updates through an
internal omitted-value sentinel while preserving the existing add/list/total
contracts.

## Existing code areas affected

- `Expense` and its validation in `src/expense_tracker.py`: add stable identity
  while preserving the existing positional description/amount/category order.
- `_expense_from_record`, `load_expenses`, and `save_expenses`: read/write the
  four-field schema, validate IDs, and support the approved legacy rule.
- `ExpenseTracker`: add `edit_expense` while leaving add, list, total, and filter
  semantics intact.
- `build_parser`, `main`, and `_format_expense`: add the `edit` command and
  make IDs visible to users.
- `tests/test_expense_tracker.py`: add focused edit, migration, validation,
  persistence-safety, CLI, and regression coverage.
- `docs/implementation-plan.md`: record dependency-ordered development tasks
  after this design is approved.

## Architecture and data flow

The application consists of five small responsibilities:

1. **Domain model and validation** — `Expense` is an immutable record containing
   a stable ID, a `Decimal` amount, canonical category, and trimmed non-empty
   description.
   Validation and category normalization are centralized so API and CLI behavior
   cannot diverge.
2. **Ledger service** — `ExpenseTracker` owns the ordered collection and exposes
   add, list, total, and category-filter operations. An add validates first,
   appends only after validation, and persists the complete resulting ledger.
3. **JSON repository** — loads and validates the JSON file and serializes
   `Decimal` values as strings. It treats a missing file as an empty ledger and
   raises a clear domain/storage error for malformed or structurally invalid
   data.
4. **CLI adapter** — parses commands and options, constructs a tracker with the
   selected path, formats results, and converts expected failures into concise
   user-facing errors and a non-zero exit status.
5. **Formatting helpers** — provide stable text/JSON-independent display of
   amounts and lists. They do not own persistence or business rules.

Typical flow:

`CLI/API -> tracker -> repository.load -> validate/operate -> repository.save`

Listing and totals load the current file before operating, so a new tracker
instance sees data from earlier invocations. A failed validation or save does not
replace the existing valid file.

## Data model

### Expense

| Field | Type in Python | JSON type | Rules |
|---|---|---|---|
| `id` | `str` | string | stable, unique, immutable UUID |
| `amount` | `Decimal` | string | finite and strictly greater than zero |
| `category` | `str` | string | one canonical supported category |
| `description` | `str` | string | surrounding whitespace removed; must not be empty |

The supported categories are exactly `Food`, `Travel`, `Shopping`, `Bills`, and
`Other`. Category input is trimmed and matched case-insensitively (using
`casefold`), then stored and displayed using the canonical spelling. The same
policy applies to adding and filtering. There is no implicit category beyond the
documented default: omitted add-category input means `Other`.

Descriptions may contain Unicode and internal whitespace, including newlines;
no arbitrary length limit is introduced in this small local tool. Amount input
is converted with `Decimal`, rejects non-numeric, non-finite, zero, and negative
values, and is not converted through `float`. The accepted decimal scale is the
scale representable by `Decimal`; no currency rounding is silently imposed.

## Persistence format

The default path is `data/expenses.json`, relative to the process working
directory. Both the API constructor and CLI accept an explicit data path.
Parent directories are created when saving if possible.

The file is UTF-8 JSON with a top-level array, in insertion order:

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

Amounts are strings deliberately: JSON has no Decimal type, and this avoids
binary floating-point loss while preserving the entered Decimal value. Records must contain the four required fields with the documented types. Unknown
extra fields, missing fields, non-array roots, invalid Decimal strings, invalid
expense values, and duplicate IDs are rejected clearly rather than guessed or
discarded. Duplicate expense content is permitted when each record has a
different ID.

Missing storage means an empty ledger. An existing empty file is invalid JSON and
is reported as malformed rather than silently replaced. Reads use UTF-8 and
writes use deterministic JSON (stable field order, consistent indentation, and a
trailing newline).

Saving should be atomic-ish: write the complete document to a uniquely named
temporary file in the data file's directory, flush/close it, then replace the
destination with `os.replace`. Cleanup is attempted after failures. This reduces
the chance of truncating valid data, though it cannot guarantee durability across
power loss or protect against concurrent writers.

## Module responsibilities

The implementation may remain a small module, but these logical boundaries
should be visible and independently testable:

- `Expense`, category constants, normalization, and validation.
- `load_expenses(path)` / `save_expenses(path, expenses)` repository functions.
- `ExpenseTracker(data_path=...)` orchestration and ordered operations.
- `parse_amount` and CLI parser/`main` adapter.
- Output formatting that consistently renders Decimal values as strings (or a
  deliberate fixed display format) without changing stored precision.

Standard-library choices are `dataclasses`, `decimal.Decimal`, `json`,
`pathlib.Path`, `argparse`, and `tempfile`/`os.replace`. No dependency injection
framework, ORM, schema package, or network client is needed.

## CLI and Python API

The CLI uses a global data option followed by one required operation:

```text
python -m src.expense_tracker [--data PATH] add DESCRIPTION AMOUNT [--category CATEGORY]
python -m src.expense_tracker [--data PATH] list [--category CATEGORY]
python -m src.expense_tracker [--data PATH] total [--category CATEGORY]
python -m src.expense_tracker [--data PATH] edit ID [--description DESCRIPTION] [--amount AMOUNT] [--category CATEGORY]
```

`--data` defaults to `data/expenses.json`; an explicit path is used exactly as
provided (relative paths are relative to the working directory). `add` reports
the saved expense and generates its ID. `list` prints matching expenses
including their IDs in insertion order and a total, including an empty result
with zero. `total` prints only the selected total. `edit` requires at least one
edit option, reports the updated expense, and preserves its ID and position.
Unsupported categories, invalid amounts, missing edit fields, and unknown IDs
are parser/user errors.
Malformed JSON and filesystem failures are reported to stderr with the path and
an actionable message; commands return non-zero and never overwrite the source
as a consequence of the error.

The Python API is equivalent:

```python
tracker = ExpenseTracker(data_path="data/expenses.json")
tracker.add_expense("Coffee", Decimal("4.50"), "Other")
tracker.list_expenses(category="Other")
tracker.total(category="Other")
tracker.edit_expense("2f4f8a3f-7b8c-4f5e-9f7d-0e4c2a1b6d90", description="Latte")
```

The constructor/path contract is explicit so tests can use isolated temporary
files and callers can select a ledger without changing process-global state.

## Decisions, risks, and mitigations

- **Decimal strings** preserve monetary precision; avoiding float is mandatory.
  No currency code is stored because currency conversion and multi-currency
  support are out of scope.
- **Canonical, case-insensitive categories** are convenient for users while
  keeping persisted data stable.
- **Missing file is empty; malformed file is fatal** distinguishes first use
  from data corruption and prevents silent loss.
- **Atomic-ish replacement** protects the old file during normal write failures.
  Concurrent writers and power-loss durability remain out of scope; document
  single-user use and consider file locking if that scope changes.
- **No automatic backup or recovery** keeps the implementation small. Users can
  back up the documented JSON file before manual changes.
- **Parent-directory creation** makes the default path usable, while permission
  errors remain visible rather than swallowed.
- **Unbounded descriptions** avoid an arbitrary product constraint, but very
  large input can produce large files; a future requirement may add a limit.

## Feature design: edit an existing expense by ID

This section resolves the design questions in the edit feature requirements.
These are technical decisions for implementation, not a replacement for the
approved behavior and acceptance criteria in
`docs/requirements-analysis.md`.

### ID representation and generation

- `Expense.id` is an immutable UUID string in canonical hyphenated form.
- New expenses receive `str(uuid.uuid4())` inside the domain model. API callers
  do not supply IDs when adding an expense.
- The ID is not editable and is never reused.
- UUID generation uses only the Python standard library and does not require a
  counter file or a second persistence store.

### JSON persistence and legacy migration

- New records are serialized with exactly `id`, `amount`, `category`, and
  `description`, in that field order.
- Existing three-field records are accepted as legacy input. They are assigned
  deterministic UUID5 migration IDs derived from a fixed application namespace,
  the record's original index, and its canonical three-field content. The index
  makes duplicate legacy records distinct while preserving their order.
- Legacy records are not discarded or rewritten during read-only `list`,
  `total`, or filter operations. Their derived IDs are shown in memory.
- The first successful write involving a legacy ledger (add or edit) persists
  the complete upgraded four-field schema atomically. The derived IDs then
  become permanent.
- A legacy record with malformed fields remains a data error. Duplicate
  persisted IDs, missing IDs in an otherwise new-format record, or mixed
  records with conflicting IDs are also data errors.
- No separate migration command or backup file is introduced. The existing
  atomic-ish temporary-file replacement protects the original file if migration
  or editing fails.

### Service/API edit interface

`ExpenseTracker.edit_expense(expense_id, *, description=UNSET,
amount=UNSET, category=UNSET) -> Expense` loads the ledger, resolves exactly
one ID, applies only supplied fields, validates the complete resulting
`Expense`, replaces the item at its existing list index, saves the full ledger,
and returns the updated immutable record.

An internal sentinel distinguishes an omitted field from an explicitly supplied
invalid value. `None` is not treated as "use the default" for edits. At least
one field must be supplied. Existing `add_expense`, `list_expenses`, and
`total` call signatures remain compatible; `Expense` keeps its existing
description/amount/category positional order, with `id` added as a generated
defaulted field.

### CLI interface

The global `--data PATH` option remains before the subcommand:

```text
python -m src.expense_tracker --data PATH edit ID \
  [--description DESCRIPTION] [--amount AMOUNT] [--category CATEGORY]
```

`argparse` validates the amount using the existing Decimal-only parser.
Description, category, and ID validation occurs in the domain/service layer so
API and CLI behavior remain consistent. The parser requires at least one edit
option; values are not silently ignored. List output includes the ID so a user
can copy it into the edit command.

### Validation and error behavior

- An unknown or malformed ID raises a dedicated not-found/validation error
  (`ExpenseNotFoundError`, derived from `ValueError`) and the CLI returns 1.
- Duplicate IDs or invalid legacy/new record shapes raise `ExpenseDataError`.
- Amount, category, and description updates reuse `parse_decimal`,
  `normalize_category`, and `validate_description`.
- Validation occurs before any save. A failed validation leaves both the
  in-memory loaded list and source file unchanged.
- A failed `os.replace` leaves the original ledger unchanged under the existing
  atomic-ish write behavior and is reported as `ExpenseStorageError`.
- Malformed JSON, invalid UTF-8, and other read failures retain existing error
  handling and never trigger migration writes.

### Compatibility and output impact

- Add/list/total/filter semantics remain unchanged except that new and migrated
  list output now includes the stable ID.
- Existing callers that construct `Expense(description, amount, category)` and
  call `add_expense` continue to work; IDs are generated automatically.
- Existing three-field JSON remains readable. It is upgraded only on a
  successful write, preserving the original file if that write fails.
- Totals and category filters operate on the edited values without changing
  their public meaning.
- Concurrent writers, cross-process locking, and power-loss durability remain
  out of scope.

### Test and implementation impact

Development must add focused tests for:

1. UUID generation, JSON round-trip, uniqueness, and immutable IDs.
2. Legacy three-field loading, deterministic displayed IDs, and first-write
   migration without data loss.
3. Successful description-only, amount-only, category-only, and multi-field
   edits while preserving order.
4. Totals/filter results after edits and after a fresh tracker reload.
5. Missing, malformed, duplicate, and unknown IDs.
6. No-field, blank, invalid amount, unsupported category, and unknown option
   validation.
7. Failed replacement preserving the original file.
8. CLI edit success, list ID output, and non-zero error behavior.

The Development Agent must update `src/expense_tracker.py` and
`tests/test_expense_tracker.py` only after this design is accepted, then update
the implementation plan with the ordered work and run targeted plus full tests.

## Design-stage handoff

- **Agent:** design-agent
- **Skill:** `.github/skills/software-design/SKILL.md`
- **Instructions followed:** `.github/copilot-instructions.md`
- **Requirements input:** The edit-by-ID section of
  `docs/requirements-analysis.md`, plus the current source and tests
- **Design artifact:** Updated `docs/design.md`
- **Key decisions:** UUID4 for new IDs, deterministic UUID5 migration IDs for
  legacy records, lazy migration on first successful write, immutable IDs,
  partial keyword-only API edits, `edit` CLI subcommand, IDs shown by `list`,
  duplicate IDs treated as data errors, and atomic-ish failure safety
- **Validation performed:** Checked that all ten requested design areas and
  test impact are explicitly covered; no application source or test files were
  modified
- **Handoff to Development Agent:** Implement this design, update
  `docs/implementation-plan.md` with dependency-ordered tasks, add the listed
  regression and feature tests, preserve existing commands, and report exact
  targeted and full-suite results
