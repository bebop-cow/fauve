import sys
sys.path.insert(0, "src")
import pipeline
from chat import Chat

problems = []

# A: no paste yet, so it must not be tainted
c = Chat("SYS")
c.add_user("hi")
if c.tainted == True:
    problems.append("A: tainted before any paste")

# B: one clean paste
c = Chat("SYS")
c.add_paste("hello")
if not c.history[-1]["content"].startswith("[UNTRUSTED PASTE 1") or not c.tainted:
    problems.append("B: not tainted or label wrong")

# C: two pastes, numbers are distinct
c = Chat("SYS")
c.add_paste("one")
c.add_paste("two")
if "PASTE 2" not in c.history[2]["content"]:
    problems.append("C: label number wrong")

# D: withheld paste
real = pipeline.sanitize
pipeline.sanitize = lambda raw: (None, [])
c = Chat("SYS")
banners = c.add_paste("ATTACKER-TEXT-123")
pipeline.sanitize = real
if (not c.tainted
        or "[FAUVE NOTICE]" not in c.history[-1]["content"]
        or any("ATTACKER-TEXT-123" in m["content"] for m in c.history)
        or not banners):
    problems.append("D: withheld path wrong")

# E: reply is stored reviewed, as assistant
c = Chat("SYS")
c.add_reply("see https://evil.test/c?d=SECRET123")
if any("SECRET123" in m["content"] for m in c.history) or c.history[-1]["role"] != "assistant":
    problems.append("E: raw reply stored")

# F: only message 0 may be system
c = Chat("SYS")
c.add_paste("x"); c.add_user("y"); c.add_reply("z")
if any(m["role"] == "system" for m in c.history[1:]):
    problems.append("F: extra system message")

# G: secret in a paste never reaches history
c = Chat("SYS")
c.add_paste("card 4111111111111111")
if any("4111111111111111" in m["content"] for m in c.history):
    problems.append("G: card in history")

if problems:
    print("FAIL"); [print(" ", p) for p in problems]; sys.exit(1)
print("T15 ok")