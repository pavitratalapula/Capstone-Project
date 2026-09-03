# Automated Documentation Sync

This project implements a lightweight documentation sync tool for local repositories. It traverses a repository, summarizes the important files, checks for documentation gaps, and generates a Markdown report that is easy to share in pull requests or release reviews.

## Capstone workflow covered
- Requirements capture and documentation
- Architecture proposal and design review
- Implementation planning
- Working implementation and tests
- Verification and final PR summary

## Running the tool
```bash
python src/documentation_sync.py --repo demo_repo --output docs/demo_sync_report.md
```

## Project structure
- `src/documentation_sync.py` – CLI entry point and sync logic
- `tests/test_documentation_sync.py` – validation tests
- `demo_repo/` – sample project used for local verification
- `requirements.md` – functional and non-functional requirements
- `architecture.md` – system design summary
- `design-review.md` – risk review record
- `impl-plan.md` – dependency-ordered implementation plan

## Expected output
The generated report includes:
- repository summary
- file inventory by extension
- notes on likely documentation gaps
- a final set of recommended next steps
