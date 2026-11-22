from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import re
import sys
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "S1"
INDEX_DIR = PROJECT_ROOT / "Index"
INDEX_MD = INDEX_DIR / "pokemon-index.md"
INDEX_JSON = INDEX_DIR / "pokemon-index.json"
OUTPUT_HTML = PROJECT_ROOT / "Pokemon-Bilder-Auswahl.html"
ARCHIVE_DIR = PROJECT_ROOT / "Hilfsdateien" / "Archiv"

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
EXTENSION_PRIORITY = {
    ".png": 0,
    ".jpg": 1,
    ".jpeg": 2,
    ".webp": 3,
    ".gif": 4,
    ".bmp": 5,
}


def configure_project(project_root: Path) -> None:
    """Point the generator at a selected project folder."""
    global PROJECT_ROOT, DEFAULT_SOURCE, INDEX_DIR, INDEX_MD, INDEX_JSON
    global OUTPUT_HTML, ARCHIVE_DIR

    PROJECT_ROOT = project_root.resolve()
    DEFAULT_SOURCE = PROJECT_ROOT / "S1"
    INDEX_DIR = PROJECT_ROOT / "Index"
    INDEX_MD = INDEX_DIR / "pokemon-index.md"
    INDEX_JSON = INDEX_DIR / "pokemon-index.json"
    OUTPUT_HTML = PROJECT_ROOT / "Pokemon-Bilder-Auswahl.html"
    ARCHIVE_DIR = PROJECT_ROOT / "Hilfsdateien" / "Archiv"


def configure_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def normalize_rel(value: str) -> str:
    return value.replace("\\", "/").lstrip("./")


