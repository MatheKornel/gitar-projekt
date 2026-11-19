from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).resolve().parent
PYTHON_DIR = ROOT / "backend" / "python"

hiddenimports = [
    m for m in collect_submodules("music21")
    if ".test" not in m and ".corpus" not in m
]
hiddenimports += ["music21.corpus"]

datas = []
datas += collect_data_files("music21", excludes=["**/corpus/**", "**/test/**"])
datas += collect_data_files("librosa")

a = Analysis(
    [str(PYTHON_DIR / "main.py")],
    pathex=[str(PYTHON_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "IPython", "jupyter", "notebook"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GitarProjekt",
    # A program a print() kimenettel jelzi az állapotot és a hibákat,
    # ezért a konzolablak megmarad a GUI mellett.
    console=True,
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="GitarProjekt",
)
