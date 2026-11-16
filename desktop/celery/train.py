import re
from pathlib import Path
from sklearn.pipeline import make_pipeline, make_union
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import classification_report
import joblib

HERE = Path(__file__).resolve().parent
LINE = re.compile(r'^(\w+):\s*"(.*)"\s*$')

# 1. read examples.txt
#    for each line: skip blanks and lines starting with "#"
#    m = LINE.match(line); if no match, print the line and stop (catches typos in the file)
#    collect texts (m.group(2).strip()) and labels (m.group(1))

# 2. the model: words AND letter patterns, then logistic regression
#    words   = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), sublinear_tf=True)
#    letters = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
#    model   = make_pipeline(make_union(words, letters),
#                            LogisticRegression(class_weight="balanced", max_iter=2000))

# 3. honest test: cross-validation
#    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=1)
#    guesses = cross_val_predict(model, texts, labels, cv=folds)
#    print(classification_report(labels, guesses))
#    for each text, label, guess: if guess != label, print them (the mistakes to learn from)

# 4. train on everything and save
#    model.fit(texts, labels)
#    joblib.dump(model, HERE / "celery.joblib")