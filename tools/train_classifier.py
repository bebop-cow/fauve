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
# load tools/hints.csv → list of hints, list of slots
# X = [ngrams(h) for h in hints]
# split 80/20 with train_test_split (stratify=slots, random_state=1)
# vec = DictVectorizer(); fit on train, transform test
# clf = LogisticRegression(class_weight="balanced", max_iter=1000)
# print accuracy on test, then each wrong one: hint, want, got