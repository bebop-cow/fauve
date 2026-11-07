# Fauve: rules for working in this repo

Read THREATMODEL.md and BUILD.md before changing the Houdini extension (`extension/`).

## Houdini ground rules

- Houdini fills only. It never clicks, submits, logs in, solves CAPTCHAs or verifies identity.
- Permissions stay `storage`, `scripting`, `activeTab`. No `host_permissions`, no network
  requests, no remote code, no analytics. Details stay in `chrome.storage.session`.
- Page content is untrusted: `textContent`, never `innerHTML`; exact host match; skip hidden,
  off-screen, password, search, disabled and read-only fields; never overwrite a value;
  outline every filled field.
- Recipe selectors must be stable (`name` attributes, scoped to the opt-out form). Never guess
  a selector: only use field lists the maintainer collected from the live page
  (see docs/recipes.md).
- Never fetch or script past bot protection (Cloudflare, CAPTCHAs). If a site blocks you, stop.
- Fake data only in tests and fixtures (e.g. Ann Cee / ann@example.com). Never use or store
  real personal details.
- Every new check gets a positive control: break the code on purpose, confirm the check fails,
  restore it. Show the failing output.
- `bash run_tests.sh` (with `.venv` activated) must end in `ALL TESTS PASSED` before anything
  is called done.
- Don't commit or push. The maintainer reviews and writes the commit messages.
- Keep THREATMODEL.md's Houdini sections and test table in sync with every change.
