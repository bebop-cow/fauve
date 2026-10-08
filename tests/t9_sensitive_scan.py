import sys
sys.path.insert(0, "src")
from scan import find_sensitive

planted = {
    "card": "card4111111111111111",
    "ssn":  "ssn 123-45-6789",
    "aws_key": "AKIAIOSFODNN7EXAMPLE",
    "sk_key": "sk-sf495yoefhndostyfv869-",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----",
}

glued = [
    ("card4111111111111111", "card"),
    ("id_4111111111111111", "card"),
]

problems = []

# CHECK A: each planted secret is found with the right kind
for kind, sample in planted.items():
    found = find_sensitive(sample)
    if kind not in found:
        problems.append(f"CHECK A: {kind} not found")

# CHECK B: clean text finds nothing
safe = ["order 12345", "4111111111111112", "sk-short"]
for s in safe:
    if find_sensitive(s) != []:
        problems.append(f"CHECK B: false positive on {s!r}")

# CHECK C: everything in one text
bigstring = " ".join(planted.values())
found = find_sensitive(bigstring)
for kind in planted:
    if kind not in found:
        problems.append(f"CHECK C: {kind} is missing")

# CHECK D: 
for text, kind in glued:
    if kind not in find_sensitive(text):
        problems.append(f"CHECK D: {kind} missed in glued text")

if problems:
    for p in problems:
        print("T9 BROKEN:", p)
    sys.exit(1)
print("T9 OK")