import sys
sys.path.insert(0, "src")
from scan import mask_sensitive

CARD_OK = "4111111111111111"        # fake test card, passes Luhn
CARD_BAD = "4111111111111112"       # fails Luhn: must be left alone
SSN = "123-45-6789"
AWS = "AKIAIOSFODNN7EXAMPLE"
RSA = ("-----BEGIN RSA PRIVATE KEY-----\n"
       "FAKEKEYBODYLINEONE\n"
       "FAKEKEYBODYLINETWO\n"
       "-----END RSA PRIVATE KEY-----")

text = (f"card {CARD_OK} and ssn {SSN} and key {AWS}. "
        f"order number {CARD_BAD} is not a card.\n{RSA}")
out = mask_sensitive(text)
problems = []

# CHECK A: the real values must be gone
for name, value in [("card", CARD_OK), ("ssn", SSN), ("aws_key", AWS)]:
    if value in out:
        problems.append(f"CHECK A: {name} value still in output")

# CHECK B: values are replaced by labels, not just deleted
for label in ["[REDACTED card]", "[REDACTED ssn]", "[REDACTED aws_key]"]:
    if label not in out:
        problems.append(f"CHECK B: {label} missing from output")

# CHECK C: a number that fails Luhn must be left alone
if CARD_BAD not in out:
    problems.append("CHECK C: non-card number was masked")

# CHECK D: masking text with nothing sensitive changes nothing
plain = "Hi, lunch Friday at 12?"
if mask_sensitive(plain) != plain:
    problems.append("CHECK D: clean text was changed")

# CHECK E: the key body must not survive masking
for body in ["FAKEKEYBODYLINEONE", "FAKEKEYBODYLINETWO"]:
    if body in out:
        problems.append("CHECK E: private key body still in output")

if problems:
    for p in problems:
        print("T9b BROKEN:", p)
    sys.exit(1)
print("T9b OK")