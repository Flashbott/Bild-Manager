"""Bridge between the Pokémon Manager UI and the existing S1 generator."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType


GENERATOR_FILENAME = "pokemon_auswahl_aktualisieren.py"


def _candidate_generator_paths(project_root: Path) -> list[Path]:
    candidates: list[Path] = []
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        candidates.append(Path(bundle_root) / "engine" / GENERATOR_FILENAME)
    candidates.append(Path(__file__).resolve().parent / "engine" / GENERATOR_FILENAME)
    source_root_generator = Path(__file__).resolve().parents[1] / "Hilfsdateien" / GENERATOR_FILENAME
    candidates.append(source_root_generator)
    # In a source checkout the project generator remains a useful development
    # fallback. Packaged releases deliberately prefer the bundled, tested
    # generator so that an old project folder cannot silently downgrade logic.
    if os.environ.get("POKEMON_MANAGER_DEVELOPER_GENERATOR") == "1":
        candidates.append(project_root / "Hilfsdateien" / GENERATOR_FILENAME)
    elif not getattr(sys, "_MEIPASS", None):
        candidates.append(project_root / "Hilfsdateien" / GENERATOR_FILENAME)
    return candidates


def load_generator(project_root: Path) -> ModuleType:
    """Load the project generator or the bundled fallback generator."""
    generator_path = next(
        (path for path in _candidate_generator_paths(project_root) if path.is_file()),
        None,
    )
    if generator_path is None:
        raise FileNotFoundError(
            "Der S1-Aktualisierungsgenerator wurde nicht gefunden. "
            "Bitte die Anwendung reparieren oder den Projektordner prüfen."
        )

    module_name = "pokemon_generator_runtime"
    spec = importlib.util.spec_from_file_location(module_name, generator_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Generator konnte nicht geladen werden: {generator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "update_project"):
        raise RuntimeError(
            "Der vorhandene Generator ist zu alt für die Pokémon-Manager-App."
        )
    return module


def update_s1(project_root: Path) -> dict:
    generator = load_generator(project_root)
    return generator.update_project(project_root)
