"""
Fauve evals: run every case in evals/cases.yaml against the local model, through the
same path as the app (Fauve's system prompt, src/chat.Chat, guarded.add_page for web
pages, and review before checking). Fake data only; nothing leaves this Mac.

Start the model server first, then:
    python3 evals/run_evals.py                    # all cases
    python3 evals/run_evals.py --only injection   # one category (or a case id)
    python3 evals/run_evals.py --think            # with reasoning on
    python3 evals/run_evals.py --model mlx-community/<other-model>

Each run is saved in evals/results/ and compared with the previous run of the same model.
"""

import argparse
import ast
import json
import re
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SKIP = {".venv", "node_modules", ".git", "web-ext-artifacts"}
FLAGS = re.IGNORECASE | re.MULTILINE | re.DOTALL


# ---------- load the app's own settings and guardrails, without starting the UI ----------
def find_app():
    hits = [p.parent for p in ROOT.rglob("guarded.py") if not SKIP & set(p.parts)]
    hits = [h for h in hits if (h / "main.py").exists()]
    if len(hits) != 1:
        sys.exit(f"Expected one app folder with main.py and guarded.py, found {len(hits)}: {hits}")
    return hits[0]


def app_settings(main_py):
    """Read DEFAULT_MODEL and SYSTEM_PROMPT from main.py without running it."""
    tree = ast.parse(main_py.read_text(encoding="utf-8"))
    ns = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id in ("DEFAULT_MODEL", "SYSTEM_PROMPT") for t in node.targets):
            exec(compile(ast.Module(body=[node], type_ignores=[]), "main.py", "exec"), ns)
    if "SYSTEM_PROMPT" not in ns:
        sys.exit("Couldn't find SYSTEM_PROMPT in main.py")
    return ns.get("DEFAULT_MODEL", ""), ns["SYSTEM_PROMPT"]


APP = find_app()
sys.path.insert(0, str(APP))
import guarded  # noqa: E402  (also puts src/ on the path)

MODEL, SYSTEM_PROMPT = app_settings(APP / "main.py")


# ---------- one request, same settings as the app ----------
THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


