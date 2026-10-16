# Requirements: Repository Scope Index

This repository contains two separate local utilities. The primary Expense
Tracker requirements are in `docs/requirements-analysis.md`. The legacy
Documentation Sync requirements are retained below for regression context.

---

# Legacy Requirements: Automated Documentation Sync

## User story
As a platform engineering team, we want an automated documentation sync workflow that scans a repository, extracts a machine-readable summary of the relevant files and modules, and produces a refreshed documentation report without manual copy-pasting.

## Problem statement
Teams maintain source code and documentation in different places, and the documentation often drifts from the actual implementation. This leads to stale onboarding guidance, poor release readiness, and inconsistent architecture records.

## Functional requirements
1. The system shall scan a target repository directory and identify the project entry points, source files, tests, and documentation assets.
2. The system shall summarize each file with metadata such as relative path, size, extension, and line count.
3. The system shall detect whether root documentation such as README.md or docs/ exists and record any documentation gaps.
4. The system shall generate a Markdown report that is easy to review in pull requests and local development workflows.
5. The system shall support a CLI invocation with a repository path and an output file path.
6. The system shall write the generated report to disk and exit with a clear status message.
7. The system shall handle missing repository paths gracefully by returning a structured error.

## Non-functional requirements
1. The tool must run using the standard Python runtime without third-party dependencies.
2. The tool must complete its core flow in under a second for repositories with a few hundred files.
3. The generated output must be deterministic and human-readable.
4. The tool must be safe to run repeatedly without altering source files beyond the generated documentation artifact.
5. The code must be easy to extend for future integrations with GitHub, Confluence, or Jira.

## Acceptance criteria
- A user can run the tool on any local repository and receive a Markdown summary file.
- The summary includes an overview, file inventory, and documentation gap analysis.
- Missing folders or invalid repo paths are reported clearly.
- The output is generated in a stable format suitable for code review and release documentation.

## Out of scope
- Remote repository sync to GitHub or Confluence APIs
- AI-generated prose for business requirements
- Multi-user or concurrent repository processing
- Secret scanning or security policy enforcement

---

# Requirements Analysis: Expense Tracker

## Scope note

This section records the baseline Expense Tracker requirements separately from
the legacy Automated Documentation Sync requirements above. The Expense
Tracker is the primary capstone application; its current approved feature set
and acceptance criteria are maintained in `docs/requirements-analysis.md`,
including the later edit-by-ID feature. Source and tests are reviewed against
those artifacts rather than used to infer new requirements.

## Problem statement

People need a small local expense ledger that records spending consistently,
can be reviewed and totaled, and remains available between program runs.
Without persistence and category filtering, users must manually reconstruct
their spending and cannot reliably answer how much was spent in a category.

## User story

As a person tracking personal spending, I want to add an expense with an
amount, category, and description, list my saved expenses, filter them by
category, and see a total, so that I can understand my spending without a
remote service.

## Functional requirements

1. The system shall add an expense containing a positive monetary amount, a
   category, and a non-empty description.
2. The supported categories shall be `Food`, `Travel`, `Shopping`, `Bills`,
   and `Other`; unsupported categories shall be rejected.
3. The system shall list all persisted expenses in insertion order.
4. The system shall calculate the total of all expenses.
5. The system shall filter the list and total by a selected category.
6. Categories shall be trimmed and matched case-insensitively when adding,
   editing, and filtering.
7. The system shall persist expenses locally as JSON and load them on a later
   invocation.
8. JSON records shall contain the amount, category, and description fields;
   monetary values shall be serialized as strings and round-trip without
   binary floating-point loss.
9. The system shall provide a CLI or equivalent user-facing command contract
   for add, edit-by-ID, list, and category-filtered list/total operations.
10. Invalid input, malformed JSON, and persistence read/write failures shall
    produce a clear user-facing error and must not silently discard existing
    expenses.

## Non-functional requirements

1. The implementation shall use the local filesystem only and require no
   network service or third-party runtime dependency.
2. Persistence writes shall be deterministic and use UTF-8 JSON.
3. A failed add or failed persistence operation shall leave the previously
   valid JSON data unchanged.
4. Listing and totals shall be repeatable for the same data file and inputs.
5. The behavior shall be covered by isolated unit tests, including persistence
   across separate tracker instances.
6. The data format and storage location shall be documented so users can
   back up or remove their local ledger.

## Acceptance criteria

- Given valid amount, category, and description values, adding an expense
  reports success and stores one record in the local JSON file.
- Given a persisted JSON file, a new process/instance lists the same expenses
  in insertion order.
- Given expenses of multiple categories, an unfiltered total equals the sum of
  all amounts and a category-filtered total equals only that category's sum.
- Listing with a category returns no records and a zero total when that
  category has no matching expenses.
- Zero, negative, non-numeric, or non-finite amounts are rejected with a
  clear error.
- Empty or whitespace-only descriptions and unsupported categories are
  rejected with a clear error.
- Missing storage is treated as an empty ledger (unless the chosen contract
  specifies a required file), while malformed JSON is reported as an error
  and does not overwrite the file.
- Unit tests verify add, list, total, filtering, JSON round-trip, validation,
  and persistence failure behavior.

## Edge cases

- Empty or missing JSON file.
- Malformed JSON, a non-array root value, missing fields, wrong field types,
  duplicate records, and unknown extra fields.
- Decimal scale is preserved without currency rounding; currency conversion is
  not supported.
- Categories are trimmed and case-insensitive; descriptions allow Unicode and
  internal newlines without an arbitrary length limit.
- The default path is relative to the working directory; parent directories are
  created when saving.
- Concurrent writers, interrupted writes, and power-loss durability are not
  guaranteed.
- Filtering matches one normalized category.

## Original baseline exclusions

- Cloud, database, account, login, or multi-device synchronization.
- Budgets, recurring expenses, income, refunds, or deletion.
- Charts, reports, date ranges, currencies conversion, taxes, or receipts.
- Import/export formats other than the defined local JSON file.
- Encryption, secret management, and financial advice.
- Features not approved in the current requirements and design artifacts.

Editing was excluded from the initial baseline but is now an approved feature;
see the edit-by-ID requirements in `docs/requirements-analysis.md`.
