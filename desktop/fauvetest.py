import urllib.request
from html.parser import HTMLParser

# 1. Is Ollama up?
try:
    r = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
    print("1. OLLAMA: UP")
except Exception as ex:
    print("1. OLLAMA: DOWN ->", ex)

# 2. Can we fetch the internet?
try:
    r = urllib.request.urlopen("https://connectivitycheck.gstatic.com/generate_204", timeout=5)
    print("2. INTERNET: UP, status", r.status)
except Exception as ex:
    print("2. INTERNET: DOWN ->", type(ex).__name__, ex)

# 3. Can we fetch YOUR site, and what's actually in the raw HTML?
site = "https://example.com"   # <-- PUT YOUR BUSINESS SITE URL HERE
try:
    req = urllib.request.Request(site, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    print(f"3. SITE FETCH: OK, {len(raw)} chars of raw HTML")
    print("   FIRST 300 CHARS OF HTML:")
    print("   " + raw[:300])
except Exception as ex:
    print("3. SITE FETCH: FAILED ->", type(ex).__name__, ex)