"""
The local model server for Fauve.app: mlx_lm.server on this Mac only.

- Offline first: HF_HUB_OFFLINE and friends are set when this module is
  imported, before mlx_lm or huggingface_hub load. The model comes from the
  Hugging Face cache on disk; nothing asks huggingface.co for updates.
- 127.0.0.1 only, never 0.0.0.0, so nothing else on the network can reach it.
- If a server already answers on the port (for example one you started in
  Terminal), Fauve uses it and leaves it running when it quits.
- Otherwise it runs inside the app's own process (a background thread), so it
  stops when Fauve quits. No second Python, no Terminal window.
- Before starting, it checks the model is in the cache. If it isn't (for example
  ~/.cache was cleared), Fauve says so at launch with the download command,
  instead of starting a server that fails on every message.
- The server logs warnings and errors only (never request bodies, which hold the
  chat). In Fauve.app they go to ~/Library/Logs/Fauve/fauve.log (folder 0700, file 0600).
"""

import os
import sys
import threading
import time
import urllib.request
from pathlib import Path

OFFLINE_ENV = {
    "HF_HUB_OFFLINE": "1",              # never contact huggingface.co
    "HF_HUB_DISABLE_TELEMETRY": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "HF_DATASETS_OFFLINE": "1",
    "DO_NOT_TRACK": "1",
}
os.environ.update(OFFLINE_ENV)          # before anything imports huggingface_hub

HOST = "127.0.0.1"
PORT = 8080
LOG_LEVEL = "WARNING"                   # INFO/DEBUG would log request bodies (the chat)
LOG_DIR = Path.home() / "Library" / "Logs" / "Fauve"
LOG_MAX = 1_000_000                     # bytes; the old log is kept once as fauve.log.1


def download_command(model):
    return f"hf download {model}"


def model_on_disk(model):
    """True if the model's weights are in the Hugging Face cache. Offline: never downloads."""
    try:
        from huggingface_hub import snapshot_download    # here: after OFFLINE_ENV is set
        path = Path(snapshot_download(model, local_files_only=True))
        return any(path.glob("*.safetensors"))
    except Exception:
        return False


def log_to_file(folder=None):
    """Fauve.app has no terminal: send stderr (warnings, errors, tracebacks) to a
    private log file. Returns its path."""
    folder = Path(folder) if folder else LOG_DIR
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(folder, 0o700)
    path = folder / "fauve.log"
    if path.exists() and path.stat().st_size > LOG_MAX:
        os.replace(path, folder / "fauve.log.1")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.fchmod(fd, 0o600)
    sys.stderr = os.fdopen(fd, "a", buffering=1)
    return path


def base_url(port=PORT):
    return f"http://{HOST}:{port}"


def answering(port=PORT, timeout=2):
    """True if a model server answers on this Mac at the port."""
    from guarded import local_open      # localhost only, never via a proxy
    try:
        with local_open(urllib.request.Request(base_url(port) + "/v1/models"), timeout=timeout):
            return True
    except Exception:
        return False


def _serve(model, port, errors):
    try:
        from mlx_lm import server         # imported here: after OFFLINE_ENV is set
        argv = sys.argv
        sys.argv = ["mlx_lm.server", "--model", model, "--host", HOST, "--port", str(port),
                    "--log-level", LOG_LEVEL]
        try:
            server.main()                 # blocks: serves until the app quits
        finally:
            sys.argv = argv
    except BaseException as ex:          # noqa: BLE001  (report anything, incl. SystemExit from argparse)
        import traceback                  # log first (Console.app), then let ready() see it
        print("Fauve: the model server failed to start:", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        errors.append(f"{type(ex).__name__}: {ex}"[:300])


class LocalServer:
    """start() returns at once; ready() waits until the model answers."""

    def __init__(self, model, port=PORT):
        self.model, self.port = model, port
        self.mode = None                  # "reused", "started" or "missing"
        self.errors = []
        self._thread = None

    def start(self):
        if answering(self.port):
            self.mode = "reused"
            return self.mode
        if not model_on_disk(self.model):
            self.errors.append(f"the model {self.model} isn't downloaded on this Mac (it may have been "
                               f"removed with ~/.cache). Download it once, about 6 GB, in Terminal with: "
                               f"{download_command(self.model)}")
            self.mode = "missing"
            return self.mode
        self._thread = threading.Thread(target=_serve, args=(self.model, self.port, self.errors),
                                        name="mlx_lm.server", daemon=True)
        self._thread.start()
        self.mode = "started"
        return self.mode

    def ready(self, timeout=300):
        """Waits for the server. Returns None when it answers, or why it didn't."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if answering(self.port, timeout=2):
                return None
            if self.errors:
                return self.errors[0]
            if self._thread is not None and not self._thread.is_alive():
                return "the model server stopped"
            time.sleep(0.5)
        return f"it didn't answer within {timeout} seconds"