def normalize_label(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def display_name_from_path(path: Path) -> str:
    return path.stem.replace("_", " ")


def make_id(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(char for char in normalized if not unicodedata.combining(char))
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").casefold()
    return slug or "pokemon"


def unique_id(base: str, used: set[str]) -> str:
    candidate = make_id(base)
    if candidate not in used:
        return candidate
    number = 2
    while f"{candidate}-{number}" in used:
        number += 1
    return f"{candidate}-{number}"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def split_markdown_row(line: str) -> list[str]:
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    return [cell.strip().replace("\\|", "|") for cell in value.split("|")]


def parse_bool(value: str) -> bool:
    return value.strip().casefold() in {"ja", "yes", "true", "1", "neu"}


def parse_index(path: Path) -> list[dict]:
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    header_index = None
    header: list[str] = []
    for index, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        cells = split_markdown_row(line)
        normalized = [cell.strip(" *").casefold() for cell in cells]
        if "id" in normalized and "datei" in normalized and "anzeigename" in normalized:
            header_index = index
            header = normalized
            break

    if header_index is None:
        return []

    columns = {name: index for index, name in enumerate(header)}

    def cell(cells: list[str], name: str, default: str = "") -> str:
        index = columns.get(name)
        if index is None or index >= len(cells):
            return default
        return cells[index].strip()

    entries: list[dict] = []
    for line in lines[header_index + 2 :]:
        if not line.lstrip().startswith("|"):
            break
        cells = split_markdown_row(line)
        if not cells or all(not value.replace("-", "").strip() for value in cells):
            continue
        if len(cells) < len(header):
            cells.extend([""] * (len(header) - len(cells)))
        try:
            order = int(cell(cells, "reihenfolge", "0") or "0")
        except ValueError:
            order = 0
        entries.append(
            {
                "id": cell(cells, "id"),
                "anzeigename": cell(cells, "anzeigename"),
                "datei": normalize_rel(cell(cells, "datei")),
                "status": cell(cells, "status", "aktiv") or "aktiv",
                "neu": parse_bool(cell(cells, "neu", "nein")),
                "reihenfolge": order,
                "sha256": cell(cells, "sha-256") or cell(cells, "sha256"),
                "duplikat_von": cell(cells, "duplikat von") or cell(cells, "duplikat_von"),
            }
        )
    return [entry for entry in entries if entry["id"] and entry["datei"]]


def is_automatic_name(entry: dict) -> bool:
    old_stem = Path(entry.get("datei", "")).stem
    return normalize_label(entry.get("anzeigename", "")) == normalize_label(old_stem)


def format_markdown(entries: list[dict], generated_at: str, source: Path) -> str:
    source_label = source.name or "S1"
    lines = [
        "# Pokémon-Index für S1",
        "",
        "> Diese Datei ist die führende, lesbare Indexdatei für die Pokémon-Auswahl.",
        "> Neue Dateien werden beim Aktualisierungslauf ergänzt. Fehlende Dateien bleiben als fehlt dokumentiert.",
        f"> Quelle: {source_label}",
        f"> Letzte Aktualisierung: {generated_at}",
        "",
        "| ID | Anzeigename | Datei | Status | Neu | Reihenfolge | SHA-256 | Duplikat von |",
        "|---|---|---|---|---|---:|---|---|",
    ]
    for entry in entries:
        values = [
            entry["id"],
            entry["anzeigename"].replace("|", "\\|"),
            entry["datei"].replace("|", "\\|"),
            entry["status"],
            "ja" if entry.get("neu") else "nein",
            str(entry["reihenfolge"]),
            entry.get("sha256", ""),
            entry.get("duplikat_von", ""),
        ]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def safe_json_for_script(value: object) -> str:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


HTML_TEMPLATE = """<!doctype html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pokémon auswählen und drucken</title>
<style>
@page { size: A4 portrait; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { font-family: Arial, Helvetica, sans-serif; color: #172033; background: #eef2f7; }
.screen-only { max-width: 1180px; margin: 0 auto; padding: 22px; }
h1 { margin: 0 0 8px; font-size: 28px; }
.intro { margin: 0 0 8px; font-size: 16px; }
.updated { margin: 0 0 18px; color: #526176; font-size: 13px; }
.toolbar { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 18px; }
button { border: 0; border-radius: 8px; padding: 10px 15px; font-size: 15px; font-weight: 700; cursor: pointer; background: #dbe5f5; color: #172033; }
button:hover { filter: brightness(0.96); }
button.primary { background: #2166d1; color: white; }
.filter-bar { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 18px; }
.filter-bar button.active { background: #172033; color: white; }
#selectionStatus { margin: 0 0 18px; font-weight: 700; }
#chooser { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 12px; }
.pokemon-card { display: block; padding: 10px; border: 2px solid #d9e0ea; border-radius: 12px; background: white; cursor: pointer; transition: border-color .12s ease, box-shadow .12s ease; }
.pokemon-card:hover { border-color: #91afe0; }
.pokemon-card.selected { border-color: #2166d1; box-shadow: 0 0 0 3px #d5e4ff; }
.card-header { display: flex; align-items: center; gap: 8px; min-height: 28px; margin-bottom: 8px; }
.card-header input { width: 20px; height: 20px; accent-color: #2166d1; flex: 0 0 auto; }
.card-title { font-weight: 700; flex: 1; }
.new-badge { border-radius: 999px; padding: 3px 7px; background: #e7f7ec; color: #146c2e; font-size: 11px; font-weight: 700; }
.thumbnail { height: 125px; display: flex; align-items: center; justify-content: center; overflow: hidden; border-radius: 8px; background: #05070d; }
.thumbnail img { max-width: 100%; max-height: 100%; width: auto; height: auto; object-fit: contain; }
#printPreview { padding: 0 22px 22px; background: #eef2f7; }
.preview-heading { max-width: 1180px; margin: 0 auto 10px; font-size: 18px; font-weight: 700; }
.empty-preview { max-width: 1180px; margin: 0 auto; padding: 20px; border-radius: 10px; background: white; color: #526176; }
.print-page { width: 210mm; height: 297mm; padding: 6mm; margin: 0 auto 18px; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: repeat(3, 1fr); gap: 2mm; background: white; box-shadow: 0 3px 16px rgba(23, 32, 51, .18); page-break-after: always; }
.print-page:last-child { page-break-after: auto; }
.print-cell { min-width: 0; min-height: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; border: 0.2mm solid #ddd; }
.print-cell img { max-width: 100%; max-height: 100%; width: auto; height: auto; object-fit: contain; }
.bottom-print-action { max-width: 1180px; margin: 0 auto; padding: 0 22px 28px; text-align: center; }
.bottom-print-action button { min-width: 250px; }
@media print {
  html, body { background: white; }
  .screen-only, .preview-heading, .empty-preview, .bottom-print-action { display: none !important; }
  #printPreview { padding: 0; background: white; }
  .print-page { margin: 0; box-shadow: none; }
}
</style>
</head>
<body>
<section class="screen-only">
  <h1>Pokémon auswählen und drucken</h1>
  <p class="intro">Setze bei den gewünschten Pokémon einen Haken. Beim Drucken werden nur die ausgewählten Bilder im 2×3-Raster auf A4-Seiten verwendet.</p>
  <p class="updated">Indexstand: __GENERATED_AT__</p>
  <div class="toolbar">
    <button type="button" id="selectAll">Alle auswählen</button>
    <button type="button" id="selectNew">Nur neue auswählen</button>
    <button type="button" id="clearAll">Auswahl löschen</button>
    <button type="button" class="primary" id="printSelected">Ausgewählte Pokémon drucken</button>
  </div>
  <div class="filter-bar" aria-label="Anzeige-Filter">
    <button type="button" class="active" data-filter="all">Alle anzeigen</button>
    <button type="button" data-filter="new">Nur neue anzeigen</button>
  </div>
  <p id="selectionStatus" aria-live="polite"></p>
  <div id="chooser" aria-label="Pokémon-Auswahl"></div>
</section>

<section id="printPreview" aria-live="polite">
  <p class="preview-heading">Druckvorschau</p>
  <p class="empty-preview">Noch kein Pokémon ausgewählt.</p>
</section>

<section class="bottom-print-action" aria-label="Druckauftrag">
  <button type="button" class="primary" id="printSelectedBottom">Druckauftrag starten</button>
</section>

<script>
const pokemon = __DATA__;
const chooser = document.getElementById("chooser");
const preview = document.getElementById("printPreview");
const status = document.getElementById("selectionStatus");
const selectedIds = new Set();
let currentFilter = "all";

function visibleItems() {
  return currentFilter === "new" ? pokemon.filter((item) => item.new) : pokemon;
}

function selectedItems() {
  return pokemon.filter((item) => selectedIds.has(item.id));
}

function renderChooser() {
  chooser.replaceChildren();
  for (const item of visibleItems()) {
    const label = document.createElement("label");
    label.className = "pokemon-card" + (selectedIds.has(item.id) ? " selected" : "");
    const header = document.createElement("span");
    header.className = "card-header";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = selectedIds.has(item.id);
    checkbox.setAttribute("aria-label", item.name + " auswählen");
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) selectedIds.add(item.id);
      else selectedIds.delete(item.id);
      label.classList.toggle("selected", checkbox.checked);
      renderPreview();
      updateStatus();
    });
    const title = document.createElement("span");
    title.className = "card-title";
    title.textContent = item.name;
    header.append(checkbox, title);
    if (item.new) {
      const badge = document.createElement("span");
      badge.className = "new-badge";
      badge.textContent = "Neu";
      header.appendChild(badge);
    }
    const thumbnail = document.createElement("span");
    thumbnail.className = "thumbnail";
    const image = document.createElement("img");
    image.src = item.file;
    image.alt = item.name;
    thumbnail.appendChild(image);
    label.append(header, thumbnail);
    chooser.appendChild(label);
  }
  updateStatus();
}

function updateStatus() {
  status.textContent = selectedIds.size + " von " + pokemon.length + " ausgewählt";
}

function renderPreview() {
  preview.querySelectorAll(".print-page, .empty-preview").forEach((node) => node.remove());
  const selected = selectedItems();
  if (selected.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty-preview";
    empty.textContent = "Noch kein Pokémon ausgewählt.";
    preview.appendChild(empty);
    return;
  }
  for (let start = 0; start < selected.length; start += 6) {
    const page = document.createElement("section");
    page.className = "print-page";
    for (let slot = 0; slot < 6; slot += 1) {
      const cell = document.createElement("div");
      cell.className = "print-cell";
      const item = selected[start + slot];
      if (item) {
        const image = document.createElement("img");
        image.src = item.file;
        image.alt = item.name;
        cell.appendChild(image);
      }
      page.appendChild(cell);
    }
    preview.appendChild(page);
  }
}

document.getElementById("selectAll").addEventListener("click", () => {
  pokemon.forEach((item) => selectedIds.add(item.id));
  renderChooser();
  renderPreview();
});

document.getElementById("selectNew").addEventListener("click", () => {
  pokemon.filter((item) => item.new).forEach((item) => selectedIds.add(item.id));
  renderChooser();
  renderPreview();
});

document.getElementById("clearAll").addEventListener("click", () => {
  selectedIds.clear();
  renderChooser();
  renderPreview();
});

document.querySelectorAll("[data-filter]").forEach((button) => button.addEventListener("click", () => {
  currentFilter = button.dataset.filter;
  document.querySelectorAll("[data-filter]").forEach((item) => item.classList.toggle("active", item === button));
  renderChooser();
}));

function startPrint() {
  if (selectedIds.size === 0) {
    window.alert("Bitte wähle zuerst mindestens ein Pokémon aus.");
    return;
  }
  window.print();
}

document.getElementById("printSelected").addEventListener("click", startPrint);
document.getElementById("printSelectedBottom").addEventListener("click", startPrint);

renderChooser();
renderPreview();
</script>
</body>
</html>
"""


def build_html(entries: list[dict], generated_at: str) -> str:
    active_entries = [
        {
            "id": entry["id"],
            "name": entry["anzeigename"],
            "file": normalize_rel(entry["datei"]),
            "new": bool(entry.get("neu")),
        }
        for entry in entries
        if entry.get("status") == "aktiv"
    ]
    return (
        HTML_TEMPLATE.replace("__DATA__", safe_json_for_script(active_entries))
        .replace("__GENERATED_AT__", generated_at)
    )


def archive_existing_output(path: Path) -> Path | None:
    if not path.exists():
        return None
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = ARCHIVE_DIR / f"{path.stem}-{timestamp}{path.suffix}"
    suffix = 2
    while target.exists():
        target = ARCHIVE_DIR / f"{path.stem}-{timestamp}-v{suffix}{path.suffix}"
        suffix += 1
    shutil.copy2(path, target)
    return target


def collect_current_files(source: Path) -> list[dict]:
    records = []
    for path in sorted(source.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if not path.is_file() or path.suffix.casefold() not in SUPPORTED_EXTENSIONS:
            continue
        relative = (Path(source.name) / path.relative_to(source)).as_posix()
        records.append(
            {
                "path": path,
                "datei": relative,
                "sha256": file_hash(path),
                "format": path.suffix.casefold().lstrip("."),
            }
        )
    return records


def merge_entries(existing: list[dict], current: list[dict]) -> tuple[list[dict], list[str], list[str]]:
    bootstrap = not existing
    existing_by_path = {
        normalize_rel(item["datei"]).casefold(): item for item in existing
    }
    existing_by_hash: dict[str, list[dict]] = {}
    for item in existing:
        if item.get("sha256"):
            existing_by_hash.setdefault(item["sha256"], []).append(item)

    by_hash: dict[str, list[dict]] = {}
    for record in current:
        by_hash.setdefault(record["sha256"], []).append(record)

    canonical_path_by_hash: dict[str, str] = {}
    for digest, records in by_hash.items():
        existing_paths = {
            normalize_rel(item["datei"]).casefold()
            for item in existing_by_hash.get(digest, [])
        }
        matching = [
            record for record in records
            if record["datei"].casefold() in existing_paths
        ]
        candidates = matching or records
        canonical_path_by_hash[digest] = min(
            candidates,
            key=lambda record: (
                EXTENSION_PRIORITY.get("." + record["format"], 99),
                record["datei"].casefold(),
            ),
        )["datei"]

    used_existing_ids: set[str] = set()
    used_ids = {item["id"] for item in existing if item.get("id")}
    max_order = max(
        (int(item.get("reihenfolge", 0) or 0) for item in existing),
        default=0,
    )
    merged: list[dict] = []
    duplicate_reports: list[str] = []
    new_reports: list[str] = []
    canonical_ids: dict[str, str] = {}

    def find_existing(record: dict) -> dict | None:
        direct = existing_by_path.get(record["datei"].casefold())
        if direct is not None and direct["id"] not in used_existing_ids:
            return direct
        for candidate in existing_by_hash.get(record["sha256"], []):
            if candidate["id"] not in used_existing_ids:
                return candidate
        return None

    ordered_current = sorted(
        current,
        key=lambda record: (
            record["datei"].casefold()
            != canonical_path_by_hash[record["sha256"]].casefold(),
            record["datei"].casefold(),
        ),
    )

    for record in ordered_current:
        is_duplicate = (
            record["datei"].casefold()
            != canonical_path_by_hash[record["sha256"]].casefold()
        )
        old = find_existing(record)
        if old is None:
            max_order += 10
            name = display_name_from_path(record["path"])
            old = {
                "id": unique_id(name, used_ids),
                "anzeigename": name,
                "datei": record["datei"],
                "status": "aktiv",
                "neu": not bootstrap,
                "reihenfolge": max_order,
                "sha256": record["sha256"],
                "duplikat_von": "",
            }
            used_ids.add(old["id"])
            if not bootstrap:
                new_reports.append(record["datei"])
        else:
            old = dict(old)
            used_existing_ids.add(old["id"])
            old_path = normalize_rel(old.get("datei", ""))
            if old_path.casefold() != record["datei"].casefold() and is_automatic_name(old):
                old["anzeigename"] = display_name_from_path(record["path"])
            if old.get("sha256") and old["sha256"] != record["sha256"]:
                old["neu"] = True
            old["datei"] = record["datei"]
            old["sha256"] = record["sha256"]

        old["format"] = record["format"]
        old["quelle"] = "S1"
        if is_duplicate:
            canonical_id = canonical_ids.get(record["sha256"], "")
            old["status"] = "dubletten"
            old["neu"] = False
            old["duplikat_von"] = canonical_id
            duplicate_reports.append(f"{record['datei']} -> {canonical_id}")
        else:
            old["status"] = "aktiv"
            old["duplikat_von"] = ""
            canonical_ids[record["sha256"]] = old["id"]
        merged.append(old)

    current_paths = {record["datei"].casefold() for record in current}
    for old in existing:
        if old["id"] in used_existing_ids:
            continue
        if normalize_rel(old["datei"]).casefold() not in current_paths:
            missing = dict(old)
            missing["status"] = "fehlt"
            missing["neu"] = False
            missing["duplikat_von"] = ""
            merged.append(missing)

    merged.sort(
        key=lambda item: (
            int(item.get("reihenfolge", 0) or 0),
            item["anzeigename"].casefold(),
        )
    )
    return merged, duplicate_reports, new_reports


def write_outputs(entries: list[dict], source: Path) -> tuple[Path | None, str]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "quelle": "S1",
        "erstellt": generated_at,
        "eintraege": entries,
    }

    # Build all three outputs before replacing any existing file. This keeps
    # the previous, usable state intact when a write or archive operation
    # fails halfway through an update.
    outputs = {
        INDEX_MD: format_markdown(entries, generated_at, source),
        INDEX_JSON: json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        OUTPUT_HTML: build_html(entries, generated_at),
    }
    transaction_dir = Path(tempfile.mkdtemp(prefix=".generator-tmp-", dir=PROJECT_ROOT))
    old_dir = transaction_dir / "old"
    temporary_files: dict[Path, Path] = {}
    existed: dict[Path, bool] = {}
    archived: Path | None = None
    replaced: list[Path] = []
    try:
        for destination, content in outputs.items():
            destination.parent.mkdir(parents=True, exist_ok=True)
            existed[destination] = destination.is_file()
            if existed[destination]:
                old_path = old_dir / destination.relative_to(PROJECT_ROOT)
                old_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(destination, old_path)
            temporary = transaction_dir / "new" / destination.relative_to(PROJECT_ROOT)
            temporary.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(content, encoding="utf-8", newline="\n")
            temporary_files[destination] = temporary

        archived = archive_existing_output(OUTPUT_HTML)
        for destination, temporary in temporary_files.items():
            os.replace(temporary, destination)
            replaced.append(destination)
    except Exception:
        for destination in reversed(replaced):
            old_path = old_dir / destination.relative_to(PROJECT_ROOT)
            try:
                if existed.get(destination) and old_path.is_file():
                    os.replace(old_path, destination)
                elif destination.exists():
                    destination.unlink()
            except OSError:
                # Preserve the original exception while leaving a clear
                # trace in the next integrity check.
                pass
        raise
    finally:
        shutil.rmtree(transaction_dir, ignore_errors=True)
    return archived, generated_at


def update_project(
    project_root: Path | None = None,
    source: Path | None = None,
) -> dict:
    """Update one Pokémon project and return a machine-readable result."""
    if project_root is not None:
        configure_project(project_root)

    source_path = (source or DEFAULT_SOURCE).expanduser()
    if not source_path.is_absolute():
        source_path = PROJECT_ROOT / source_path
    source_path = source_path.resolve()
    if not source_path.is_dir():
        raise FileNotFoundError(f"Quellordner nicht gefunden: {source_path}")

    current = collect_current_files(source_path)
    if not current:
        raise ValueError(
            f"Keine unterstützten Bilddateien in {source_path}"
        )

    existing = parse_index(INDEX_MD)
    entries, duplicate_reports, new_reports = merge_entries(existing, current)
    archived, generated_at = write_outputs(entries, source_path)
    active = [entry for entry in entries if entry.get("status") == "aktiv"]
    new_active = [entry for entry in active if entry.get("neu")]
    missing = [entry for entry in entries if entry.get("status") == "fehlt"]

    return {
        "source": str(source_path),
        "image_count": len(current),
        "active_count": len(active),
        "new_entry_count": len(new_reports),
        "new_active_count": len(new_active),
        "missing_count": len(missing),
        "duplicate_count": len(duplicate_reports),
        "new_entries": new_reports,
        "duplicates": duplicate_reports,
        "archived_html": str(archived) if archived else None,
        "generated_at": generated_at,
        "markdown": str(INDEX_MD),
        "json": str(INDEX_JSON),
        "html": str(OUTPUT_HTML),
    }


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(
        description="Aktualisiert Pokémon-Index und Auswahl-HTML aus S1."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Projektordner, standardmäßig der übergeordnete Ordner dieses Skripts",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Bildquelle, standardmäßig S1",
    )
    args = parser.parse_args()
    try:
        result = update_project(args.project_root, args.source)
    except (FileNotFoundError, ValueError) as error:
        print(f"FEHLER: {error}", file=sys.stderr)
        return 2

    print(f"Quelle: {result['source']}")
    print(f"Bilddateien erkannt: {result['image_count']}")
    print(f"Aktive Kacheln: {result['active_count']}")
    print(f"Neue Einträge: {result['new_entry_count']}")
    print(f"Neue/zu prüfende Kacheln: {result['new_active_count']}")
    print(f"Fehlende frühere Dateien: {result['missing_count']}")
    print(f"Exakte Dubletten ausgeblendet: {result['duplicate_count']}")
    for item in result["new_entries"]:
        print(f"  NEU: {item}")
    for item in result["duplicates"]:
        print(f"  DUBLETTE: {item}")
    if result["archived_html"]:
        print(f"Vorherige HTML archiviert: {result['archived_html']}")
    print(f"Markdown: {result['markdown']}")
    print(f"JSON: {result['json']}")
    print(f"HTML: {result['html']}")
    print(f"Aktualisiert: {result['generated_at']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
