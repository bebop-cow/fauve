import re
from pathlib import Path
from model2vec import StaticModel
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import classification_report
import joblib

HERE = Path(__file__).resolve().parent
LINE = re.compile(r'^(\w+):\s*"(.*)"\s*$')

# 1. read examples.txt
texts = []
labels = []
with open(HERE / "examples.txt", encoding="utf-8") as f:
    for line in f:
        line = line.strip()                      # drop the newline and edge spaces
        if not line or line.startswith("#"):     # blank line or comment: skip it
            continue
        match = LINE.match(line)
        if not match:                            # a typo in the file: stop and show it
            sys.exit(f"Bad line in examples.txt: {line}")
        texts.append(match.group(2).strip())     # the message
        labels.append(match.group(1))            # the label before the colon

print(len(texts), sorted(set(labels)))



# 2. the model: turn every example into numbers by meaning, and use plain logistic regression on those numbers
embedder = StaticModel.from_pretrained("minishlab/potion-base-8M")   # downloads once (~30 MB), then cached
X = embedder.encode(texts)
model = LogisticRegression(class_weight="balanced", max_iter=2000)

# 3. honest test: cross-validation
folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=1)
guesses = cross_val_predict(model, X, labels, cv=folds)
print(classification_report(labels, guesses))
for text, label, guess in zip(texts, labels, guesses):
    if guess != label:
        print(f"{label} → {guess}: {text}")

# 4. train on everything and save
#    model.fit(texts, labels)
#    joblib.dump(model, HERE / "celery.joblib")