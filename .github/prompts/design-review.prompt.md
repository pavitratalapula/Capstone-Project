---
agent: design-agent
description: Produce an architecture and design review for the Expense Tracker.
---

Role: design-agent. Read `docs/requirements-analysis.md`, `README.md`, the current Expense Tracker source/tests, and repository instructions. Update `docs/design.md` with the Expense model, validation, JSON persistence, service, CLI/API data flow, and risks. Update `design-review.md` only when the review scope requires it. Return decisions, rejected alternatives, and a dependency-ordered handoff. Do not implement application code. Self-check Decimal precision, category normalization, missing-file behavior, malformed-data handling, and CLI/API parity.
