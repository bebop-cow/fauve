# T16: Houdini extension (recipes + fill logic), tested on local fake pages.
# Run from the repo root:  python3 tests/t16_houdini_ext.py
# Needs: pip3 install playwright  &&  python3 -m playwright install chromium
# Uses only fake data. Never opens a real broker site.
import json, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

EXT = Path("extension")
problems = []

# ---------- static checks: files parse, permissions match recipes ----------
try:
    recipes = json.loads((EXT / "recipes.json").read_text())
except Exception as e:
    print("FAIL\n  recipes.json is not valid JSON:", e); sys.exit(1)
manifest = json.loads((EXT / "manifest.json").read_text())

# A: activeTab model: no standing access to any site.
#    The extension only touches the tab the user is on, when they click it.
if manifest.get("host_permissions"):
    problems.append("A: host_permissions present; activeTab model allows none")

# B: exactly storage + scripting + activeTab, nothing broader
if set(manifest.get("permissions", [])) != {"storage", "scripting", "activeTab"}:
    problems.append("B: permissions are not exactly storage + scripting + activeTab")

# C: every recipe has host, fields, manual; host is a bare domain
for key, r in recipes.items():
    if not all(k in r for k in ("label", "host", "fields", "manual")):
        problems.append(f"C: recipe '{key}' is missing a key")
    if not re.fullmatch(r"[a-z0-9.-]+", r.get("host", "")):
        problems.append(f"C: recipe '{key}' host is not a bare domain")

# ---------- pull the two functions out of popup.js, unchanged ----------
src = (EXT / "popup.js").read_text()

def grab(name):
    start = src.index(f"function {name}(")
    depth, i = 0, src.index("{", start)
    while True:
        depth += {"{": 1, "}": -1}.get(src[i], 0)
        i += 1
        if depth == 0:
            return src[start:i]

funcs = grab("splitName") + "\n" + grab("fillPage") + "\n" + grab("autoFill")

# Fake broker pages. Each records 'input' events the way a React page would,
# and records any click or submit so we can prove Houdini never does either.
SPY = """
<script>
  window.seen = {}; window.clicked = false; window.submitted = false;
  document.addEventListener('input', e => { window.seen[e.target.name] = e.target.value; });
  document.addEventListener('click', () => { window.clicked = true; }, true);
  document.addEventListener('submit', e => { e.preventDefault(); window.submitted = true; }, true);
</script>"""

PEOPLECONNECT = SPY + """
<form><input name="name-0-first"><input name="name-0-middle" value="KEEPME">
<input name="name-0-last"><button type="submit">Continue</button></form>"""

# A text input, not type="date": a date box silently rejects non-date text,
# which would let this check pass even if the disabled-skip were missing.
DOB = SPY + """<form><input name="dob-string" type="text" disabled></form>"""

SPOKEO = SPY + """
<input name="email" type="search" placeholder="site search">
<form><input name="url" type="url"><input name="email" type="email">
<button type="submit">OPT OUT</button></form>"""

FAKE = {"first": "Testy", "middle": "", "last": "McTest", "email": "fake@example.com"}

