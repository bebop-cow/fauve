import sys
sys.path.insert(0, "src")
from pipeline import prepare

GONE = ["PAYLOAD-COMMENT", "PAYLOAD-DISPLAYNONE", "PAYLOAD-WHITE",
        "PAYLOAD-FONT0", "PAYLOAD-UNCLOSED", "PAYLOAD-STRAY"]

raw = open("tests/t2_email.html", encoding="utf-8").read()
model_input, banners = prepare([raw, None])
problems = []

seen = " ".join(model_input)
for m in GONE:
    if m in seen:
        problems.append(f"CHECK A: {m} reached the model")
if len(model_input) != 1:
    problems.append(f"CHECK B: model got {len(model_input)} items")
if len(banners) != 2:
    problems.append(f"CHECK C: {len(banners)} banners")

if problems:
    for p in problems:
        print("T2B BROKEN:", p)
    sys.exit(1)
print("T2B OK")