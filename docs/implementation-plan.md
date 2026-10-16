# Expense Tracker Implementation Plan

This plan is for the approved local Expense Tracker design. It deliberately
does not include changes to the unrelated documentation-sync feature.

## Dependency-ordered tasks

### 1. Establish the domain contract

- Define the canonical category tuple: `Food`, `Travel`, `Shopping`, `Bills`,
  `Other`.
- Define the `Expense` record and centralized description, amount, and category
  validation.
- Implement case-insensitive, trimmed category normalization and the `Other`
  default.

**Depends on:** none.

### 2. Implement JSON serialization and loading

- Serialize each Decimal amount as a string in a top-level JSON array.
- Implement UTF-8 loading for the default or supplied path.
- Treat a missing file as an empty ledger.
- Validate root type, required fields, field types, Decimal finiteness/value,
  categories, and descriptions; expose clear errors without coercion.

**Depends on:** domain contract.

### 3. Implement safe persistence

- Create missing parent directories as needed.
- Produce deterministic JSON with stable formatting.
- Write a temporary file beside the destination, flush/close it, and replace
  with `os.replace`.
- Clean up temporary files after failures and preserve the previous destination
  whenever replacement has not succeeded.

**Depends on:** JSON serialization.

### 4. Implement the tracker service

- Accept `data_path`, defaulting to `data/expenses.json`.
- Load persisted data for operations.
- Add only validated expenses, then save the complete ordered ledger.
- Implement insertion-order listing and Decimal totals, with validated optional
  category filtering.

**Depends on:** domain contract, loading, and persistence.

### 5. Implement the CLI adapter

- Add `--data` with the documented default and `add`, `list`, and `total`
  subcommands.
- Parse amount text directly to Decimal and reject invalid/non-finite/non-positive
  values.
- Format records and totals without converting to float.
- Return a success status for valid operations and concise stderr/non-zero
  results for validation, malformed JSON, and filesystem failures.

**Depends on:** tracker service.

### 6. Add isolated unit and integration coverage

- Test category normalization/defaults and all invalid input classes.
- Test add/list/total/filter behavior and insertion order.
- Test Decimal string round-trip, including precision beyond binary float.
- Test missing file, malformed JSON, wrong root/fields, and unknown categories.
- Test failed writes leave an existing file unchanged.
- Test separate tracker instances using the same temporary path.
- Test CLI parser/exit behavior and explicit/default data paths.

**Depends on:** CLI and tracker service.

### 7. Documentation and handoff

- Keep `docs/design.md` synchronized with any accepted contract changes.
- Add usage and data-location notes to the user-facing documentation if the
  implementation changes the project entry point.
- Record test command and representative CLI verification in the final review.

**Depends on:** implementation and validation.

## Validation plan

1. Run the focused Expense Tracker test suite with `pytest`.
2. Run the complete repository test suite to ensure the documentation-sync
   behavior remains unaffected.
3. Use a temporary data path to execute `add` in one process and `list`/`total`
   in another; verify insertion order and exact Decimal values.
4. Exercise an absent path and confirm it behaves as an empty ledger, then
   exercise malformed and structurally invalid JSON and confirm a clear
   non-zero error with unchanged file bytes.
5. Force a persistence failure (for example, an unwritable destination or
   replacement failure in an isolated test seam) and verify the prior valid
   file remains unchanged and no partial destination is exposed.
6. Compare repeated saves of unchanged data to confirm deterministic UTF-8 JSON.
7. Manually verify category matching for mixed case and surrounding whitespace,
   unsupported categories, zero/negative/non-finite amounts, blank
   descriptions, Unicode, and newline-containing descriptions.

## Completion criteria

The work is complete when all requirements and acceptance cases are covered,
the CLI/API use the same validation rules, persistence round-trips Decimal
amounts as strings, and all focused and full-suite checks pass without changing
the existing documentation-sync contract.

## Edit-by-ID implementation record

The approved design was implemented without changing the legacy
Documentation Sync utility:

- Added immutable UUID4 IDs to new `Expense` instances and persisted IDs in the
  four-field JSON record schema.
- Added deterministic UUID5 IDs for legacy three-field records and lazy schema
  migration on the first successful write.
- Added duplicate-ID validation and `ExpenseNotFoundError` handling.
- Added `ExpenseTracker.edit_expense` with partial keyword-only updates,
  validation reuse, insertion-order preservation, and atomic-ish persistence.
- Added the `edit` CLI subcommand and included IDs in list/add/edit output.
- Added focused regression tests for IDs, migration, edits, validation,
  persistence failures, totals, filtering, and CLI behavior.

**Implementation validation:** `35 passed` in
`tests/test_expense_tracker.py`. Full-suite and syntax-validation results are
recorded by the Development Agent handoff after execution.

## Latest repository verification

The following are fresh verification results for the current workspace, not
the historical implementation-stage counts above:

- Expense Tracker suite: **45 passed**
- Documentation Sync suite: **11 passed**
- Complete suite: **56 passed**
- Python compilation and both module imports: passed
- Expense Tracker add/edit/list/total CLI smoke test: passed using an isolated
  temporary JSON ledger

The Documentation Sync CLI processed a temporary fixture of 300 small Python
files in **0.241 seconds** on this machine, including Python startup; the
fixture and generated report were removed after the measurement. This is one
local sample, not a performance guarantee across machines or repository
shapes. Output error handling, hidden-directory pruning, deterministic reruns,
output self-exclusion, and safe protection of existing repository files are
covered by `tests/test_documentation_sync.py`.
