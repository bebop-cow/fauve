# Fauve

An open-source AI agent that can search, summarize, plan, and prepare drafts
for you, but never sends, pays, or stores passwords.

## Design rules
- Read, prepare, hand off: the agent reads and drafts; you do the final click.
- No send, pay, delete, or login tools exist inside the agent.
- Credentials never reach the model: scoped, short-lived OAuth tokens only,
  held in memory and wiped after 3 minutes of inactivity.
- The agent runs in a sandbox with default-deny network egress.
- An audit command lists exactly what the agent has stored.

## Status
Design phase. See [THREATMODEL.md](THREATMODEL.md) for the threat model.
Feedback and attack ideas are welcome via issues.

## License
See [LICENSE](LICENSE).
