# Changelog: Fauve Houdini extension

Versions are the `version` in `extension/manifest.json`.

## 0.2.1 (in development)

- New recipe: FastPeopleSearch (`www.fastpeoplesearch.com`). Fills first, middle and last
  name and email in the opt-out start form only. Selectors are scoped to that form, so
  the site's people search is never filled. Tested by T16 Q.
- New recipe: Whitepages (`www.whitepages.com`). Fills nothing: the page has only the
  people-search bar and a profile-URL box. Houdini shows the manual steps instead and
  never runs the field finder there. Tested by T16 R.
- Recipe fills are now outlined in gold, like field-finder fills, so every filled field
  can be checked before submitting.
- Recipe fills now follow the field finder's rules: they skip hidden, off-screen,
  password, search, disabled, read-only and non-input fields, and never overwrite a value
  already in a field. Tested by T16 S.
- Permissions unchanged: `storage`, `scripting`, `activeTab`.

## 0.2.0

- Field classifier. On an unknown opt-out page, fields the field finder couldn't place
  are scored by a small logistic-regression classifier over character n-grams
  (`extension/classify.js`, weights in `extension/classifier.json`, built from fake data;
  see BUILD.md). No network, no model download, no LLM. Unsure answers (< 0.9) leave the
  field empty.
- `checkMapping` gate on classifier output and `describeFields` for unplaced fields
  (T17, T18). End-to-end tests including JS/Python parity, injection-style labels,
  off-screen traps and copied markers (T19).
- Popup input checks: name required, email format, phone pattern.

## 0.1.x (0.1.0 – 0.1.96)

- First release. Recipes for PeopleConnect (Instant Checkmate and TruthFinder) and
  Spokeo, with exact-host matching and stable `name` selectors.
- Field finder for other opt-out pages. It only runs on opt-out-looking URLs and needs a
  second confirming click on an unknown host.
- Fill only: never clicks, submits or logs in. Skips hidden, off-screen, password,
  search, disabled and read-only fields and people-search forms. The field finder never
  overwrites a value.
- Details are kept in `chrome.storage.session` only. Permissions are `storage`,
  `scripting` and `activeTab`, with no host permissions.
- Popup design updated to match the Houdini web page. Tested by T16 (A–P).
