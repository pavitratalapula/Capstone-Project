# Legacy Implementation Plan: Automated Documentation Sync

The active Expense Tracker plan is `docs/implementation-plan.md`. This root
plan applies only to the retained Documentation Sync utility.

The tasks below describe the original implementation sequence. The utility is
implemented; its current behavior and verification are recorded after the
historical plan.

## Dependency-ordered work breakdown

### 1. Project skeleton
- Create the Python package layout and test directory.
- Define the CLI contract for repository and output arguments.

Blocked by: none

### 2. Repository scanner and file analysis
- Implement repository walking and file filtering.
- Count files, lines, and sizes for the generated summary.

Blocked by: project skeleton

### 3. Documentation gap detection
- Detect missing root docs, docs folder, and test coverage markers.
- Produce warnings for likely documentation gaps.

Blocked by: repository scanner

### 4. Markdown rendering
- Build the Markdown report structure.
- Include summary metrics, file inventory, and warnings.

Blocked by: repository scanner and document gap detection

### 5. CLI integration and validation
- Wire the scanner, analyzer, and renderer into the CLI entry point.
- Validate failure handling for invalid repo paths.

Blocked by: Markdown rendering

### 6. Test suite and verification
- Add unit tests for happy path and missing-path behavior.
- Run the proof commands and confirm output quality.

Blocked by: CLI integration

### 7. Final handoff
- Prepare the PR summary, evidence, and reviewer checklist.

Blocked by: verification

## Priority order
1. Project skeleton
2. Repository scan and analyzer
3. Gap detection
4. Markdown renderer
5. CLI integration
6. Test suite and validation
7. Final handoff

## Dependencies summary
The implementation is linear: the analyzer and gap detector must be complete before the report renderer can produce a stable final document, and CLI validation must run after the rendering logic is correct.

## Current implementation and verification

The existing utility in `src/documentation_sync.py` now prunes hidden and
generated directories, excludes its own selected output from inventory, uses
accurate line counts, detects test files by path/name rather than incidental
substring, and produces deterministic Markdown. It reports invalid UTF-8 and
filesystem failures clearly and refuses to overwrite an unrelated existing
file inside the scanned repository.

Current validation:

```text
C:/Python314/python.exe -m pytest tests/test_documentation_sync.py -q
11 passed in 0.10s

C:/Python314/python.exe -m pytest -q
56 passed in 0.33s

C:/Python314/python.exe -m compileall -q src tests
exit code 0
```

A temporary fixture containing 300 small Python files completed the full CLI
run in 0.241 seconds on this machine. This single measurement includes Python
startup and is not a guarantee for other machines or repository shapes.
