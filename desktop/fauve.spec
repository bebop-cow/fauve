# PyInstaller spec for Fauve.app (the web-view interface, webui.py).
# Build with:  bash build_app.sh      Output: ~/Applications/Fauve.app
#
# What goes in the app: Python, webui + guards, Fauve's src/ pipeline, the page
# (ui/), the paintings and fonts, pywebview, and MLX + mlx_lm to run the model.
# What doesn't: the model itself. It stays in your Hugging Face cache
# (~/.cache/huggingface/hub), which the app reads offline.
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

HERE = Path(SPECPATH)
ROOT = HERE.parent
SRC = ROOT / "src"

datas = [
    (str(HERE / "ui" / "index.html"), "ui"),
    (str(HERE / "ui" / "app.css"), "ui"),
    (str(HERE / "ui" / "app.js"), "ui"),
    (str(HERE / "ui" / "icon-day-96.png"), "ui"),
    (str(HERE / "ui" / "icon-night-96.png"), "ui"),
    (str(HERE / "assets" / "panels" / "morning-edition.webp"), "assets/panels"),   # tall panels for the
    (str(HERE / "assets" / "panels" / "night-desk.webp"), "assets/panels"),        # 380px painting column
    (str(HERE / "assets" / "panels" / "red-studio.webp"), "assets/panels"),
    (str(HERE / "assets" / "panels" / "picnic.webp"), "assets/panels"),
    (str(HERE / "assets" / "panels" / "rainy-window.webp"), "assets/panels"),
    (str(HERE / "assets" / "panels" / "bella-ciao.webp"), "assets/panels"),
]
datas += [(str(f), "webfonts") for f in sorted((ROOT / "assets" / "fonts").glob("*"))]
# guarded.py looks for src/pipeline.py next to itself and refuses to start without it
datas += [(str(f), "src") for f in sorted(SRC.glob("*.py"))]
datas += collect_data_files("mlx")                 # mlx.metallib (the GPU kernels)
datas += collect_data_files("mlx_lm")              # chat templates, etc.

binaries = collect_dynamic_libs("mlx")

hiddenimports = (
    ["localserver", "cloud", "guarded", "chat", "pipeline", "sanitize", "scan", "draft_review",
     "html.parser", "mlx_lm.server", "webview.platforms.cocoa"]
    + collect_submodules("mlx")                     # the C++ core imports some of these itself
    + collect_submodules("mlx_lm")                  # models are loaded by name from the config
)

a = Analysis(
    [str(HERE / "webui.py")],
    pathex=[str(HERE), str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["flet", "flet_desktop", "flet_cli", "torch", "tensorflow", "jax", "flax",
              "matplotlib", "IPython", "notebook", "tkinter", "PyInstaller", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Fauve", console=False,
          argv_emulation=False, target_arch="arm64", codesign_identity=None)
coll = COLLECT(exe, a.binaries, a.datas, name="Fauve")
app = BUNDLE(
    coll,
    name="Fauve.app",
    icon=str(Path(os.environ["FAUVE_WORK"]) / "Fauve.icns"),   # made by build_app.sh
    bundle_identifier="local.fauve.desktop",
    version="0.1.0",
    info_plist={
        "CFBundleDisplayName": "Fauve",
        "CFBundleShortVersionString": "0.1.0",
        "LSMinimumSystemVersion": "14.0",
        "NSHighResolutionCapable": True,
        "LSApplicationCategoryType": "public.app-category.productivity",
    },
)
