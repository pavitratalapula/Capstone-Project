# Custom Agents and Runtime Delegation

## Custom agents

Custom agents are repository configuration files under `.github/agents/`. They
define reusable roles, tools, inputs, outputs, skills, handoffs, and validation
rules for the Expense Tracker:

- `requirements-agent.md`
- `design-agent.md`
- `development-agent.md`
- `qa-agent.md`
- `code-review-agent.md`
- `documentation-agent.md`

They are selectable Copilot customizations, not evidence that they ran.

## Runtime subagents and delegation

A runtime subagent is a separate agent process/context delegated work by a
parent agent during a live interaction. It is different from a repository
custom-agent definition.

This repository does not contain a runtime transcript, delegation log, parent
agent ID, subagent ID, or tool trace. Therefore it does **not** claim that a
specific runtime subagent delegation occurred. The SDLC artifacts demonstrate
the intended handoffs and reproducible roles, not hidden execution history.

## Reviewer interpretation

During a live capstone demonstration, show the custom agent files and invoke
the relevant agent explicitly if runtime delegation evidence is required. Keep
the resulting transcript or approved summary separately from the repository
unless it is intentionally committed. Do not convert the existence of a custom
agent file into a claim of subagent execution.
