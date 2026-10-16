# Expense Tracker Requirements Analysis

## Scope and repository finding

The requested feature is a local Expense Tracker: add expenses with amount,
category, and description; list them; calculate totals; filter by category;
persist data in JSON; and cover the behavior with unit tests.

`src/expense_tracker.py` and `tests/test_expense_tracker.py` are the current
Expense Tracker implementation and regression suite. They are reviewed against
the requirements below; implementation behavior does not substitute for
approved product requirements.

## Problem statement

People need a simple local ledger that survives program runs and makes
category-level spending visible. A non-persistent or unfilterable ledger
forces users to reconstruct spending manually and makes totals unreliable.

## User story

As a person tracking personal spending, I want to add an expense with an
amount, category, and description, list saved expenses, filter by category,
and see totals, so that I can understand my spending without a remote
service.

## Functional requirements

1. Add an expense with a positive monetary amount, supported category, and
   non-empty description.
2. List all saved expenses in insertion order.
3. Calculate the total for all expenses.
4. Filter expenses by category and calculate that category's total.
5. Persist expenses locally in UTF-8 JSON and reload them in a later
   invocation.
6. Store at least `amount`, `category`, and `description` in every JSON
   record. Amount serialization must preserve the supported monetary
   precision.
7. Expose a documented user-facing command/API contract for add, list, and
   category filtering.
8. Reject invalid input and report malformed JSON or storage failures clearly;
   never silently replace valid data after a failed operation.
9. Define and apply one consistent category normalization policy. The
   supported category set is `Food`, `Travel`, `Shopping`, `Bills`, and
   `Other`; matching trims surrounding whitespace and ignores case.

## Non-functional requirements

- Use local filesystem storage and no network service.
- Use deterministic JSON output and stable listing order.
- Keep valid data unchanged when validation or persistence fails.
- Make storage location and data format discoverable to users.
- Add isolated unit tests for behavior and persistence across tracker
  instances/processes.

## Acceptance criteria

- A valid add operation reports success and creates/updates the local JSON
  ledger with the three required fields.
- A fresh tracker instance can load the ledger and list the same records in
  insertion order.
- The unfiltered total is the sum of all amounts; a category-filtered total
  includes only matching records.
- A category with no records returns an empty list and zero total.
- Zero, negative, non-numeric, or non-finite amounts are rejected clearly.
- Blank descriptions and unsupported categories are rejected clearly.
- Missing storage is handled according to the selected empty-ledger contract;
  malformed JSON is an error and does not overwrite the source file.
- Unit tests cover add, list, total, filtering, validation, JSON round-trip,
  and persistence failures.

## Edge cases requiring explicit handling

- Missing, empty, malformed, or structurally invalid JSON.
- Missing fields, wrong field types, duplicate records, or extra fields.
- Decimal precision and currency representation.
- Category case/whitespace, exact category set, and default category policy.
- Unicode, newlines, and maximum description length.
- Missing parent directory, read-only files, interrupted writes, and
  concurrent writers.

## Out of scope for the original baseline

- Cloud/database sync, accounts, authentication, or multi-device use.
- Budgets, recurring expenses, income, refunds, or deletion.
- Charts, date-range reports, currency conversion, taxes, and receipt
  attachment.
- Import/export formats other than the defined local JSON format.
- Encryption, secret management, or financial advice.
- New features not approved in the current requirements and design artifacts.

## Baseline decisions

The baseline contract uses `Food`, `Travel`, `Shopping`, `Bills`, and `Other`;
Decimal values are stored as JSON strings without implicit currency rounding;
the default ledger is `data/expenses.json`; both CLI and Python API usage are
supported; a missing ledger is empty; malformed JSON and storage errors are
reported without replacing existing data. Concurrent-writer coordination and
power-loss durability are not guaranteed.

---

# Feature Requirements: Edit an Existing Expense by ID

## Feature status and scope change

This is a feature request for the existing Expense Tracker. Editing is now in
scope; deletion, budgets, recurring expenses, income, refunds, and remote
synchronization remain out of scope.

This artifact defines the required user-visible behavior. The Design Agent must
confirm the ID representation, persistence schema, compatibility/migration
policy, and exact API/CLI syntax before implementation. Requirements analysis
does not authorize application source or test changes.

## User story

As an Expense Tracker user, I want to edit an existing expense by its ID so
that I can correct an amount, category, or description without deleting and
re-adding the record.

## Functional requirements

1. Every persisted expense shall have a stable, unique ID that can be supplied
   to an edit operation.
2. A user shall be able to edit an existing expense by ID through the supported
   Python API and documented CLI.
3. An edit shall update one or more of amount, category, and description.
4. Omitted editable fields shall retain their existing values.
5. The edited expense shall retain its original ID and insertion-order position.
6. A successful edit shall replace the matching record in the same local JSON
   ledger using the existing UTF-8 and Decimal-as-string conventions.
7. Listing, totals, category filtering, and reload behavior shall reflect a
   successful edit without changing their existing meaning.
8. The resulting complete expense shall satisfy the same validation contract as
   a newly added expense.