UNKNOWN = SPY + """
<form>
  <label>First name <input name="fname"></label>
  <label>Last name <input name="lname"></label>
  <input type="email" placeholder="Your email">
  <input type="tel" name="contact">
  <label>Name <input name="who"></label>
  <input type="email" name="trap" style="display:none">
  <input type="search" name="q" placeholder="Search people by email">
  <input name="first_name_2" value="ALREADY">
  <button type="submit">Send</button>
</form>"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    def load(html):
        page.set_content(html)
        # Define the two functions in the page; stop with the real error if they don't parse.
        err = page.evaluate("""code => {
            try { (0, eval)(code); }
            catch (e) { return String(e); }
            return (typeof splitName === 'function' && typeof fillPage === 'function' && typeof autoFill === 'function')
       ? '' : 'splitName, fillPage or autoFill missing after loading';
        }""", funcs)
        if err:
            print("FAIL\n  could not load the functions from popup.js:", err)
            print("  --- code the test pulled out of popup.js ---")
            print(funcs)
            sys.exit(1)

    def fill(fields, values):
        return page.evaluate("([f, v]) => fillPage(f, v)", [fields, values])

    # D: splitName
    load("")
    cases = {
        "Testy McTest": ("Testy", "", "McTest"),
        "  Ann  Bee   Cee Dee ": ("Ann", "Bee Cee", "Dee"),
        "Cher": ("Cher", "", ""),
    }
    for full, want in cases.items():
        got = page.evaluate("n => { const s = splitName(n); return [s.first, s.middle, s.last]; }", full)
        if tuple(got) != want:
            problems.append(f"D: splitName({full!r}) gave {got}")

    pc = recipes["peopleconnect"]["fields"]

    # E: PeopleConnect: names land, the page sees the input events
    load(PEOPLECONNECT)
    fill(pc, FAKE)
    seen = page.evaluate("window.seen")
    if seen.get("name-0-first") != "Testy" or seen.get("name-0-last") != "McTest":
        problems.append("E: first/last not filled, or page never saw the change")

    # F: an empty value never wipes what's already in a field
    if page.input_value('input[name="name-0-middle"]') != "KEEPME":
        problems.append("F: empty middle name erased an existing value")

    # G: the count reports only fields that really got a value
    load(PEOPLECONNECT)
    n = fill(pc, FAKE)
    if n != 2:
        problems.append(f"G: reported {n} filled, expected 2")

    # H: wrong-shaped values ({name: {...}}) fill nothing and report 0
    load(PEOPLECONNECT)
    n = fill(pc, {"name": {"first": "Testy", "last": "McTest"}, "email": "fake@example.com"})
    if n != 0:
        problems.append(f"H: bad value shape still reported {n} filled")

    # I: never clicks, never submits
    load(PEOPLECONNECT)
    fill(pc, FAKE)
    if page.evaluate("window.clicked || window.submitted"):
        problems.append("I: fill clicked or submitted something")

    # J: disabled fields are skipped
    load(DOB)
    n = fill({'input[name="dob-string"]': "first"}, FAKE)
    if page.input_value('input[name="dob-string"]') != "" or n != 0:
        problems.append("J: filled a disabled field")

    # K: Spokeo: only the email box in the form; search box and URL untouched
    load(SPOKEO)
    fill(recipes["spokeo"]["fields"], FAKE)
    if page.input_value('input[type="email"]') != "fake@example.com":
        problems.append("K: Spokeo email not filled")
    if page.input_value('input[type="search"]') or page.input_value('input[name="url"]'):
        problems.append("K: filled the search box or the URL box")

    # N: autoFill fills the clear fields and leaves everything doubtful alone
    load(UNKNOWN)
    n = page.evaluate("v => autoFill(v)", {**FAKE, "phone": "555-0100"})
    got = lambda sel: page.input_value(sel)
    if (got('[name="fname"]'), got('[name="lname"]'), got('[placeholder="Your email"]'), got('[name="contact"]')) != ("Testy", "McTest", "fake@example.com", "555-0100"):
        problems.append("N: autoFill missed a clear field")
    if got('[name="who"]') or got('[name="trap"]') or got('[name="q"]'):
        problems.append("N: autoFill filled an ambiguous, hidden or search field")
    if got('[name="first_name_2"]') != "ALREADY":
        problems.append("N: autoFill overwrote an existing value")
    if n != 4 or page.evaluate("window.clicked || window.submitted"):
        problems.append(f"N: count {n} (want 4), or it clicked/submitted")

    browser.close()

# L: recipe lookup is an exact host match
def find(host):
    return [k for k, r in recipes.items() if r["host"] == host]
if find("suppression.peopleconnect.us") != ["peopleconnect"]:
    problems.append("L: real host not matched")
for bad in ("suppression.peopleconnect.us.evil.com", "www.instantcheckmate.com", "spokeo.com.evil.com"):
    if find(bad):
        problems.append(f"L: matched look-alike host {bad}")
# M: the popup passes the name parts flat ({ ...name, email }), not nested ({ name, email }).
#    Nested values make fillPage find nothing and report "Filled 0".
    if not re.search(r"\{\s*\.\.\.name\s*,", src) or "args: [recipe.fields, values]" not in src:
       problems.append("M: popup.js must build values as { ...name, ... } and pass them to fillPage")
# the popup must use === for the host, not includes()
if "r.host === host" not in src:
    problems.append("L: popup.js no longer uses an exact host match")

if problems:
    print("FAIL"); [print(" ", p) for p in problems]; sys.exit(1)
print("T16 ok")
