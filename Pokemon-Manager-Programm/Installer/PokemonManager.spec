# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH).parent
app_dir = project_root / "App"
generator = project_root / "Hilfsdateien" / "pokemon_auswahl_aktualisieren.py"
version_file = project_root / "VERSION.json"
manual = project_root / "Gebrauchsanweisung_Pokemon-Auswahl.html"
readme = project_root / "README.md"


a = Analysis(
    [str(app_dir / "pokemon_manager.py")],
    pathex=[str(app_dir)],
    binaries=[],
    datas=[
        (str(generator), "engine"),
        (str(version_file), "."),
        (str(manual), "docs"),
        (str(readme), "docs"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    name="Pokemon-Manager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    exclude_binaries=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="Pokemon-Manager",
)