9. Failed validation, lookup, or persistence shall not expose a partial update
   or replace the previously valid ledger.
10. The CLI shall report a successful edit and the updated expense; failures
    shall be clear and return a non-zero status.

## Non-functional requirements

- IDs must address exactly one record reliably after reload; representation and
  schema must be documented by the Design Agent.
- Existing JSON data must not be silently discarded by identity/schema changes.
- Decimal precision and deterministic JSON output must be preserved.
- Existing add, list, total, filter, and persistence behavior must remain
  backward compatible unless an explicit migration decision is approved.
- The edit operation must use the local filesystem only and must not introduce a
  database, network service, or third-party dependency.
- Focused tests must use isolated ledgers and include cross-instance reload
  verification.

## Validation rules

- The ID is required, uses the Design Agent's documented format, and identifies
  exactly one existing expense.
- Missing, malformed, or unknown IDs must produce a clear lookup/validation
  error.
- At least one editable field must be supplied; an empty edit is invalid.
- An explicitly supplied amount must use the existing Decimal contract, remain
  finite, and be greater than zero. Binary-float conversion must not reduce
  monetary precision.
- An explicitly supplied description must be a non-empty string after trimming.
- An explicitly supplied category must use the existing case-insensitive,
  whitespace-normalized policy and supported category set:
  `Food`, `Travel`, `Shopping`, `Bills`, or `Other`.
- Unknown edit fields must be rejected rather than ignored.
- Duplicate IDs or invalid persisted records must fail clearly before an edit
  is saved.

## Edge cases

- Editing an ID in an empty or missing ledger.
- Editing an ID that is syntactically valid but not present.
- Duplicate IDs in existing or migrated JSON data.
- Legacy records that do not contain an ID.
- Malformed JSON, invalid record shape, invalid UTF-8, or invalid edited values.
- An edit that changes only one field, all editable fields, or no fields.
- Editing a record into a different category and verifying both filtered totals.
- A failed persistence replacement must leave the original file bytes unchanged.
- Interrupted or concurrent writes remain outside the current guarantee unless
  the Design Agent proposes a bounded requirement.

## Acceptance criteria

- Given a persisted expense with ID `X`, editing its description by `X` changes
  only that description, preserves its ID and insertion position, and persists
  the result.
- Given an edit with any valid subset of amount, category, and description, the
  resulting record passes the add validation contract.
- Given an edit that changes amount or category, unfiltered totals and relevant
  category-filtered totals reflect the new values after reload.
- Given a missing, malformed, duplicate, or unknown ID, the operation fails
  clearly and the existing ledger remains unchanged.
- Given no editable fields, an unknown field, blank description, invalid amount,
  or unsupported category, the operation fails validation and does not persist a
  partial update.
- Existing add/list/total/filter behavior and CLI syntax continue to pass their
  regression tests.
- Focused unit and CLI tests cover successful edits, partial/multiple edits,
  stable IDs, reload, lookup failures, validation failures, and failed-write
  safety.

## Impact on existing functionality

- The `Expense` data model and JSON record schema must gain an ID field or an
  equivalent stable identity mechanism.
- `add_expense` must generate or accept the identity according to the approved
  design while preserving existing caller behavior where possible.
- JSON load/save validation must handle the identity field and any approved
  legacy-data migration.
- The tracker API needs an edit operation, and the CLI needs a documented edit
  command while preserving existing command syntax.
- Listing output may need to display IDs so users can select a record to edit.
- Totals and category filters should not change their public meaning; they must
  operate on the updated record values.
- New tests and README/API documentation are required after implementation.

## Open questions and assumptions for the Design Agent

1. Which stable ID format is approved: UUID string, integer, or another
   standard-library-compatible representation?
2. Are IDs generated only by the application, or may trusted API callers supply
   them?
3. What exact CLI syntax represents partial edits, and how are omitted fields
   distinguished from explicitly empty values?
4. How are legacy records without IDs handled: deterministic migration,
   rejection, or another compatibility rule? No records may be lost.
5. Are duplicate IDs a fatal data error, and what error/status should the CLI
   expose?
6. Must `list` display IDs, and must edit output include the complete updated
   record?
7. Is the existing atomic-ish temporary-file replacement behavior sufficient,
   and what durability/concurrency guarantees are explicitly out of scope?
8. Confirm that edits do not create additional records and deletion remains out
   of scope.

## Requirements-stage handoff

- **Agent:** requirements-agent
- **Skill:** `.github/skills/requirements-analysis/SKILL.md`
- **Instructions followed:** `.github/copilot-instructions.md`
- **Input considered:** Existing implementation, tests, baseline requirements,
  repository conventions, and the edit-by-ID feature request
- **Output artifact:** This updated `docs/requirements-analysis.md`
- **Validation performed:** Checked that the feature has functional,
  non-functional, validation, edge-case, acceptance, compatibility, and
  clarification sections; no source or test files were modified.
- **Handoff to Design Agent:** Resolve ID representation, legacy JSON migration,
  CLI/API edit contract, duplicate-ID policy, and list-display behavior in
  `docs/design.md` and update `docs/implementation-plan.md` before development.
