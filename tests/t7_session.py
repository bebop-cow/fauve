import sys
sys.path.insert(0, "src")
from session import Session

t = [1000.0]                       # fake clock, we move it by hand
s = Session(60, clock=lambda: t[0])
s.cookies["sid"] = "COOKIE-7f3a"
problems = []

# CHECK A: before expiry, everything works
if s.call_tool("view_cart") != "ok":
    problems.append("CHECK A: refused too early")
if "sid" not in s.cookies:
    problems.append("CHECK A: cookie lost early")

t[0] += 61                         # now past expiry

# CHECK B: cart tools refused
if s.call_tool("add_to_cart") == "ok":
    problems.append("CHECK B: cart tool allowed after expiry")

# CHECK C: cookies gone
if s.cookies:
    problems.append("CHECK C: cookies survived expiry")

# CHECK D: exactly at the expiry moment is already expired
t2 = [1000.0]
s2 = Session(60, clock=lambda: t2[0])
t2[0] = 1000.0 + 60
if s2.call_tool("view_cart") == "ok":
    problems.append("CHECK D: boundary allowed")

if problems:
    for p in problems:
        print("T7 BROKEN:", p)
    sys.exit(1)
print("T7 OK")