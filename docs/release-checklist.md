# Houdini release checklist

For each extension release. Steps marked **HUMAN** are done by the maintainer; nothing
here is done against live sites by scripts or agents.

## 1. Code and docs

- [ ] `extension/manifest.json` `version` bumped; CHANGELOG.md has an entry for it.
- [ ] Permissions are exactly `storage`, `scripting`, `activeTab`; no `host_permissions`.
- [ ] THREATMODEL.md Houdini sections and test table match the code (T16 range, new
      recipes, new threats).
- [ ] Every new check has a positive control (broken on purpose, failing output seen,
      restored).
- [ ] `source .venv/bin/activate && bash run_tests.sh` ends in `ALL TESTS PASSED`.

## 2. Lint and build

```
npx web-ext lint --source-dir extension
npx web-ext build --source-dir extension --overwrite-dest
```

- [ ] Lint: 0 errors. Read every warning and note why any that remain are fine.
- [ ] The zip is in `web-ext-artifacts/` and its name has the new version.
- [ ] If the classifier changed: rebuild it (BUILD.md step 2) and check the last line
      matches BUILD.md.

## 3. Local check (BUILD.md step 5)

- [ ] Serve `tests/fixtures`, load `extension/` unpacked, open
      `http://localhost:8000/opt-out.html`, enter fake details, and click Fill twice.
- [ ] Expect "Filled 2 field(s)": Forename and Mobile no. Company name, the
      instruction-like label, the off-screen field and the locked field stay empty.

## 4. Live checks per recipe (**HUMAN**)

Load the built extension. Use your own details only on the broker's real page, and
**don't submit** unless you mean to opt out. For each broker, check the host, what fills
(outlined in gold), what stays empty, and the popup message. If a field moved or was
renamed, don't ship that recipe: collect a new field list (docs/recipes.md) and fix it.

| Broker | Page | Should fill (outlined) | Must stay empty / untouched | Popup |
|---|---|---|---|---|
| PeopleConnect (Instant Checkmate, TruthFinder) | `suppression.peopleconnect.us`, name step after you log in | First, middle (if you have one), last name | Email login, birthdate, record choice, Desired Behavior | "Filled n field(s)" + manual steps |
| Spokeo | `www.spokeo.com` opt-out page | Email box in the opt-out form | Listing URL box, site search, CAPTCHA | "Filled 1 field(s)" + manual steps |
| FastPeopleSearch | `www.fastpeoplesearch.com/optout` | First, middle, last name, email (in the opt-out form) | "I am" list, agreement checkbox, header people search, CAPTCHA | "Filled 4 field(s)" (3 with no middle name) + manual steps |
| Whitepages | `www.whitepages.com/suppression-requests` | Nothing | Header search (`s_name`, `s_loc`), profile-URL box | "Nothing for Houdini to fill on this step" + the 4 manual steps |
| TruePeopleSearch | _recipe not written yet_ | | | |
| BeenVerified | _recipe not written yet_ | | | |

Also check:

- [ ] A look-alike host (e.g. `fastpeoplesearch.com` without `www`, if it doesn't
      redirect) gets no recipe. Houdini falls back to the field finder only on
      opt-out-looking paths, after the warning click.
- [ ] A non-opt-out page (e.g. a broker's home page) gets "This doesn't look like an
      opt-out page".
- [ ] Nothing is ever clicked or submitted by Houdini.
- [ ] Type something into a mapped field first, then click Fill: your text stays.
- [ ] Closing the browser clears saved details.

## 5. Store submission (**HUMAN**)

**Firefox (AMO)**

- Upload the zip from `web-ext-artifacts/`.
- Source code: the extension is hand-written and not minified or bundled. The one
  generated file is `extension/classifier.json` (classifier weights). In the reviewer
  notes, point to BUILD.md, which explains how to rebuild it with
  `tools/make_hints.py` and `tools/train_classifier.py` (fake data, fixed seed). Attach
  the source zip if AMO asks for it.
- Data collection: `data_collection_permissions` is `none` (in the manifest). Houdini
  sends nothing anywhere.

**Chrome Web Store**

- Upload the same zip.
- Single purpose: fills data broker opt-out forms in the current tab; the user submits.
- Permission justifications:
  - `activeTab`: fill the form on the tab the user is on, only when they click.
  - `scripting`: inject the fill function into that tab.
  - `storage`: keep the user's details in session memory (`chrome.storage.session`)
    until the browser closes.
- Privacy practices: no data collected, sold or transferred. Remote code: none.

**After approval**

- [ ] Replace `FIREFOX-LINK` and `CHROME-LINK` in `web/houdini.html` with the listing
      URLs, then publish the page.
- [ ] Update THREATMODEL.md's status table ("in the stores").
