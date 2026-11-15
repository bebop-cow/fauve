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
"""

import os
import sys
import threading
import time
import urllib.request

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
        sys.argv = ["mlx_lm.server", "--model", model, "--host", HOST, "--port", str(port)]
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
        self.mode = None                  # "reused" or "started"
        self.errors = []
        self._thread = None

    def start(self):
        if answering(self.port):
            self.mode = "reused"
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
