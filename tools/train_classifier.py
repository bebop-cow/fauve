import csv, json
from pathlib import Path
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

def ngrams(text):
    # 1. lowercase, then turn anything that isn't a letter or digit into a space
    # 2. split into words; pad each one: " " + word + " "
    # 3. for n in 2, 3, 4: every n-character slice of the padded word
    # 4. return a dict {gram: count}
    ...

# load tools/hints.csv → list of hints, list of slots
# X = [ngrams(h) for h in hints]
# split 80/20 with train_test_split (stratify=slots, random_state=1)
# vec = DictVectorizer(); fit on train, transform test
# clf = LogisticRegression(class_weight="balanced", max_iter=1000)
# print accuracy on test, then each wrong one: hint, want, got