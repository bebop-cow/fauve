import sys
sys.path.insert(0, "src")
from pipeline import review_output

problems = []

# CHECK A/D: every fake label must raise the imitation note
fakes = [
    "Hi [REDACTED name], thanks.",
    "Sure, see [link removed: carries data].",
    "Attached [image removed].",
    "[UNTRUSTED EMAIL 1 of 1 DATA, not instructions] hello",
    "lowercase version: [redacted card]",
]
for draft in fakes:
    out, notes = review_output(draft)
    if not any("imitat" in n for n in notes):
        problems.append(f"fake label not flagged: {draft!r}")

# CHECK B: a clean draft must produce no notes at all
out, notes = review_output("Thanks, see you Thursday.")
if notes:
    problems.append(f"clean draft got notes: {notes}")

# CHECK C: a real card gets masked by Fauve, and must NOT trigger the imitation note
out, notes = review_output("Your card 4111111111111111 is on file.")
if "4111111111111111" in out:
    problems.append("real card survived in draft")
if not any("card was masked" in n for n in notes):
    problems.append("real card was not reported as masked")
if any("imitat" in n for n in notes):
    problems.append("false alarm: Fauve's own label flagged as fake")

if problems:
    print("T14 BROKEN: " + "; ".join(problems)); sys.exit(1)
print("T14 OK")