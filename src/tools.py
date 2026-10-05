import hashlib

def pin(description):
    return hashlib.sha256(description.encode()).hexdigest()

PINNED = {
    "search_email": "3e439c3c4168ff5690f98dad933970b918ca1d3db186182f261620e2f68f0e37",
    "create_draft": "cf8bf4b7e3445d389057c6de2dc9edf79d8fd8a8ae22a9349163d4200b5c4ab3",
}

def load_tools(registry):
    accepted, rejected = [], []
    for name, desc in registry.items():
        if name not in PINNED:
            rejected.append((name, "not on the allowlist"))
        elif pin(desc) != PINNED[name]:
            rejected.append((name, "description changed"))
        else:
            accepted.append(name)
    return accepted, rejected

