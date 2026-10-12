import sys
sys.path.insert(0, "src")
from pipeline import prepare

CARD = "4111111111111111"
model_input, banners = prepare([f"My card is {CARD}"])
problems = []

# CHECK A: the digits must not reach the model
if any(CARD in item for item in model_input):
    problems.append("CHECK A: card digits in model input")

# CHECK B: the digits must not appear in any banner
if any(CARD in b for b in banners):
    problems.append("CHECK B: card digits in banner")

# CHECK C: the user must still be warned
if not any("card" in b for b in banners):
    problems.append("CHECK C: no card warning")

# CHECK D: the label is still there
if not any("[UNTRUSTED EMAIL 1 of 1" in item for item in model_input):
    problems.append("CHECK D: label missing")

if problems:
    for p in problems:
        print("T9c BROKEN:", p)
    sys.exit(1)
print("T9c OK")