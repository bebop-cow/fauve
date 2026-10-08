import sys
sys.path.insert(0, "src")
from retention import DAY, Retention

t = [1000.0]
r = Retention(lambda: t[0])
r.add("note1")
problems = []

# CHECK A: no prompt before day 3
t[0] = 1000.0 + 2.9 * DAY
if r.prompts_due() != []:
    problems.append("CHECK A: prompted too early")

# CHECK B: prompt at exactly day 3
t[0] = 1000.0 + 3 * DAY
if r.prompts_due() != ["note1"]:
    problems.append("CHECK B: no prompt at day 3")

# CHECK C: nothing erased before day 7
t[0] = 1000.0 + 6.9 * DAY
if r.sweep() != [] or "note1" not in r.items:
    problems.append("CHECK C: erased too early")

# CHECK D: erased at exactly day 7
t[0] = 1000.0 + 7 * DAY
if r.sweep() != ["note1"] or "note1" in r.items:
    problems.append("CHECK D: not erased at day 7")

# CHECK E: overdue data erased on next launch
t2 = [1000.0]
r2 = Retention(lambda: t2[0], items={"old": 1000.0})
t2[0] = 1000.0 + 30 * DAY
r2.launch()
if "old" in r2.items:
    problems.append("CHECK E: overdue item survived launch")

if problems:
    for p in problems:
        print("T10 BROKEN:", p)
    sys.exit(1)
print("T10 OK")