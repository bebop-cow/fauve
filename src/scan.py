import re

CARD = re.compile(r"(?<!\d)\d{13,19}(?!\d)")

SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")

KEYS = {
    "aws_key":     re.compile(r"AKIA[0-9A-Z]{16}"),
    "sk_key":      re.compile(r"sk-[0-9A-Za-z_-]{20,}"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}




def luhn_ok(digits):
    nums = [int(c) for c in digits][::-1]
    total = 0
    for i, d in enumerate(nums):
        if i % 2 == 1:
            d = d * 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def find_sensitive(text):
    findings = []
    for m in CARD.finditer(text):
        if luhn_ok(m.group(0)):
            findings.append("card")
    for m in SSN.finditer(text):
        findings.append("ssn")
    for kind, pattern in KEYS.items():
        if pattern.search(text):
            findings.append(kind)
    return findings