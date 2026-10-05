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

v0.1, design plus tested building blocks. Not a working agent yet.

Implemented and tested:
- Threat model (THREATMODEL.md)
- Test harness with stub agents (T1: injection, encodings, blobs)
- HTML sanitizer for hidden content (T2, T2B)

Planned: tool layer, sandbox, OAuth broker, local model, retention
and erase commands (T3 to T12).

Run all tests: ./run_tests.sh 

## License
See [LICENSE](LICENSE).
