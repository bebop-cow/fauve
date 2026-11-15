"""
Fauve case files: saved cases, only when the user clicks SAVE.

- Nothing is saved automatically. Unsaved cases are gone when you start a new case or quit.
- Local files only: ~/Library/Application Support/Fauve/cases/<id>.json, folder 0700,
  files 0600, written atomically. Never sent anywhere.
- Everything is masked (src/scan.mask_sensitive) before it's written, and again on load.
- A case file holds the conversation, not the system prompt: a reopened case always runs
  under the app's current system prompt. Roles are user/assistant only.
- Ids are 32 hex characters, chosen here; the page can only pass an id back, never a path.
- A file that fails validation is skipped, never half-loaded.
- A chat that had web pages or pastes stays tainted when it's reopened.
"""
import json
import os
import re
import tempfile
import time
import uuid
from pathlib import Path

import guarded                       # puts src/ on the path for the next import
assert guarded.Chat
from scan import mask_sensitive      # noqa: E402  (src/scan.py)

DEFAULT_DIR = Path.home() / "Library" / "Application Support" / "Fauve" / "cases"
ID = re.compile(r"[0-9a-f]{32}")
KINDS = {"user", "fauve", "notice", "cloud"}
ROLES = {"user", "assistant"}
MAX_FILE = 4_000_000        # bytes per case file
MAX_TEXT = 200_000          # characters per message
MAX_ITEMS = 2_000           # messages per case
MAX_CASES = 500             # listed in the sidebar
TITLE_LEN = 60


class CaseError(Exception):
    """A case couldn't be saved or opened. The message is safe to show."""


def _text(v):
    if not isinstance(v, str):
        raise CaseError("a message isn't text")
    return mask_sensitive(v[:MAX_TEXT])


def title_for(messages):
    first = next((m["text"] for m in messages if m.get("kind") == "user"), "") or "Untitled case"
    one_line = " ".join(mask_sensitive(first).split())
    return one_line[:TITLE_LEN - 1] + "…" if len(one_line) > TITLE_LEN else one_line


def _clean(case):
    """Validate and mask a case dict (from the app or from disk). Raises CaseError."""
    if not isinstance(case, dict):
        raise CaseError("not a case")
    msgs, hist = case.get("messages"), case.get("history")
    if not isinstance(msgs, list) or not isinstance(hist, list) or len(msgs) > MAX_ITEMS or len(hist) > MAX_ITEMS:
        raise CaseError("the case is malformed or too long")
    messages = []
    for m in msgs:
        if not isinstance(m, dict) or m.get("kind") not in KINDS:
            raise CaseError("unknown message kind")
        model = m.get("model") or ""
        if not isinstance(model, str):
            raise CaseError("bad model name")
        messages.append({"kind": m["kind"], "text": _text(m.get("text")), "model": model[:100]})
    history = []
    for h in hist:
        if not isinstance(h, dict) or h.get("role") not in ROLES:     # never a system message
            raise CaseError("unknown role in the history")
        history.append({"role": h["role"], "content": _text(h.get("content"))})
    pastes = case.get("pastes", 0)
    return {
        "messages": messages, "history": history,
        "tainted": case.get("tainted") is True,
        "pastes": pastes if isinstance(pastes, int) and 0 <= pastes < 100_000 else 0,
        "title": title_for(messages),
    }


class CaseStore:
    def __init__(self, folder=None):
        self.dir = Path(folder) if folder else DEFAULT_DIR

    def _path(self, case_id):
        if not isinstance(case_id, str) or not ID.fullmatch(case_id):
            raise CaseError("that isn't a case id")
        return self.dir / f"{case_id}.json"

    def _ensure_dir(self):
        self.dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.dir, 0o700)

    def save(self, case, case_id=None):
        """Writes the case (masked). Returns its id. case_id=None makes a new one."""
        clean = _clean(case)
        case_id = case_id or uuid.uuid4().hex
        path = self._path(case_id)
        clean.update({"version": 1, "id": case_id, "saved": int(time.time())})
        data = json.dumps(clean, ensure_ascii=False).encode()
        if len(data) > MAX_FILE:
            raise CaseError("this case is too long to save")
        self._ensure_dir()
        fd, tmp = tempfile.mkstemp(dir=self.dir, prefix=".tmp-", suffix=".json")
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            os.replace(tmp, path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        return case_id

    def load(self, case_id):
        path = self._path(case_id)
        try:
            if path.is_symlink() or path.stat().st_size > MAX_FILE:
                raise CaseError("that case file can't be opened")
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise CaseError("that case file is gone") from None
        except (OSError, ValueError):
            raise CaseError("that case file can't be read") from None
        clean = _clean(raw)
        clean["id"] = case_id
        return clean

    def list(self):
        """[{id, title, saved}] newest first; files that don't validate are skipped."""
        if not self.dir.is_dir():
            return []
        out = []
        for p in self.dir.glob("*.json"):
            if not ID.fullmatch(p.stem):
                continue
            try:
                c = self.load(p.stem)
                saved = json.loads(p.read_text(encoding="utf-8")).get("saved", 0)
            except (CaseError, OSError, ValueError):
                continue
            out.append({"id": p.stem, "title": c["title"], "saved": saved if isinstance(saved, int) else 0})
        out.sort(key=lambda c: c["saved"], reverse=True)
        return out[:MAX_CASES]

    def delete(self, case_id):
        self._path(case_id).unlink(missing_ok=True)
