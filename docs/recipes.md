# Adding a Houdini recipe

A recipe tells Houdini exactly which fields to fill on one broker's opt-out page
(`extension/recipes.json`). Recipes are only written from a field list the maintainer
collected on the live page in their own browser. Selectors are never guessed, and no
script or headless browser is pointed past a broker's bot protection.

## 1. Collect the field list (maintainer, in your own browser)

1. Find the opt-out page from a link on the broker's own site (footer, privacy policy,
   "Do Not Sell"), not from a third-party guide. Note the exact URL and host.
2. Open it normally. If it shows a CAPTCHA or "verify you are human" page, complete it
   yourself as you normally would; that is you using the site, not Houdini.
3. Don't type anything into the page. Open DevTools (Console) and paste the snippet below.
   It reads the visible fields and copies them to your clipboard as JSON. It never types,
   clicks or submits.
4. Paste the JSON, the URL, and anything you noticed (search bars, dropdowns, checkboxes,
   multi-step flows) into the chat or issue.

```js
copy(JSON.stringify((() => {
  const visible = el => {
    const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return el.type !== 'hidden' && s.display !== 'none' && s.visibility !== 'hidden'
        && r.width >= 4 && r.height >= 4 && r.right > 0 && r.bottom > 0;
  };
  const labelText = el => [...(el.labels || [])].map(l => l.textContent.trim()).join(' | ');
  return [...document.querySelectorAll('input, select, textarea')].filter(visible).map(el => ({
    tag: el.tagName.toLowerCase(),
    name: el.getAttribute('name'),
    id: el.id || null,
    type: el.tagName === 'INPUT' ? el.type : null,
    autocomplete: el.getAttribute('autocomplete'),
    placeholder: el.getAttribute('placeholder'),
    aria_label: el.getAttribute('aria-label'),
    label: labelText(el) || null,
    disabled: el.disabled,
    readonly: !!el.readOnly,
    form_action: el.form ? el.form.getAttribute('action') : null,
  }));
})(), null, 2))
```

The function inside `copy(...)` is `DESCRIBE` from `tools/inspect_form.py`. If you change
one, change the other. `tools/inspect_form.py URL` does the same thing headless, but most
broker sites block headless browsers. When that happens, stop and use the snippet instead.

## 2. Draft the recipe

```json
"broker": {
  "label": "Broker",
  "host": "www.broker.com",
  "fields": { "form[action=\"/optout\"] input[name=\"firstname\"]": "first" },
  "manual": ["Everything Houdini must not do, in order"]
}
```

- `host`: the exact hostname from the URL bar. No wildcards, no scheme.
- `fields`: selector → one of `first`, `middle`, `last`, `email`, `phone`.
  - Use `name` attributes only. Never use generated class names or random-looking ids.
  - Scope every selector to the opt-out form (e.g. `form[action="..."]`) so a site
    search bar with the same `name` can't match first.
  - Never map a people-search bar, a profile-URL box, a password, a date of birth or an
    ID number.
  - If there's nothing safe to fill, use `"fields": {}` (like Whitepages). A recipe with
    empty fields still stops the field finder from guessing on that host, and the popup
    shows the manual steps.
- `manual`: steps the user does: searching, choosing their record, dropdowns, checkboxes,
  CAPTCHA, submit, email or phone verification.

## 3. Test it (T16)

In `tests/t16_houdini_ext.py`:

1. Add a fake copy of the form, built from the field list, with fake data only. Include
   the page's look-alike fields (header search bar, decoys with the same names) so the
   scoping is tested.
2. Add a check that runs the recipe and checks that:
   - the right fields get the right fake values and are outlined
   - search bars, dropdowns, checkboxes and anything unmapped stay untouched
   - the fill count is right
   - nothing is clicked or submitted
3. Add the host to check L: the exact host must match, and the bare domain and
   `<host>.evil.com` must not.
4. Positive control: break the recipe on purpose (unscope a selector, or map the search
   bar). Confirm the check fails, keep the failing output, then restore the recipe.
5. Update the T16 range in THREATMODEL.md and add a live-check line in
   docs/release-checklist.md.
6. Run `bash run_tests.sh`. It must end in `ALL TESTS PASSED`.

T16 only sees the fake copy. The maintainer checks every recipe on the live page before
it ships.
