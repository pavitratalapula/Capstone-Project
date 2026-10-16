# Architecture: Repository Scope Index

The primary Expense Tracker architecture is in `docs/design.md`. The legacy
Documentation Sync architecture is retained below as a separate scope.

---

# Legacy Architecture: Automated Documentation Sync

## Overview
The solution is a lightweight CLI tool that scans a repository, extracts metadata from source and documentation files, and emits a Markdown documentation report. It is intentionally dependency-light so it can run in CI, dev desktops, or local authoring workflows without additional infrastructure.

The Expense Tracker is a separate, local-ledger scope documented in
`docs/design.md`; it is not part of this repository-scanning data flow.

## High-level components

### 1. Repository scanner
Responsible for traversing the project tree and filtering files that matter for documentation generation. It skips hidden directories such as `.git`, virtual environments, and build caches.

### 2. File analyzer
Responsible for reading supported text files and deriving relative path, extension, byte size, and line count.

### 3. Documentation gap detector
Responsible for checking whether common documentation anchors such as `README.md` or `docs/` exist and highlighting missing assets in the output.

### 4. Markdown renderer
Responsible for composing the final report into a stable, human-readable Markdown structure, including summary metrics and file inventory.

### 5. CLI entry point
Responsible for argument parsing, repository validation, output writing, and user-facing status messages.

## Data flow
1. The user passes a repository path and an output file path to the CLI.
2. The repository scanner walks the tree and identifies candidate files.
3. The file analyzer inspects each file and builds a structured list of metadata.
4. The gap detector compares the inventory with standard documentation expectations.
5. The Markdown renderer creates a summary report, including risk warnings and next steps.
6. The report is written to disk and reported back to the user.

## Technology choices
- Python 3.11+ standard library only
- `pathlib` for filesystem traversal
- `argparse` for CLI usage
- `dataclasses` for structured summaries
- Markdown output for easy review in pull requests and documentation

## Key design decisions
- Keep the implementation dependency-free to minimize installation friction.
- Keep the system deterministic so generated documentation is reviewable and diff-friendly.
- Prefer simple file metadata over full AST parsing to support broad repository types.
- Structure the report as a summary plus inventory to keep it readable while still actionable.

## Risks and mitigations
- Large repositories may generate lengthy reports because the file inventory is comprehensive for supported extensions. Hidden and common generated directories are pruned during traversal.
- Some repos include generated build artifacts. Mitigation: skip hidden and common cache directories.
- Documentation gaps may be false positives. Mitigation: present them as suggestions rather than strict blockers.
- Files that cannot be decoded as UTF-8 or read due to filesystem errors stop report generation with a clear CLI error; they are not silently omitted.
- The generated report omits volatile timestamps and excludes its own output path from the inventory so repeated runs over unchanged inputs are reproducible.

## Related design boundary

The Expense Tracker uses its own JSON persistence, Decimal model, and CLI
contract. Its dependency-ordered implementation and validation plan are in
`docs/implementation-plan.md`; those decisions must not be inferred from the
documentation-sync scanner.
