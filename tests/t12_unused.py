import sys
sys.path.insert(0, "src")
from retention import DAY, Retention

t = [1000.0]
r = Retention(lambda: t[0])
for k in ["A", "B", "C", "D"]:
    r.add(k)
problems = []

# keep everything alive: keep at day 3 and day 17
for day in (3, 17):
    t[0] = 1000.0 + day * DAY
    for k in ["A", "B", "C", "D"]:
        r.keep(k)
    if day == 3:
        t[0] = 1000.0 + 3.0 * DAY
        r.touch("C")
        t[0] = 1000.0 + 3.1 * DAY
        r.touch("D")
        t[0] = 1000.0 + 10 * DAY
        r.touch("A")

# CHECK C: before the boundary, C is not flagged yet (27.9 days after its touch)
t[0] = 1000.0 + 30.9 * DAY
if "C" in r.unused():
    problems.append("CHECK C: flagged before 28 days")

# CHECK A: at day 31 only B and C are flagged
t[0] = 1000.0 + 31 * DAY
if set(r.unused()) != {"B", "C"}:
    problems.append(f"CHECK A: wrong flags {sorted(r.unused())}")

# CHECK B: flagging does not delete
if not all(k in r.items for k in ["A", "B", "C", "D"]):
    problems.append("CHECK B: flagging erased something")

if problems:
    for p in problems:
        print("T12 BROKEN:", p)
    sys.exit(1)
print("T12 OK")