# Read-only form inspector for drafting Houdini recipes.
#   python3 tools/inspect_form.py URL [--headed]
# Opens URL in Chromium, waits for it to load, and prints every visible
# input, select and textarea with the attributes a recipe can key on.
#
# Read-only by design: it never types, clicks, submits, scrolls into forms,
# or tries to solve or get around a CAPTCHA or bot check. If the page looks
# like a bot wall or CAPTCHA, it says so and stops; a human has to look.
import json, sys
from playwright.sync_api import sync_playwright

DESCRIBE = """() => {
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
}"""

# Text that usually means a bot wall or CAPTCHA rather than the real form.
WALL = ["captcha", "verify you are human", "are you a robot", "checking your browser",
        "just a moment", "access denied", "cf-challenge", "challenge-platform",
        "press & hold", "unusual traffic", "request unsuccessful", "attention required"]

def main():
    if len(sys.argv) < 2 or not sys.argv[1].startswith("https://"):
        print("usage: python3 tools/inspect_form.py https://... [--headed]"); sys.exit(2)
    url, headed = sys.argv[1], "--headed" in sys.argv
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        page = browser.new_page()
        resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass   # busy pages never go idle; read what's there
        status = resp.status if resp else None
        html = page.content().lower()
        frames = [f.url for f in page.frames if f != page.main_frame]
        print(f"url:    {page.url}")
        print(f"status: {status}")
        print(f"title:  {page.title()!r}")
        hits = sorted({w for w in WALL if w in html}
                      | {"captcha iframe" for f in frames if "captcha" in f or "challenge" in f or "turnstile" in f})
        if hits:
            print("bot check / CAPTCHA signs:", ", ".join(hits))
        if status and status >= 400:
            print("blocked: HTTP", status)
        fields = page.evaluate(DESCRIBE)
        print(f"{len(fields)} visible field(s):")
        for f in fields:
            print("  " + json.dumps(f))
        browser.close()

if __name__ == "__main__":
    main()
