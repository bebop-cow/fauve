import json, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

EXT = Path("extension")
problems = []

MAP_SRC = (EXT / "mapping.js").read_text().replace("export ", "")
CANDS = [{"id": "0"}, {"id": "1"}]
cases = {
    "not json":       ("hello", []),
    "not an array":   ('{"id":"0","slot":"email"}', []),
    "unknown id":     ('[{"id":"99","slot":"email"}]', []),
    "unknown slot":   ('[{"id":"0","slot":"password"}]', []),
    "selector as id": ('[{"id":"0\\"],body","slot":"email"}]', []),
    "number id":      ('[{"id":0,"slot":"email"}]', []),
    "extra key":      ('[{"id":"0","slot":"email","value":"evil"}]', [{"id": "0", "slot": "email"}]),
    "duplicate":      ('[{"id":"0","slot":"email"},{"id":"0","slot":"phone"}]', [{"id": "0", "slot": "email"}]),
    "mixed":          ('[{"id":"1","slot":"last"},{"id":"7","slot":"first"}]', [{"id": "1", "slot": "last"}]),
}

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    # T17: checkMapping rejects anything the model shouldn't be able to do
    mp = browser.new_page()
    err = mp.evaluate("""code => {
        try { (0, eval)(code); } catch (e) { return String(e); }
        return typeof checkMapping === 'function' ? '' : 'checkMapping missing after loading';
    }""", MAP_SRC)
    if err:
        problems.append(f"T17: could not load mapping.js: {err}")
    else:
        for name, (raw, want) in cases.items():
            got = mp.evaluate("([c, r]) => checkMapping(c, r)", [CANDS, raw])
            if got != want:
                problems.append(f"T17 {name}: got {got}, want {want}")

    browser.close()

if problems:
    print("FAIL"); [print(" ", p) for p in problems]; sys.exit(1)
print("T17 ok")