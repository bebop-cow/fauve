import sys
sys.path.insert(0, "src")
from sanitize import sanitize

EXPECTED = {"html_comment": 1, "hidden_element": 5,
            "invisible_char": 13, "stray_closing_tag": 2,
            "uncertain_style": 1, "dark_mode_style": 1}

GONE = ["PAYLOAD-COMMENT", "PAYLOAD-DISPLAYNONE", "PAYLOAD-WHITE",
        "PAYLOAD-FONT0", "PAYLOAD-UNCLOSED", "PAYLOAD-STRAY"]
SURVIVE = ["Hi, your invoice is attached.", "PAYLOAD-CLASS"]

text, report = sanitize(open("tests/t2_email.html", encoding="utf-8").read())
problems = []

if text is None:
    problems.append("sanitizer failed closed")
else:
    for m in GONE:
        if m in text:
            problems.append(f"CHECK 1: {m} survived")
    if any(0xE0000 <= ord(c) <= 0xE007F for c in text):
        problems.append("CHECK 1: invisible characters survived")
    for s in SURVIVE:
        if s not in text:
            problems.append(f"CHECK 2: {s} missing")
    if report != EXPECTED:
        problems.append(f"CHECK 3: counts are {report}")

if problems:
    for p in problems:
        print("T2 BROKEN:", p)
    sys.exit("failure")
print("T2 OK")