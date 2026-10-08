import sys
sys.path.insert(0, "src")
from retention import DAY, Retention

t = [1000.0]
r = Retention(lambda: t[0])
r.add("note1")
problems = []

t[0] = 1000.0 + 5 * DAY
r.keep("note1")              # kept at day 5; everything below is counted from here
base = 1000.0 + 5 * DAY

# CHECK A: nothing happens before 14 days after the keep
t[0] = base + 13.9 * DAY
if r.sweep() != [] or r.prompts_due() != []:
    problems.append("CHECK A: acted too early after keep")

# CHECK B: prompt at exactly 14 days after the keep
t[0] = base + 14 * DAY
if r.prompts_due() != ["note1"]:
    problems.append("CHECK B: no prompt at day 14 after keep")

# CHECK C: not erased before 18 days after the keep
t[0] = base + 17.9 * DAY
if r.sweep() != [] or "note1" not in r.items:
    problems.append("CHECK C: erased too early after keep")

# CHECK D: ignored prompt means erased at 18 days after the keep
t[0] = base + 18 * DAY
if r.sweep() != ["note1"] or "note1" in r.items:
    problems.append("CHECK D: not erased at day 18 after keep")

# CHECK E: the 14 days restart from the latest keep (explicit each time)
t2 = [1000.0]
r2 = Retention(lambda: t2[0])
r2.add("x")
t2[0] = 1000.0 + 1 * DAY
r2.keep("x")
t2[0] = 1000.0 + 15 * DAY
r2.keep("x")
t2[0] = 1000.0 + 15 * DAY + 13.9 * DAY
if r2.prompts_due() != []:
    problems.append("CHECK E: second keep did not restart the 14 days")

# CHECK F: keeping a missing key does not create it
r.keep("nope")
if "nope" in r.items:
    problems.append("CHECK F: keep created a missing item")

# CHECK G: an erased key does not stay kept
t[0] = 1000.0 + 100 * DAY
r.add("note1")
t[0] = 1000.0 + 103 * DAY
if r.prompts_due() != ["note1"]:
    problems.append("CHECK G: kept status carried over after erase")

if problems:
    for p in problems:
        print("T11 BROKEN:", p)
    sys.exit(1)
print("T11 OK")