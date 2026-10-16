---
agent: requirements-agent
description: Analyze a proposed Expense Tracker requirement.
---

Role: requirements-agent. Analyze this proposed Expense Tracker change: `${input:requirement}`. Ground the analysis in `README.md`, the current source/tests, and `docs/requirements-analysis.md`. Return structured sections for user story, functional requirements, non-functional requirements, acceptance criteria, edge cases, and out-of-scope decisions. Update only `docs/requirements-analysis.md`; do not implement code. Self-check that every acceptance criterion is testable and that persistence/error behavior is explicit.
