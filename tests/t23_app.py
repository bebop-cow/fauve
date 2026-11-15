# T23: Fauve.app (localserver.py, webui startup, fauve.spec). No model, no network:
# mlx_lm is replaced by a fake module.
# A  offline first: importing localserver sets HF_HUB_OFFLINE (and friends) before
#    anything can import huggingface_hub; webui imports localserver first in main()
#    and never imports mlx_lm / huggingface_hub / transformers at module level
# B  the app's model server listens on 127.0.0.1 only
# C  a server already answering on the port is reused, not started again
# D  a server that fails to start is reported, never hangs; while starting, the
#    prompt box is refused
# E  the build bundles Fauve's src/ pipeline, the page and every MLX module, and
#    leaves Flet out
import ast, contextlib, io, os, sys, time, types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".venv", "node_modules", ".git", "web-ext-artifacts"}
found = [p for p in ROOT.rglob("localserver.py") if not SKIP & set(p.parts) and (p.parent / "guarded.py").exists()]
if len(found) != 1:
    sys.exit(f"T23: expected one localserver.py next to guarded.py, found {len(found)}")
APP = found[0].parent
sys.path.insert(0, str(APP))

fails = []
def check(name, ok, detail=""):
    if not ok:
        fails.append(f"FAIL {name}: {detail}")

# ---------- A: offline before anything loads ----------
for k in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY"):
    os.environ.pop(k, None)
import localserver  # noqa: E402
check("A", os.environ.get("HF_HUB_OFFLINE") == "1" and os.environ.get("TRANSFORMERS_OFFLINE") == "1"
      and os.environ.get("HF_HUB_DISABLE_TELEMETRY") == "1",
      "importing localserver must put Hugging Face in offline mode")

HEAVY = ("mlx", "mlx_lm", "huggingface_hub", "transformers")
def top_imports(tree):
    names = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            names += [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module.split(".")[0])
    return names
ls_src = (APP / "localserver.py").read_text()
check("A", not set(top_imports(ast.parse(ls_src))) & set(HEAVY),
      "localserver.py imports mlx / huggingface at module level (before offline mode is set)")
web_src = (APP / "webui.py").read_text()
web_tree = ast.parse(web_src)
check("A", not set(top_imports(web_tree)) & set(HEAVY + ("localserver",)),
      "webui.py imports mlx / huggingface / localserver at module level")
main_fn = next((f for f in web_tree.body if isinstance(f, ast.FunctionDef) and f.name == "main"), None)
first = main_fn.body[0] if main_fn and main_fn.body else None
check("A", isinstance(first, ast.Import) and first.names[0].name == "localserver",
      "webui.main() must import localserver before anything else")

# ---------- fake mlx_lm.server ----------
CALLS = []
fake_server = types.ModuleType("mlx_lm.server")
def fake_main():
    CALLS.append(list(sys.argv))
    if FAKE["fail"]:
        raise RuntimeError("could not load the model (fake)")
    time.sleep(FAKE["serve"])
fake_server.main = fake_main
fake_pkg = types.ModuleType("mlx_lm")
fake_pkg.server = fake_server
sys.modules["mlx_lm"], sys.modules["mlx_lm.server"] = fake_pkg, fake_server
FAKE = {"fail": False, "serve": 0.3}
FREE_PORT = 59117                       # nothing should answer here

# ---------- B: 127.0.0.1 only ----------
check("B", localserver.HOST == "127.0.0.1", f"HOST is {localserver.HOST}")
s = localserver.LocalServer("fake/model", FREE_PORT)
check("B", s.start() == "started", "no server on the port, so the app should start its own")
time.sleep(0.2)
argv = CALLS[-1] if CALLS else []
host = argv[argv.index("--host") + 1] if "--host" in argv else None
check("B", host == "127.0.0.1", f"the model server would listen on {host!r}, not 127.0.0.1: {argv}")
check("B", "--port" in argv and argv[argv.index("--port") + 1] == str(FREE_PORT), f"wrong port: {argv}")

# ---------- C: reuse a running server ----------
CALLS.clear()
real_answering = localserver.answering
localserver.answering = lambda port=localserver.PORT, timeout=2: True
try:
    s = localserver.LocalServer("fake/model", FREE_PORT)
    mode = s.start()
    time.sleep(0.2)
    check("C", mode == "reused" and not CALLS and s.ready(timeout=2) is None,
          f"a running server should be reused (mode {mode}, started {len(CALLS)} time(s))")
finally:
    localserver.answering = real_answering

# ---------- D: failures are reported ----------
FAKE["fail"] = True
s = localserver.LocalServer("fake/model", FREE_PORT)
log = io.StringIO()
with contextlib.redirect_stderr(log):
    s.start()
    t = time.monotonic()
    err = s.ready(timeout=20)
check("D", "failed to start" in log.getvalue(), "a failed start should be logged to stderr (Console.app)")
check("D", err and "could not load the model" in err and time.monotonic() - t < 10,
      f"a failed start should be reported quickly, got {err!r}")
FAKE["fail"] = False

import webui  # noqa: E402
from guarded import Chat  # noqa: E402
class FakeModel:
    model = "fake-local"
    def __init__(self): self.chat = Chat("SYS")
    def is_up(self): return True
    def reset(self): self.chat = Chat("SYS")
    def generate(self, on_raw): return "hi"
api = webui.Api(FakeModel(), run=lambda fn: fn(), starting=True)
st = api.send("hello")
check("D", st["busy"] and not any(m["kind"] == "user" for m in st["messages"]),
      "the prompt box should be refused while the model is starting")
api._started("could not load the model (fake)")
st = api.state()
check("D", not st["busy"] and any("didn't start" in m["text"] for m in st["messages"]),
      "a failed start should end 'busy' and say so")
api = webui.Api(FakeModel(), run=lambda fn: fn(), starting=True)
api._started(None, "reused")
st = api.state()
check("D", not st["busy"] and any(m["kind"] == "fauve" for m in st["messages"]),
      "a good start should greet and accept messages")

# ---------- E: what the build bundles ----------
spec = (APP / "fauve.spec").read_text()
check("E", 'SRC.glob("*.py")' in spec and '"src")' in spec,
      "fauve.spec doesn't bundle src/ (guarded.py refuses to start without it)")
for f in ("index.html", "app.css", "app.js"):
    check("E", f'"ui" / "{f}"' in spec, f"fauve.spec doesn't bundle ui/{f}")
import webui as _webui
for _sel, _path, _mime in _webui.ART:          # build_page() inlines these; a missing one crashes the app
    _rel = _path.relative_to(APP)
    _expr = " / ".join(f'"{part}"' for part in _rel.parts)      # e.g. "assets" / "panels" / "red-studio.webp"
    check("E", _expr in spec, f"fauve.spec doesn't bundle {_rel} (used by the page)")
check("E", 'collect_submodules("mlx")' in spec and 'collect_submodules("mlx_lm")' in spec,
      "fauve.spec doesn't collect every mlx / mlx_lm module (the app's model server can't import them)")
check("E", 'collect_data_files("mlx")' in spec, "fauve.spec doesn't bundle mlx.metallib")
check("E", '"flet"' in spec.split("excludes=")[1].split("]")[0] if "excludes=" in spec else False,
      "fauve.spec should exclude Flet")

if fails:
    print("\n".join(fails))
    sys.exit(1)
print("T23 OK")
