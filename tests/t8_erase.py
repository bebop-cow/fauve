import sys, os, tempfile
sys.path.insert(0, "src")
sys.path.insert(0, "tests")
from store import Store
from checks import canary_forms, CANARY

def leaks(root, store):
    found = []
    for folder, _, files in os.walk(root):
        for f in files:
            data = open(os.path.join(folder, f), errors="ignore").read()
            if any(form in data for form in canary_forms(CANARY)):
                found.append(f)
    if any(form in str(store.cache) for form in canary_forms(CANARY)):
        found.append("cache")
    return found

with tempfile.TemporaryDirectory() as root:
    s = Store(root)
    s.save("note1", f"secret {CANARY}")
    problems = []

    # CHECK 0: planting worked (otherwise the test proves nothing)
    if not leaks(root, s):
        problems.append("CHECK 0: canary not planted")

    # CHECK D: save wrote exactly what we gave it
    with open(os.path.join(root, "note1")) as f:
        if f.read() != f"secret {CANARY}":
            problems.append("CHECK D: file contents differ from saved text")

    # CHECK E: saving the same key again replaces the old text
    s.save("note1", "second version")
    with open(os.path.join(root, "note1")) as f:
        if f.read() != "second version":
            problems.append("CHECK E: second save did not replace the first")

    s.erase("note1")

    # CHECK A: nothing left anywhere
    left = leaks(root, s)
    if left:
        problems.append(f"CHECK A: canary left in {left}")

    # CHECK B: erasing a key that doesn't exist must not crash
    try:
        s.erase("nope")
    except Exception:
        problems.append("CHECK B: erase crashed on missing key")




if problems:
    for p in problems:
        print("T8 BROKEN:", p)
    sys.exit(1)
print("T8 OK")