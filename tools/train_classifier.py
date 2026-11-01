import csv, json
from pathlib import Path
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import re

def ngrams(text):
    counts = {}
    clean = re.sub(r"[^\w]", " ", text.lower())
    for each in clean.split():
        padded = " " + each + " " 
        for n in 2,3,4:
            for start in range(len(padded) - n + 1):
                piece = padded[start:start+n]
                counts[piece] = counts.get(piece,0) + 1
    return counts

print(ngrams("Hi!"))   

path = Path(__file__).with_name("hints.csv")
f = open(path, encoding="utf-8")
rows = list(csv.DictReader(f))
hint = [row["hint"] for row in rows]
slot = [row["slot"] for row in rows]

X = [ngrams(h) for h in hint]
X_train, X_test, y_train, y_test = train_test_split(X, slots, test_size=0.2, stratify=slots, random_state=1)
vec = DictVectorizer()
X_train = vec.fit_transform(X_train)
X_test = vec.transform(X_test)
clf = LogisticRegression(class_weight="balanced", max_iter=1000)
clf.fit(X_train, y_train)
print(clf.score(X_test, y_test))
