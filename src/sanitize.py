from html.parser import HTMLParser

COUNTERS = ["html_comment", "hidden_element", "invisible_char",
            "stray_closing_tag", "uncertain_style", "dark_mode_style"]

VOID = {"br", "img", "hr", "meta", "link", "input"}

def is_invisible(ch):
    return 0xE0000 <= ord(ch) <= 0xE007F or ch in "\u200b\u200c\u200d\u2060\ufeff"

def style_hides(style):
    s = "".join(style.lower().split()).replace("!important", "")
    props = dict(p.split(":", 1) for p in s.split(";") if ":" in p)
    if props.get("display") == "none": return True
    if props.get("visibility") == "hidden": return True
    if props.get("opacity") == "0": return True
    if props.get("color") == "transparent": return True
    if props.get("font-size") in ("0", "0px", "0pt"): return True
    fg = props.get("color")
    bg = props.get("background") or props.get("background-color")
    if fg and fg == bg: return True
    return False

class Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.kept = []
        self.stack = []        # entries: (tag, hidden)
        self.in_style = False
        self.report = {name: 0 for name in COUNTERS}

    def handle_comment(self, data):
        self.report["html_comment"] += 1

    def handle_data(self, data):
        if self.in_style:
            if "prefers-color-scheme: dark" in data:
                self.report["dark_mode_style"] += 1
            else:
                self.report["uncertain_style"] += 1
            return
        if self.stack and self.stack[-1][1]:   # top entry hidden?
            return                              # drop it
        for ch in data:
            if is_invisible(ch):
                self.report["invisible_char"] += 1
            else:
                self.kept.append(ch)

    def handle_starttag(self, tag, attrs):
        if tag == "style":
            self.in_style = True
            return
        if tag in VOID:
            return
        attrs = dict(attrs)
        parent_hidden = self.stack[-1][1] if self.stack else False
        own = (tag in ("script", "template")
               or "hidden" in attrs
               or style_hides(attrs.get("style", "")))
        if own:
            self.report["hidden_element"] += 1
        self.stack.append((tag, parent_hidden or own))

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False
            return
        if tag in VOID:
            return
        names = [t for t, _ in self.stack]
        if tag in names:
            while self.stack.pop()[0] != tag:
                pass
        else:
            self.report["stray_closing_tag"] += 1





def sanitize(raw_html):
    p = Sanitizer()
    try:
        p.feed(raw_html)
        p.close()
    except Exception:
        return None, {"error": "could not be cleaned"}
    text = "".join(p.kept)
    text = " ".join(text.split())
    return text, p.report