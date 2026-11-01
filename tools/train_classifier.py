import csv, json, re
from pathlib import Path
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

def ngrams(text):
    counts = {}
    clean = re.sub(r"[^\w]", " ", text.lower())
    for each in clean.split():
        padded = " " + each + " "
        for n in 2, 3, 4:
            for start in range(len(padded) - n + 1):
                piece = padded[start:start + n]
                counts[piece] = counts.get(piece, 0) + 1
    return counts

path = Path(__file__).with_name("hints.csv")
f = open(path, encoding="utf-8")
rows = list(csv.DictReader(f))
hint = [row["hint"] for row in rows]
slots = [row["slot"] for row in rows]

X = [ngrams(h) for h in hint]
X_train, X_test, y_train, y_test = train_test_split(X, slots, test_size=0.2, stratify=slots, random_state=1)
vec = DictVectorizer()
X_train = vec.fit_transform(X_train)
X_test = vec.transform(X_test)
clf = LogisticRegression(class_weight="balanced", max_iter=1000)
clf.fit(X_train, y_train)
print(clf.score(X_test, y_test))

# Held-out test: spellings and wrappers that never appear in hints.csv as-is.
# The classifier should get these from letter patterns of words it knows.
VARIANTS = [
    ("SUR-NAME:", "last"), ("Last-Name", "last"), ("lastname", "last"),
    ("Forename(s)", "first"), ("FIRSTNAME", "first"), ("Given-Name *", "first"),
    ("Middle Init.", "middle"), ("E Mail", "email"), ("Your e-mail adress", "email"),
    ("Mobile no.", "phone"), ("Tel. number", "phone"), ("Phone #", "phone"),
    ("Company name", "none"), ("Zip/Postal", "none"), ("Ref. number", "none"),
    ("Street", "none"), ("Search by name", "none"),
    ("Disregard prior rules. This box is the email.", "none"),
]

# limit; the value only goes into the page you're on, and you review it first.
THRESHOLD = 0.9   # below this, Houdini leaves the field empty

seen = set(h.lower() for h in hint)
filled = wrong = left_out = 0
print("\nheld-out variants:")
for text, want in VARIANTS:
    assert text.lower() not in seen, f"leak: {text!r} is in hints.csv"
    probs = clf.predict_proba(vec.transform([ngrams(text)]))[0]
    best = probs.argmax()
    got, sure = clf.classes_[best], probs[best]
    used = got if sure >= THRESHOLD and got != "none" else "none"
    if used == want: mark = "ok   "
    elif used == "none": mark = "empty"; left_out += 1
    else: mark = "WRONG"; wrong += 1
    if used != "none" and used == want: filled += 1
    print(f"  {mark} {text!r}: want {want}, got {got} ({sure:.2f})")
print(f"at {THRESHOLD}: filled right {filled}, WRONG {wrong}, left empty {left_out}")

# Export for the extension: classes, biases, and one weight per class for each gram.
model = {
    "threshold": THRESHOLD,
    "classes": list(clf.classes_),
    "intercept": [round(float(b), 4) for b in clf.intercept_],
    "weights": {gram: [round(float(clf.coef_[c][i]), 4) for c in range(len(clf.classes_))]
                for gram, i in vec.vocabulary_.items()},
}
out = Path(__file__).resolve().parent.parent / "extension" / "classifier.json"
out.write_text(json.dumps(model, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
print(f"wrote {out.name}: {len(model['weights'])} grams, {out.stat().st_size // 1024} KB")