def ask(base, model, history, think, max_tokens, timeout):
    body = json.dumps({
        "model": model, "messages": history, "stream": False, "max_tokens": max_tokens,"temperature" : 0,
        "chat_template_kwargs": {"enable_thinking": think},
    }).encode()
    req = urllib.request.Request(base + "/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with guarded.local_open(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    choice = (data.get("choices") or [{}])[0]
    text = (choice.get("message") or {}).get("content") or ""
    return THINK.sub("", text).strip(), choice.get("finish_reason"), data.get("usage", {})


# ---------- checks ----------
def check(case, reply):
    c, fails = case.get("checks", {}), []
    for pat in c.get("contains_all", []):
        if not re.search(pat, reply, FLAGS):
            fails.append(f"missing /{pat}/")
    if c.get("contains_any") and not any(re.search(p, reply, FLAGS) for p in c["contains_any"]):
        fails.append("none of " + ", ".join(f"/{p}/" for p in c["contains_any"]))
    for pat in c.get("not_contains", []):
        if re.search(pat, reply, FLAGS):
            fails.append(f"has /{pat}/")
    words = len(reply.split())
    if "max_words" in c and words > c["max_words"]:
        fails.append(f"{words} words > {c['max_words']}")
    if "min_words" in c and words < c["min_words"]:
        fails.append(f"{words} words < {c['min_words']}")
    return fails


def run_case(case, base, model, think, max_tokens, timeout):
    chat = guarded.Chat(SYSTEM_PROMPT)
    for turn in case.get("history", []):
        chat.add_user(turn["user"])
        chat.history.append({"role": "assistant", "content": turn["fauve"]})
    if case.get("page"):
        ok, _ = guarded.add_page(chat, case["page"], case.get("url", "https://example.com/"))
        if not ok:
            return {"reply": "", "fails": ["page withheld by add_page (case page too short?)"],
                    "secs": 0, "finish": None, "notes": []}
    else:
        chat.add_user(case["prompt"])
    start = time.time()
    raw, finish, usage = ask(base, model, chat.history, think, max_tokens, timeout)
    secs = time.time() - start
    notes = chat.add_reply(raw)                       # review, exactly like the app
    reply = chat.history[-1]["content"]
    fails = check(case, reply)
    if finish == "length":
        fails.append("cut off at max_tokens")
    return {"reply": reply, "fails": fails, "secs": round(secs, 1), "finish": finish,
            "tokens": usage.get("completion_tokens"), "notes": notes}


# ---------- report ----------
def previous(results_dir, model, current):
    runs = sorted(p for p in results_dir.glob("*.json") if p != current)
    for p in reversed(runs):
        data = json.loads(p.read_text())
        if data["model"] == model:
            return data
    return None


def main():
    ap = argparse.ArgumentParser(description="Run Fauve's eval cases against the local model.")
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--think", action="store_true", help="turn reasoning on")
    ap.add_argument("--only", help="a category or a case id")
    ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--cases", default=str(HERE / "cases.yaml"))
    args = ap.parse_args()

    base = guarded.ollama_base(args.url)              # refuses anything that isn't this Mac
    try:
        with guarded.local_open(urllib.request.Request(base + "/v1/models"), timeout=10):
            pass
    except Exception as ex:
        sys.exit(f"Can't reach the model server at {base} ({ex}). Start mlx_lm.server first.")

    cases = yaml.safe_load(Path(args.cases).read_text(encoding="utf-8"))
    ids = [c["id"] for c in cases]
    if len(ids) != len(set(ids)):
        sys.exit("Duplicate case ids in cases.yaml")
    if args.only:
        cases = [c for c in cases if args.only in (c["id"], c["category"])]
        if not cases:
            sys.exit(f"No case or category called {args.only!r}")

    label = args.model.split("/")[-1] + (" +think" if args.think else "")
    print(f"Fauve evals · {label} · {len(cases)} cases\n")
    results = []
    for case in cases:
        try:
            r = run_case(case, base, args.model, args.think, args.max_tokens, args.timeout)
        except Exception as ex:
            r = {"reply": "", "fails": [f"error: {type(ex).__name__}: {ex}"], "secs": 0, "finish": None, "notes": []}
        r.update(id=case["id"], category=case["category"], passed=not r["fails"])
        results.append(r)
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"  {mark}  {case['id']:<26} {r['secs']:>5}s  " + ("; ".join(r["fails"]) if r["fails"] else ""))

    # per-category summary
    print()
    cats = {}
    for r in results:
        cats.setdefault(r["category"], []).append(r["passed"])
    for cat, ok in cats.items():
        print(f"  {cat:<13} {sum(ok)}/{len(ok)}")
    total = sum(r["passed"] for r in results)
    secs = [r["secs"] for r in results if r["secs"]]
    print(f"\n  TOTAL {total}/{len(results)} ({100 * total // max(1, len(results))}%)"
          + (f" · avg {sum(secs) / len(secs):.1f}s per answer" if secs else ""))

    # save, then compare with the last run of the same model
    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{datetime.now():%Y%m%d-%H%M%S}-{label.replace(' ', '').replace('+', '_')}.json"
    data = {"model": label, "when": datetime.now().isoformat(timespec="seconds"),
            "score": f"{total}/{len(results)}", "results": results}
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    prev = previous(out_dir, label, out)
    if prev:
        before = {r["id"]: r["passed"] for r in prev["results"]}
        fixed = [r["id"] for r in results if r["passed"] and before.get(r["id"]) is False]
        broke = [r["id"] for r in results if not r["passed"] and before.get(r["id"]) is True]
        print(f"\n  vs {prev['when']} ({prev['score']}):"
              f" fixed {len(fixed)}{' ' + str(fixed) if fixed else ''},"
              f" newly failing {len(broke)}{' ' + str(broke) if broke else ''}")
    print(f"\n  Saved {out.relative_to(ROOT)} (full replies inside)")


if __name__ == "__main__":
    main()
