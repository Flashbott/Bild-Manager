"""Local Pokémon Manager for importing images and updating the print selection."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import shutil
import sys
import threading
import time
import traceback
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

try:
    from PIL import Image, ImageOps, ImageTk
except ImportError as error:  # pragma: no cover - packaged builds include Pillow
    raise RuntimeError(
        "Pillow fehlt. Die Pokémon-Manager-App benötigt Pillow für Bildprüfung und Vorschauen."
    ) from error

from pokemon_engine import update_s1
from pokemon_backup import (
    BackupInfo,
    create_backup,
    format_backup_size,
    list_backups,
    prune_backups,
    restore_backup,
)
from pokemon_security import AdminPinManager


APP_NAME = "PokemonManager"
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
DEFAULT_LANGUAGE = "de"
LANGUAGE_LABELS = {"de": "Deutsch", "en": "English"}
CONFIG_SCHEMA_VERSION = 2
BACKUP_KEEP = 5
ADMIN_SESSION_SECONDS = 15 * 60


def application_version() -> str:
    candidates = []
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        candidates.append(Path(bundle_root) / "VERSION.json")
    candidates.append(Path(__file__).resolve().parents[1] / "VERSION.json")
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            version = str(data.get("app_version", "")).strip()
            if version:
                return version
        except (OSError, ValueError, TypeError):
            continue
    return "0.3.0"


APP_VERSION = application_version()

TRANSLATIONS = {
    "de": {
        "window_title": "Pokémon-Manager",
        "subtitle": "So geht es:\n1. Bilder auswählen – Downloads öffnen, Bilder markieren und „Öffnen“ klicken. Die App übernimmt die Bilder automatisch.\n2. Druckauswahl aktualisieren – die neue Liste wird erstellt.\n3. Auswahlseite öffnen – dort gewünschte Bilder anklicken.",
        "language": "Sprache:",
        "data_storage": "Arbeitsordner",
        "project_folder": "Arbeitsordner auswählen",
        "folder_dialog_title": "Arbeitsordner auswählen – Bilder und Druckauswahl werden hier gespeichert",
        "working_folder": "Arbeitsordner:",
        "working_folder_missing": "Noch nicht ausgewählt",
        "working_folder_required": "Bitte zuerst einen Arbeitsordner auswählen.",
        "change": "Ändern …",
        "open_input": "Eingangsordner öffnen",
        "import_check": "Importprüfung",
        "preview": "Bildvorschau",
        "preview_empty": "Wähle eine Datei aus der Importliste.",
        "no_preview": "Keine Vorschau verfügbar.",
        "status_heading": "Status",
        "file_heading": "Datei",
        "size_heading": "Größe",
        "format_heading": "Format",
        "target_heading": "Ziel",
        "add_files": "Bilder auswählen …",
        "remove": "Aus Liste entfernen",
        "clear": "Importliste leeren",
        "copy_s1": "Automatische Übernahme",
        "update_s1": "Druckauswahl aktualisieren",
        "open_selection": "Auswahlseite öffnen",
        "open_log": "Protokoll öffnen",
        "open_manual": "Anleitung öffnen",
        "settings": "⚙",
        "settings_title": "Einstellungen und Verwaltung",
        "settings_intro": "Hier findest du den Arbeitsordner, Sicherungen und die geschützte Administration. Der normale Bildimport bleibt im Hauptfenster.",
        "settings_folder": "Arbeitsordner ändern …",
        "settings_close": "Schließen",
        "backup_heading": "Sicherungen und Administration",
        "create_backup": "Sicherung erstellen",
        "restore_backup": "Wiederherstellen …",
        "administration": "Administration …",
        "backup_created": "Sicherung erstellt: {count} Datei(en), {size}",
        "backup_created_title": "Sicherung erstellt",
        "backup_failed_title": "Sicherung fehlgeschlagen",
        "backup_failed": "Die Sicherung wurde nicht erstellt. Es wurden keine Projektdaten geändert.\n\n{error}",
        "restore_title": "Sicherung wiederherstellen",
        "restore_choose": "Wähle eine Sicherung aus. Die aktuelle Datenlage wird vorher automatisch gesichert.",
        "restore_empty": "Es sind noch keine gültigen Sicherungen vorhanden.",
        "restore_confirm": "Sicherung vom {created} mit dem Anlass „{reason}“ wiederherstellen?\n\nDie aktuelle Datenlage wird vorher gesichert.",
        "restore_success_title": "Sicherung wiederhergestellt",
        "restore_success": "Die Sicherung vom {created} wurde wiederhergestellt.",
        "restore_failed_title": "Wiederherstellung fehlgeschlagen",
        "restore_failed": "Die Wiederherstellung wurde abgebrochen. Eine vorherige Sicherung bleibt erhalten.\n\n{error}",
        "restore_time": "Zeitpunkt",
        "restore_reason": "Anlass",
        "restore_files": "Dateien",
        "restore_size": "Größe",
        "restore_action": "Sicherung wiederherstellen",
        "cancel": "Abbrechen",
        "progress": "Vorgang läuft …",
        "admin_setup_title": "Administrator-PIN einrichten",
        "admin_setup_question": "Für geschützte Aktionen wird eine vierstellige Administrator-PIN benötigt. Jetzt einrichten?",
        "admin_setup_intro": "Diese PIN gilt nur für den Pokémon-Manager und wird nicht im Klartext gespeichert. Die normale Bildauswahl bleibt ohne PIN nutzbar.",
        "admin_enter": "Neue vierstellige Administrator-PIN:",
        "admin_repeat": "Administrator-PIN wiederholen:",
        "admin_pin_error": "Die PIN muss genau vier Ziffern enthalten.",
        "admin_pin_mismatch": "Die beiden PIN-Eingaben stimmen nicht überein.",
        "admin_pin_saved": "Administrator-PIN wurde gespeichert.",
        "admin_configured": "Administrator-PIN ist eingerichtet.",
        "admin_not_configured": "Administrator-PIN ist noch nicht eingerichtet.",
        "admin_required": "Für diese Aktion ist die Administrator-PIN erforderlich.",
        "admin_verify_title": "Administrator-PIN",
        "admin_change_title": "Administrator-PIN ändern",
        "admin_manage_info": "Status: {status}\n\nDie PIN schützt nur sensible Verwaltungsaktionen. Änderungen werden lokal für dieses Windows-Benutzerkonto gespeichert.",
        "admin_status_configured": "eingerichtet",
        "admin_status_missing": "noch nicht eingerichtet",
        "admin_setup_button": "PIN einrichten",
        "admin_change_button": "PIN / App-Passwort ändern",
        "admin_close_button": "Schließen",
        "admin_auth_failed": "Authentifizierung fehlgeschlagen",
        "owner_setup_hint": "Bitte richte vor der Übergabe an Julian einmalig eine Administrator-PIN ein.",
        "operation_failed_title": "Vorgang fehlgeschlagen",
        "manual_missing_title": "Anleitung fehlt",
        "manual_missing": "Die Anleitung wurde im Arbeitsordner nicht gefunden.",
        "app_version": "Version {version}",
        "ready_sentence": "Bereit.",
        "language_changed": "Sprache geändert: {language}",
        "info": "Bilddateien im Arbeitsbestand: {count} · Einstellungen werden automatisch gespeichert.",
        "first_run_title": "Arbeitsordner auswählen",
        "first_run_question": "Bitte wähle jetzt einen Arbeitsordner aus. Dort speichert der Pokémon-Manager deine Bilddateien, die Druckauswahl und automatische Sicherungen. Du kannst einen bestehenden Ordner wählen oder einen neuen Ordner anlegen.",
        "changed": "Arbeitsordner geändert.",
        "no_new_files": "Keine neuen Dateien ausgewählt.",
        "files_checked": "{count} Datei(en) geprüft. Bereit zur Bestätigung.",
        "removed": "Aus Importliste entfernt: {name}",
        "clear_title": "Importliste leeren",
        "clear_question": "Alle geprüften Dateien aus der Liste entfernen?",
        "cleared": "Importliste geleert.",
        "no_import_title": "Keine Übernahme",
        "no_import": "Es gibt keine gültigen, neuen Dateien zur Übernahme.",
        "copied_status": "{count} Datei(en) in den Arbeitsbestand übernommen.",
        "copy_error_title": "Übernahme mit Fehlern",
        "copy_done_title": "Übernahme abgeschlossen",
        "copy_done": "{count} Datei(en) wurden in den Arbeitsbestand kopiert.",
        "update_failed_status": "Aktualisierung der Druckauswahl fehlgeschlagen: {error}",
        "update_failed_title": "Aktualisierung der Druckauswahl fehlgeschlagen",
        "updated_status": "Druckauswahl aktualisiert: {active} aktive Kacheln, {new} neue Einträge.",
        "updated_title": "Druckauswahl aktualisiert",
        "updated_info": "Aktive Kacheln: {active}\nNeue Einträge: {new}\nFehlende Dateien: {missing}\n\nDie Auswahlseite kann jetzt geöffnet werden.",
        "selection_missing_title": "Auswahlseite fehlt",
        "selection_missing": "Bitte zuerst „Druckauswahl aktualisieren“ ausführen.",
        "file_dialog_images": "Bilddateien",
        "file_dialog_all": "Alle Dateien",
        "unsupported_format": "Nicht unterstütztes Bildformat",
        "ready": "Bereit",
        "already_exists": "Bereits vorhanden: {name}",
        "selected_twice": "Doppelt ausgewählt: {name}",
        "copied_to_s1": "In den Arbeitsbestand kopiert: {name}",
        "file_details": "Datei: {name}\nStatus: {status}\nGröße: {size}\nMaße: {dimensions}\nHinweis: {message}",
        "unknown": "unbekannt",
        "empty_value": "–",
        "status_ready": "Bereit",
        "status_duplicate": "Duplikat",
        "status_invalid": "Ungültig",
        "status_error": "Fehler",
        "status_imported": "Übernommen",
    },
    "en": {
        "window_title": "Pokémon Manager",
        "subtitle": "How it works:\n1. Choose images – open Downloads, select images and click “Open”. The app adds the images automatically.\n2. Update print selection – the new list is created.\n3. Open selection page – click the images you want.",
        "language": "Language:",
        "data_storage": "Working folder",
        "project_folder": "Choose working folder",
        "folder_dialog_title": "Choose working folder – images and print selection are saved here",
        "working_folder": "Working folder:",
        "working_folder_missing": "Not selected yet",
        "working_folder_required": "Please choose a working folder first.",
        "change": "Change …",
        "open_input": "Open input folder",
        "import_check": "Import review",
        "preview": "Image preview",
        "preview_empty": "Select a file from the import list.",
        "no_preview": "Preview unavailable.",
        "status_heading": "Status",
        "file_heading": "File",
        "size_heading": "Size",
        "format_heading": "Format",
        "target_heading": "Target",
        "add_files": "Choose images …",
        "remove": "Remove from list",
        "clear": "Clear import list",
        "copy_s1": "Automatic import",
        "update_s1": "Update print selection",
        "open_selection": "Open selection page",
        "open_log": "Open log",
        "open_manual": "Open guide",
        "settings": "⚙",
        "settings_title": "Settings and administration",
        "settings_intro": "This area contains the working folder, backups and protected administration. Normal image import stays in the main window.",
        "settings_folder": "Change working folder …",
        "settings_close": "Close",
        "backup_heading": "Backups and administration",
        "create_backup": "Create backup",
        "restore_backup": "Restore …",
        "administration": "Administration …",
        "backup_created": "Backup created: {count} file(s), {size}",
        "backup_created_title": "Backup created",
        "backup_failed_title": "Backup failed",
        "backup_failed": "The backup was not created. No project data was changed.\n\n{error}",
        "restore_title": "Restore backup",
        "restore_choose": "Choose a backup. The current data is backed up automatically first.",
        "restore_empty": "No valid backups are available yet.",
        "restore_confirm": "Restore the backup from {created} with reason “{reason}”?\n\nThe current data will be backed up first.",
        "restore_success_title": "Backup restored",
        "restore_success": "The backup from {created} was restored.",
        "restore_failed_title": "Restore failed",
        "restore_failed": "The restore was cancelled. A previous backup remains available.\n\n{error}",
        "restore_time": "Time",
        "restore_reason": "Reason",
        "restore_files": "Files",
        "restore_size": "Size",
        "restore_action": "Restore backup",
        "cancel": "Cancel",
        "progress": "Operation in progress …",
        "admin_setup_title": "Set up administrator PIN",
        "admin_setup_question": "A four-digit administrator PIN is required for protected actions. Set it up now?",
        "admin_setup_intro": "This PIN is only for Pokémon Manager and is not stored in plain text. Normal image selection remains available without a PIN.",
        "admin_enter": "New four-digit administrator PIN:",
        "admin_repeat": "Repeat administrator PIN:",
        "admin_pin_error": "The PIN must contain exactly four digits.",
        "admin_pin_mismatch": "The two PIN entries do not match.",
        "admin_pin_saved": "Administrator PIN saved.",
        "admin_configured": "Administrator PIN is configured.",
        "admin_not_configured": "Administrator PIN is not configured yet.",
        "admin_required": "This action requires the administrator PIN.",
        "admin_verify_title": "Administrator PIN",
        "admin_change_title": "Change administrator PIN",
        "admin_manage_info": "Status: {status}\n\nThe PIN protects sensitive administration actions only. Changes are stored locally for this Windows user account.",
        "admin_status_configured": "configured",
        "admin_status_missing": "not configured",
        "admin_setup_button": "Set up PIN",
        "admin_change_button": "Change PIN / app password",
        "admin_close_button": "Close",
        "admin_auth_failed": "Authentication failed",
        "owner_setup_hint": "Set up an administrator PIN once before handing the app to Julian.",
        "operation_failed_title": "Operation failed",
        "manual_missing_title": "Guide missing",
        "manual_missing": "The guide was not found in the working folder.",
        "app_version": "Version {version}",
        "ready_sentence": "Ready.",
        "language_changed": "Language changed: {language}",
        "info": "Images in working collection: {count} · Settings are saved automatically.",
        "first_run_title": "Choose working folder",
        "first_run_question": "Please choose a working folder now. Pokémon Manager stores your images, print selection and automatic backups there. You can choose an existing folder or create a new one.",
        "changed": "Working folder changed.",
        "no_new_files": "No new files selected.",
        "files_checked": "{count} file(s) checked. Ready for confirmation.",
        "removed": "Removed from import list: {name}",
        "clear_title": "Clear import list",
        "clear_question": "Remove all checked files from the list?",
        "cleared": "Import list cleared.",
        "no_import_title": "Nothing to copy",
        "no_import": "There are no valid new files to copy.",
        "copied_status": "{count} file(s) added to the working collection.",
        "copy_error_title": "Copy completed with errors",
        "copy_done_title": "Copy completed",
        "copy_done": "{count} file(s) were added to the working collection.",
        "update_failed_status": "Updating the print selection failed: {error}",
        "update_failed_title": "Updating the print selection failed",
        "updated_status": "Print selection updated: {active} active cards, {new} new entries.",
        "updated_title": "Print selection updated",
        "updated_info": "Active cards: {active}\nNew entries: {new}\nMissing files: {missing}\n\nThe selection page can now be opened.",
        "selection_missing_title": "Selection page missing",
        "selection_missing": "Please run “Update print selection” first.",
        "file_dialog_images": "Image files",
        "file_dialog_all": "All files",
        "unsupported_format": "Unsupported image format",
        "ready": "Ready",
        "already_exists": "Already present: {name}",
        "selected_twice": "Selected twice: {name}",
        "copied_to_s1": "Added to working collection: {name}",
        "file_details": "File: {name}\nStatus: {status}\nSize: {size}\nDimensions: {dimensions}\nNote: {message}",
        "unknown": "unknown",
        "empty_value": "–",
        "status_ready": "Ready",
        "status_duplicate": "Duplicate",
        "status_invalid": "Invalid",
        "status_error": "Error",
        "status_imported": "Imported",
    },
}


def normalize_language(value: object) -> str:
    language = str(value).casefold() if value is not None else DEFAULT_LANGUAGE
    return language if language in TRANSLATIONS else DEFAULT_LANGUAGE


def translate(locale: str, key: str, **values: object) -> str:
    language = normalize_language(locale)
    template = TRANSLATIONS[language].get(key, TRANSLATIONS[DEFAULT_LANGUAGE][key])
    return template.format(**values)


@dataclass
class ImportItem:
    source: Path
    status: str
    size: int
    sha256: str = ""
    message: str = ""
    destination: Path | None = None
    dimensions: str = ""


def app_config_path() -> Path:
    return app_data_dir() / "config.json"


def app_data_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    return base / APP_NAME


def admin_policy_path() -> Path:
    return app_data_dir() / "admin-policy.json"


def load_config() -> tuple[Path | None, bool, str]:
    path = app_config_path()
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            raw_configured = data.get("project_root")
            language = normalize_language(data.get("language"))
            if raw_configured:
                configured = Path(str(raw_configured)).expanduser()
                return configured, True, language
        except (OSError, ValueError, TypeError):
            pass
    return None, False, DEFAULT_LANGUAGE


def load_project_root() -> tuple[Path | None, bool]:
    project_root, has_config, _language = load_config()
    return project_root, has_config


def save_settings(project_root: Path, language: str) -> None:
    path = app_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "config_schema_version": CONFIG_SCHEMA_VERSION,
        "project_root": str(project_root),
        "language": normalize_language(language),
    }
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def save_project_root(project_root: Path) -> None:
    _configured_root, _has_config, language = load_config()
    save_settings(project_root, language)


def ensure_layout(project_root: Path) -> None:
    for relative in (
        "Eingang",
        "S1",
        "Index",
        "Archiv",
        "Protokolle",
        "Hilfsdateien",
        "Hilfsdateien/Archiv",
        "Backups",
    ):
        (project_root / relative).mkdir(parents=True, exist_ok=True)


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def format_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def validate_image(path: Path, language: str = DEFAULT_LANGUAGE) -> tuple[bool, str, str]:
    if path.suffix.casefold() not in SUPPORTED_EXTENSIONS:
        return False, translate(language, "unsupported_format"), ""
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            dimensions = f"{image.width} × {image.height} px"
        return True, translate(language, "ready"), dimensions
    except Exception as error:  # Pillow raises several format-specific errors.
        prefix = "Bild nicht lesbar" if normalize_language(language) == "de" else "Image cannot be read"
        return False, f"{prefix}: {error}", ""


def existing_hashes(s1_dir: Path) -> dict[str, Path]:
    hashes: dict[str, Path] = {}
    if not s1_dir.is_dir():
        return hashes
    for path in s1_dir.rglob("*"):
        if path.is_file() and path.suffix.casefold() in SUPPORTED_EXTENSIONS:
            try:
                hashes.setdefault(hash_file(path), path)
            except OSError:
                continue
    return hashes


def next_destination(source: Path, s1_dir: Path, reserved: set[str]) -> Path:
    candidate = s1_dir / source.name
    stem = source.stem
    suffix = source.suffix
    number = 2
    while candidate.exists() or str(candidate).casefold() in reserved:
        candidate = s1_dir / f"{stem}-{number}{suffix}"
        number += 1
    reserved.add(str(candidate).casefold())
    return candidate


def prepare_import_items(
    paths: list[Path], s1_dir: Path, language: str = DEFAULT_LANGUAGE
) -> list[ImportItem]:
    known_hashes = existing_hashes(s1_dir)
    reserved: set[str] = set()
    planned_hashes: dict[str, Path] = {}
    items: list[ImportItem] = []
    for source in paths:
        try:
            size = source.stat().st_size
        except OSError as error:
            items.append(ImportItem(source, "Fehler", 0, message=str(error)))
            continue
        valid, message, dimensions = validate_image(source, language)
        if not valid:
            items.append(
                ImportItem(source, "Ungültig", size, message=message, dimensions=dimensions)
            )
            continue
        try:
            digest = hash_file(source)
        except OSError as error:
            items.append(ImportItem(source, "Fehler", size, message=str(error)))
            continue
        if digest in known_hashes:
            items.append(
                ImportItem(
                    source,
                    "Duplikat",
                    size,
                    sha256=digest,
                    message=translate(
                        language, "already_exists", name=known_hashes[digest].name
                    ),
                    destination=known_hashes[digest],
                    dimensions=dimensions,
                )
            )
            continue
        if digest in planned_hashes:
            items.append(
                ImportItem(
                    source,
                    "Duplikat",
                    size,
                    sha256=digest,
                    message=translate(
                        language, "selected_twice", name=planned_hashes[digest].name
                    ),
                    destination=planned_hashes[digest],
                    dimensions=dimensions,
                )
            )
            continue
        destination = next_destination(source, s1_dir, reserved)
        planned_hashes[digest] = destination
        items.append(
            ImportItem(
                source,
                "Bereit",
                size,
                sha256=digest,
                message=message,
                destination=destination,
                dimensions=dimensions,
            )
        )
    return items


def open_path(path: Path) -> None:
    if hasattr(os, "startfile"):
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:  # pragma: no cover - Windows is the supported target.
        webbrowser.open(path.as_uri())


class PokemonManagerApp(tk.Tk):
    def __init__(self, initial_project_root: Path | None = None) -> None:
        super().__init__()
        self.geometry("1120x760")
        self.minsize(900, 620)
        configured_root, _has_config, self.language = load_config()
        self.project_root = configured_root or Path.home()
        self.project_configured = configured_root is not None
        if initial_project_root is not None:
            self.project_root = initial_project_root.expanduser().resolve()
            self.project_configured = True
        self.items: list[ImportItem] = []
        self.preview_image: ImageTk.PhotoImage | None = None
        self.config_path = app_config_path()
        self.admin_pin = AdminPinManager(admin_policy_path())
        self.admin_session_until = 0.0
        self.operation_running = False
        self.operation_queue: queue.Queue[tuple[str, object]] | None = None
        if self.project_configured:
            ensure_layout(self.project_root)
            save_settings(self.project_root, self.language)
        self._build_styles()
        self._build_ui()
        self.apply_language()
        self.refresh_project_info()
        self._set_operation_state(False)
        if not self.project_configured and initial_project_root is None:
            self.after(250, self.first_run_choice)
        if self.project_configured and not self.admin_pin.configured:
            self.after(500, self.offer_admin_setup)

    def t(self, key: str, **values: object) -> str:
        return translate(self.language, key, **values)

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", foreground="#526176")
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=0)
        root.rowconfigure(3, weight=1)

        self.title_label = ttk.Label(root, style="Title.TLabel")
        self.title_label.grid(row=0, column=0, sticky="w")

        language_frame = ttk.Frame(root)
        language_frame.grid(row=0, column=1, sticky="e")
        self.settings_button = ttk.Button(
            language_frame, command=self.open_settings, width=3
        )
        self.settings_button.pack(side="left", padx=(0, 8))
        self.language_label = ttk.Label(language_frame)
        self.language_label.pack(side="left", padx=(0, 6))
        self.language_var = tk.StringVar()
        self.language_combo = ttk.Combobox(
            language_frame,
            textvariable=self.language_var,
            values=list(LANGUAGE_LABELS.values()),
            state="readonly",
            width=12,
        )
        self.language_combo.pack(side="left")
        self.language_combo.bind("<<ComboboxSelected>>", self.on_language_change)

        self.subtitle_label = ttk.Label(
            root, style="Subtitle.TLabel", justify="left", wraplength=900
        )
        self.subtitle_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 14))

        self.path_frame = ttk.LabelFrame(root, padding=10)
        self.path_frame.grid(row=2, column=0, columnspan=2, sticky="new", pady=(0, 12))
        self.path_frame.columnconfigure(1, weight=1)
        self.path_var = tk.StringVar()
        self.project_label = ttk.Label(self.path_frame)
        self.project_label.grid(row=0, column=0, sticky="w")
        ttk.Label(self.path_frame, textvariable=self.path_var).grid(
            row=0, column=1, sticky="ew", padx=8
        )
        self.change_project_button = ttk.Button(
            self.path_frame, command=self.change_project
        )
        self.change_project_button.grid(
            row=0, column=2, padx=(4, 0)
        )
        self.change_project_button.grid_remove()
        self.open_input_button = ttk.Button(
            self.path_frame, command=self.open_input_folder
        )
        self.open_input_button.grid(
            row=0, column=3, padx=(4, 0)
        )
        self.open_input_button.grid_remove()
        self.info_var = tk.StringVar()
        ttk.Label(
            self.path_frame, textvariable=self.info_var, style="Subtitle.TLabel"
        ).grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(8, 0)
        )

        work = ttk.Frame(root)
        work.grid(row=3, column=0, sticky="nsew")
        work.columnconfigure(0, weight=3)
        work.columnconfigure(1, weight=1)
        work.rowconfigure(0, weight=1)

        self.list_frame = ttk.LabelFrame(work, padding=8)
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.list_frame.columnconfigure(0, weight=1)
        self.list_frame.rowconfigure(0, weight=1)
        columns = ("status", "datei", "groesse", "format", "ziel")
        self.tree = ttk.Treeview(
            self.list_frame, columns=columns, show="headings", selectmode="browse"
        )
        self.tree_heading_keys = {
            "status": "status_heading",
            "datei": "file_heading",
            "groesse": "size_heading",
            "format": "format_heading",
            "ziel": "target_heading",
        }
        widths = {"status": 100, "datei": 260, "groesse": 95, "format": 75, "ziel": 250}
        for column in columns:
            self.tree.heading(column, text=self.t(self.tree_heading_keys[column]))
            self.tree.column(column, width=widths[column], anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.tag_configure("ready", foreground="#146c2e")
        self.tree.tag_configure("duplicate", foreground="#8a5a00")
        self.tree.tag_configure("invalid", foreground="#a11b1b")
        self.tree.tag_configure("imported", foreground="#2166d1")
        self.tree.bind("<<TreeviewSelect>>", self.show_selected_preview)

        self.preview_frame = ttk.LabelFrame(work, padding=12)
        self.preview_frame.grid(row=0, column=1, sticky="nsew")
        self.preview_frame.rowconfigure(0, weight=1)
        self.preview_frame.columnconfigure(0, weight=1)
        self.preview_label = ttk.Label(
            self.preview_frame,
            text=self.t("preview_empty"),
            anchor="center",
            justify="center",
        )
        self.preview_label.grid(row=0, column=0, sticky="nsew")
        self.preview_info = tk.StringVar()
        ttk.Label(self.preview_frame, textvariable=self.preview_info, justify="left").grid(
            row=1, column=0, sticky="ew", pady=(12, 0)
        )

        controls = ttk.Frame(root)
        controls.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        controls.columnconfigure(0, weight=1)
        left = ttk.Frame(controls)
        left.grid(row=0, column=0, sticky="w")
        self.add_files_button = ttk.Button(left, command=self.add_files)
        self.add_files_button.pack(
            side="left", padx=(0, 6)
        )
        self.remove_button = ttk.Button(left, command=self.remove_selected)
        self.remove_button.pack(
            side="left", padx=6
        )
        self.clear_button = ttk.Button(left, command=self.clear_items)
        self.clear_button.pack(
            side="left", padx=6
        )
        right = ttk.Frame(controls)
        right.grid(row=0, column=1, sticky="e")
        self.copy_button = ttk.Button(
            right,
            command=self.import_to_s1,
            style="Primary.TButton",
        )
        self.copy_button.pack(side="left", padx=6)
        self.copy_button.pack_forget()
        self.update_button = ttk.Button(
            right,
            command=self.update_s1,
            style="Primary.TButton",
        )
        self.update_button.pack(side="left", padx=6)
        self.selection_button = ttk.Button(
            right, command=self.open_selection
        )
        self.selection_button.pack(
            side="left", padx=6
        )
        self.log_button = ttk.Button(right, command=self.open_log)
        self.log_button.pack(
            side="left", padx=(6, 0)
        )
        self.log_button.pack_forget()
        self.management_frame = ttk.LabelFrame(root, padding=(10, 6))
        self.management_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.management_frame.grid_remove()
        self.management_frame.columnconfigure(1, weight=1)
        self.management_label = ttk.Label(self.management_frame, style="Subtitle.TLabel")
        self.management_label.grid(row=0, column=0, sticky="w", padx=(0, 12))
        management_buttons = ttk.Frame(self.management_frame)
        management_buttons.grid(row=0, column=1, sticky="e")
        self.backup_button = ttk.Button(
            management_buttons, command=self.create_manual_backup
        )
        self.backup_button.pack(side="left", padx=4)
        self.restore_button = ttk.Button(
            management_buttons, command=self.open_restore_dialog
        )
        self.restore_button.pack(side="left", padx=4)
        self.admin_button = ttk.Button(
            management_buttons, command=self.open_administration
        )
        self.admin_button.pack(side="left", padx=4)
        self.manual_button = ttk.Button(
            management_buttons, command=self.open_manual
        )
        self.manual_button.pack(side="left", padx=(4, 0))
        self.progress = ttk.Progressbar(root, mode="indeterminate", length=240)
        self.progress.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.progress.grid_remove()
        self.status_var = tk.StringVar(value=self.t("ready_sentence"))
        ttk.Label(root, textvariable=self.status_var, style="Subtitle.TLabel").grid(
            row=7, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )

    def status_text(self, status: str) -> str:
        status_keys = {
            "Bereit": "status_ready",
            "Duplikat": "status_duplicate",
            "Ungültig": "status_invalid",
            "Fehler": "status_error",
            "Übernommen": "status_imported",
        }
        key = status_keys.get(status)
        return self.t(key) if key else status

    def apply_language(self) -> None:
        selected = self.tree.selection() if hasattr(self, "tree") else ()
        selected_index = int(selected[0]) if selected else None

        self.title(self.t("window_title"))
        self.title_label.configure(text=self.t("window_title"))
        self.subtitle_label.configure(text=self.t("subtitle"))
        self.settings_button.configure(text=self.t("settings"))
        self.language_label.configure(text=self.t("language"))
        self.language_combo.configure(values=list(LANGUAGE_LABELS.values()))
        self.language_var.set(LANGUAGE_LABELS[self.language])
        self.path_frame.configure(text=self.t("data_storage"))
        self.project_label.configure(text=self.t("working_folder"))
        self.change_project_button.configure(text=self.t("change"))
        self.open_input_button.configure(text=self.t("open_input"))
        self.list_frame.configure(text=self.t("import_check"))
        self.preview_frame.configure(text=self.t("preview"))
        for column, key in self.tree_heading_keys.items():
            self.tree.heading(column, text=self.t(key))
        self.add_files_button.configure(text=self.t("add_files"))
        self.remove_button.configure(text=self.t("remove"))
        self.clear_button.configure(text=self.t("clear"))
        self.copy_button.configure(text=self.t("copy_s1"))
        self.update_button.configure(text=self.t("update_s1"))
        self.selection_button.configure(text=self.t("open_selection"))
        self.log_button.configure(text=self.t("open_log"))
        self.management_frame.configure(text=self.t("backup_heading"))
        self.management_label.configure(
            text=self.t("app_version", version=APP_VERSION)
        )
        self.backup_button.configure(text=self.t("create_backup"))
        self.restore_button.configure(text=self.t("restore_backup"))
        self.admin_button.configure(text=self.t("administration"))
        self.manual_button.configure(text=self.t("open_manual"))
        self.refresh_project_info()
        self.refresh_tree()

        if selected_index is not None and selected_index < len(self.items):
            self.tree.selection_set(str(selected_index))
            self.show_selected_preview()
        else:
            self.preview_label.configure(image="", text=self.t("preview_empty"))
            self.preview_info.set("")
            self.preview_image = None

    def on_language_change(self, _event: object = None) -> None:
        selected_label = self.language_combo.get()
        selected_language = next(
            (
                language
                for language, label in LANGUAGE_LABELS.items()
                if label == selected_label
            ),
            DEFAULT_LANGUAGE,
        )
        if selected_language == self.language:
            return
        self.language = selected_language
        if self.project_configured:
            save_settings(self.project_root, self.language)
        self.apply_language()
        self.set_status(
            self.t("language_changed", language=LANGUAGE_LABELS[self.language])
        )
        self.log_event("sprache_geaendert", sprache=self.language)

    def first_run_choice(self) -> None:
        self.set_status(self.t("working_folder_required"))
        self.change_project(require_admin=False)

    def refresh_project_info(self) -> None:
        if not self.project_configured:
            self.path_var.set(self.t("working_folder_missing"))
            self.info_var.set(self.t("working_folder_required"))
            return
        self.path_var.set(str(self.project_root))
        s1 = self.project_root / "S1"
        count = sum(
            1
            for path in s1.rglob("*")
            if path.is_file() and path.suffix.casefold() in SUPPORTED_EXTENSIONS
        ) if s1.exists() else 0
        self.info_var.set(self.t("info", count=count))

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def log_event(self, event: str, **data: object) -> None:
        if not self.project_configured:
            return
        try:
            log_path = self.project_root / "Protokolle" / "pokemon-manager.jsonl"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "zeitpunkt": datetime.now().astimezone().isoformat(timespec="seconds"),
                "ereignis": event,
                **data,
            }
            with log_path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def _set_operation_state(self, running: bool) -> None:
        self.operation_running = running
        buttons = (
            self.add_files_button,
            self.remove_button,
            self.clear_button,
            self.copy_button,
            self.update_button,
            self.selection_button,
            self.log_button,
            self.backup_button,
            self.restore_button,
            self.admin_button,
            self.manual_button,
            self.change_project_button,
            self.open_input_button,
        )
        state = "disabled" if running or not self.project_configured else "normal"
        for button in buttons:
            button.configure(state=state)
        if running:
            self.progress.grid()
            self.progress.start(10)
        else:
            self.progress.stop()
            self.progress.grid_remove()

    def _run_in_background(
        self,
        operation,
        on_success,
        on_error,
    ) -> None:
        if self.operation_running:
            return
        self._set_operation_state(True)
        self.set_status(self.t("progress"))
        result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.operation_queue = result_queue

        def worker() -> None:
            try:
                result_queue.put(("success", operation()))
            except Exception as error:  # Worker errors are reported on the UI thread.
                result_queue.put(("error", (error, traceback.format_exc())))

        threading.Thread(target=worker, name="pokemon-manager-operation", daemon=True).start()
        self.after(100, lambda: self._poll_background(result_queue, on_success, on_error))

    def _poll_background(self, result_queue, on_success, on_error) -> None:
        try:
            kind, payload = result_queue.get_nowait()
        except queue.Empty:
            self.after(100, lambda: self._poll_background(result_queue, on_success, on_error))
            return
        self.operation_queue = None
        self._set_operation_state(False)
        if kind == "success":
            on_success(payload)
        else:
            error, details = payload
            on_error(error, details)

    def _backup_config_snapshot(self) -> dict[str, object]:
        return {
            "config_schema_version": CONFIG_SCHEMA_VERSION,
            "project_root": str(self.project_root),
            "language": self.language,
        }

    def _backup_error(self, error: Exception, details: str) -> None:
        self.log_event("sicherung_fehler", fehler=str(error), traceback=details)
        self.set_status(self.t("backup_failed_title"))
        messagebox.showerror(
            self.t("backup_failed_title"),
            self.t("backup_failed", error=error),
            parent=self,
        )

    def _operation_error(self, error: Exception, details: str) -> None:
        self.log_event("vorgang_fehler", fehler=str(error), traceback=details)
        self.set_status(self.t("operation_failed_title"))
        messagebox.showerror(self.t("operation_failed_title"), str(error), parent=self)

    def offer_admin_setup(self) -> None:
        if self.admin_pin.configured or self.operation_running:
            return
        if not messagebox.askyesno(
            self.t("admin_setup_title"),
            self.t("admin_setup_question") + "\n\n" + self.t("owner_setup_hint"),
            parent=self,
        ):
            return
        self.set_new_admin_pin()

    def set_new_admin_pin(self) -> bool:
        title_key = "admin_change_title" if self.admin_pin.configured else "admin_setup_title"
        pin = simpledialog.askstring(
            self.t(title_key), self.t("admin_enter"), show="*", parent=self
        )
        if pin is None:
            return False
        if not self.admin_pin.validate_pin(pin):
            messagebox.showerror(self.t(title_key), self.t("admin_pin_error"), parent=self)
            return False
        repeated = simpledialog.askstring(
            self.t(title_key), self.t("admin_repeat"), show="*", parent=self
        )
        if repeated is None:
            return False
        if pin != repeated:
            messagebox.showerror(self.t(title_key), self.t("admin_pin_mismatch"), parent=self)
            return False
        try:
            self.admin_pin.set_pin(pin)
        except (OSError, ValueError) as error:
            messagebox.showerror(self.t(title_key), str(error), parent=self)
            return False
        self.admin_session_until = time.monotonic() + ADMIN_SESSION_SECONDS
        self.log_event("administrator_pin_gesetzt")
        messagebox.showinfo(self.t(title_key), self.t("admin_pin_saved"), parent=self)
        return True

    def require_admin(self, action: str) -> bool:
        if not self.admin_pin.configured:
            messagebox.showwarning(
                self.t("admin_verify_title"),
                self.t("admin_required") + "\n\n" + self.t("owner_setup_hint"),
                parent=self,
            )
            return False
        if time.monotonic() < self.admin_session_until:
            return True
        pin = simpledialog.askstring(
            self.t("admin_verify_title"),
            f"{self.t('admin_required')}\n{action}",
            show="*",
            parent=self,
        )
        if pin is None:
            return False
        valid, message = self.admin_pin.verify(pin)
        if not valid:
            messagebox.showerror(
                self.t("admin_auth_failed"), message, parent=self
            )
            return False
        self.admin_session_until = time.monotonic() + ADMIN_SESSION_SECONDS
        self.log_event("administrator_aktion_freigegeben", aktion=action)
        return True

    def open_administration(self) -> None:
        if not self.admin_pin.configured:
            if not self.set_new_admin_pin():
                return
        elif not self.require_admin(self.t("administration")):
            return

        dialog = tk.Toplevel(self)
        dialog.title(self.t("administration"))
        dialog.transient(self)
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill="both", expand=True)
        status_key = "admin_status_configured" if self.admin_pin.configured else "admin_status_missing"
        info = ttk.Label(
            frame,
            text=self.t("admin_manage_info", status=self.t(status_key)),
            justify="left",
        )
        info.pack(anchor="w", pady=(0, 14))
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x")
        ttk.Button(
            button_frame,
            text=self.t("admin_change_button"),
            command=lambda: (self.set_new_admin_pin(), dialog.destroy()),
        ).pack(side="left")
        ttk.Button(
            button_frame,
            text=self.t("admin_close_button"),
            command=dialog.destroy,
        ).pack(side="right")
        dialog.grab_set()

    def open_settings(self) -> None:
        if self.operation_running:
            return
        if not self.project_configured:
            self.change_project(require_admin=False)
            return
        dialog = tk.Toplevel(self)
        dialog.title(self.t("settings_title"))
        dialog.transient(self)
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(
            frame,
            text=self.t("settings_intro"),
            justify="left",
            wraplength=480,
        ).pack(anchor="w", pady=(0, 12))
        folder_box = ttk.LabelFrame(frame, text=self.t("data_storage"), padding=10)
        folder_box.pack(fill="x", pady=(0, 12))
        ttk.Label(folder_box, text=self.t("working_folder")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(folder_box, text=str(self.project_root), wraplength=360).grid(
            row=1, column=0, sticky="w", pady=(5, 0)
        )

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")

        def close_then(action) -> None:
            dialog.destroy()
            self.after_idle(action)

        actions = (
            (self.t("settings_folder"), self.change_project),
            (self.t("open_input"), self.open_input_folder),
            (self.t("create_backup"), self.create_manual_backup),
            (self.t("restore_backup"), self.open_restore_dialog),
            (self.t("administration"), self.open_administration),
            (self.t("open_log"), self.open_log),
            (self.t("open_manual"), self.open_manual),
        )
        for index, (label, action) in enumerate(actions):
            row, column = divmod(index, 2)
            ttk.Button(
                buttons,
                text=label,
                command=lambda action=action: close_then(action),
            ).grid(row=row, column=column, sticky="ew", padx=4, pady=4)
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)
        ttk.Button(
            frame, text=self.t("settings_close"), command=dialog.destroy
        ).pack(anchor="e", pady=(12, 0))
        dialog.grab_set()

    def change_project(self, require_admin: bool = True) -> None:
        if require_admin and self.admin_pin.configured and not self.require_admin(
            self.t("change")
        ):
            return
        selected = filedialog.askdirectory(
            title=self.t("folder_dialog_title"),
            initialdir=str(
                self.project_root
                if self.project_configured and self.project_root.is_dir()
                else Path.home()
            ),
            mustexist=False,
        )
        if not selected:
            if not self.project_configured:
                self.set_status(self.t("working_folder_required"))
            return
        self.project_root = Path(selected).expanduser().resolve()
        self.project_configured = True
        ensure_layout(self.project_root)
        save_settings(self.project_root, self.language)
        self.items.clear()
        self.refresh_tree()
        self.refresh_project_info()
        self.set_status(self.t("changed"))
        self.log_event("projektordner_geaendert", projektordner=str(self.project_root))
        self._set_operation_state(False)
        if not self.admin_pin.configured:
            self.after(250, self.offer_admin_setup)

    def open_input_folder(self) -> None:
        ensure_layout(self.project_root)
        open_path(self.project_root / "Eingang")

    def add_files(self) -> None:
        initial = self.project_root / "Eingang"
        downloads = Path.home() / "Downloads"
        if downloads.is_dir():
            initial = downloads
        selected = filedialog.askopenfilenames(
            title=self.t("add_files"),
            initialdir=str(initial),
            filetypes=[
                (
                    self.t("file_dialog_images"),
                    " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS)),
                ),
                (self.t("file_dialog_all"), "*.*"),
            ],
        )
        if not selected:
            return
        known_sources = {item.source.resolve().casefold() for item in self.items}
        paths = [Path(value).resolve() for value in selected]
        paths = [path for path in paths if str(path).casefold() not in known_sources]
        if not paths:
            self.set_status(self.t("no_new_files"))
            return
        ensure_layout(self.project_root)
        new_items = prepare_import_items(paths, self.project_root / "S1", self.language)
        self.items.extend(new_items)
        self.refresh_tree()
        self.set_status(self.t("files_checked", count=len(new_items)))
        self.log_event("dateien_geprueft", anzahl=len(new_items))
        self.import_to_s1(show_result=False)

    def refresh_tree(self) -> None:
        for child in self.tree.get_children():
            self.tree.delete(child)
        for index, item in enumerate(self.items):
            destination = item.destination.name if item.destination else self.t("empty_value")
            tag = {
                "Bereit": "ready",
                "Duplikat": "duplicate",
                "Ungültig": "invalid",
                "Fehler": "invalid",
                "Übernommen": "imported",
            }.get(item.status, "")
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    self.status_text(item.status),
                    item.source.name,
                    format_size(item.size),
                    item.source.suffix.casefold().lstrip("."),
                    destination,
                ),
                tags=(tag,),
            )

    def show_selected_preview(self, _event: object = None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item = self.items[int(selection[0])]
        try:
            with Image.open(item.source) as image:
                preview = image.convert("RGBA")
                preview.thumbnail((300, 300), getattr(Image, "Resampling", Image).LANCZOS)
                background = Image.new("RGBA", preview.size, "white")
                background.alpha_composite(preview)
                self.preview_image = ImageTk.PhotoImage(background.convert("RGB"))
            self.preview_label.configure(image=self.preview_image, text="")
        except Exception:
            self.preview_image = None
            self.preview_label.configure(image="", text=self.t("no_preview"))
        status = self.status_text(item.status)
        self.preview_info.set(
            self.t(
                "file_details",
                name=item.source.name,
                status=status,
                size=format_size(item.size),
                dimensions=item.dimensions or self.t("unknown"),
                message=item.message or self.t("empty_value"),
            )
        )

    def remove_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        index = int(selection[0])
        removed = self.items.pop(index)
        self.refresh_tree()
        self.set_status(self.t("removed", name=removed.source.name))

    def clear_items(self) -> None:
        if not self.items:
            return
        if not messagebox.askyesno(
            self.t("clear_title"), self.t("clear_question"), parent=self
        ):
            return
        self.items.clear()
        self.refresh_tree()
        self.preview_label.configure(image="", text=self.t("preview_empty"))
        self.preview_info.set("")
        self.preview_image = None
        self.set_status(self.t("cleared"))

    def create_manual_backup(self) -> None:
        ensure_layout(self.project_root)
        project_root = self.project_root
        config_snapshot = self._backup_config_snapshot()

        def operation() -> BackupInfo:
            return create_backup(
                project_root,
                "Manuelle Sicherung",
                APP_VERSION,
                config_snapshot=config_snapshot,
                keep=BACKUP_KEEP,
            )

        def success(info: BackupInfo) -> None:
            self.set_status(
                self.t("backup_created", count=info.file_count, size=format_backup_size(info.size_bytes))
            )
            self.log_event(
                "sicherung_erstellt",
                anlass="Manuelle Sicherung",
                pfad=str(info.path),
                dateien=info.file_count,
                groesse=info.size_bytes,
            )
            messagebox.showinfo(
                self.t("backup_created_title"),
                self.t("backup_created", count=info.file_count, size=format_backup_size(info.size_bytes)),
                parent=self,
            )

        self._run_in_background(operation, success, self._backup_error)

    def open_restore_dialog(self) -> None:
        if not self.require_admin(self.t("restore_backup")):
            return
        backups = list_backups(self.project_root)
        if not backups:
            messagebox.showinfo(self.t("restore_title"), self.t("restore_empty"), parent=self)
            return

        dialog = tk.Toplevel(self)
        dialog.title(self.t("restore_title"))
        dialog.transient(self)
        dialog.geometry("760x420")
        dialog.minsize(620, 320)
        frame = ttk.Frame(dialog, padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=self.t("restore_choose"), wraplength=700).pack(
            anchor="w", pady=(0, 10)
        )
        columns = ("zeitpunkt", "anlass", "dateien", "groesse")
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        tree.heading("zeitpunkt", text=self.t("restore_time"))
        tree.heading("anlass", text=self.t("restore_reason"))
        tree.heading("dateien", text=self.t("restore_files"))
        tree.heading("groesse", text=self.t("restore_size"))
        tree.column("zeitpunkt", width=180, anchor="w")
        tree.column("anlass", width=300, anchor="w")
        tree.column("dateien", width=80, anchor="e")
        tree.column("groesse", width=120, anchor="e")
        tree.pack(fill="both", expand=True)
        mapping: dict[str, BackupInfo] = {}
        for index, info in enumerate(backups):
            identifier = str(index)
            mapping[identifier] = info
            tree.insert(
                "",
                "end",
                iid=identifier,
                values=(
                    info.created_at.replace("T", " "),
                    info.reason,
                    info.file_count,
                    format_backup_size(info.size_bytes),
                ),
            )
        tree.selection_set("0")
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(12, 0))

        def restore_selected() -> None:
            selection = tree.selection()
            if not selection:
                return
            info = mapping[selection[0]]
            if not messagebox.askyesno(
                self.t("restore_title"),
                self.t(
                    "restore_confirm",
                    created=info.created_at.replace("T", " "),
                    reason=info.reason,
                ),
                parent=dialog,
            ):
                return
            dialog.destroy()
            self._restore_backup(info)

        ttk.Button(
            buttons,
            text=self.t("restore_action"),
            command=restore_selected,
            style="Primary.TButton",
        ).pack(side="left")
        ttk.Button(buttons, text=self.t("cancel"), command=dialog.destroy).pack(
            side="right"
        )
        dialog.grab_set()

    def _restore_backup(self, selected: BackupInfo) -> None:
        ensure_layout(self.project_root)
        project_root = self.project_root
        config_snapshot = self._backup_config_snapshot()

        def operation() -> tuple[BackupInfo, BackupInfo]:
            current = create_backup(
                project_root,
                "Vor Wiederherstellung",
                APP_VERSION,
                config_snapshot=config_snapshot,
                # Keep the selected fifth snapshot until restore has
                # completed; pruning it before restore would make the
                # requested target disappear.
                keep=BACKUP_KEEP + 1,
            )
            restored = restore_backup(project_root, selected.path)
            prune_backups(project_root, keep=BACKUP_KEEP)
            return current, restored

        def success(result: tuple[BackupInfo, BackupInfo]) -> None:
            _current, restored = result
            self.items.clear()
            self.refresh_tree()
            self.refresh_project_info()
            self.set_status(
                self.t("restore_success", created=restored.created_at.replace("T", " "))
            )
            self.log_event("sicherung_wiederhergestellt", pfad=str(restored.path))
            messagebox.showinfo(
                self.t("restore_success_title"),
                self.t("restore_success", created=restored.created_at.replace("T", " ")),
                parent=self,
            )

        def error(error: Exception, details: str) -> None:
            self.log_event("wiederherstellung_fehler", fehler=str(error), traceback=details)
            self.set_status(self.t("restore_failed_title"))
            messagebox.showerror(
                self.t("restore_failed_title"),
                self.t("restore_failed", error=error),
                parent=self,
            )

        self._run_in_background(operation, success, error)

    def open_manual(self) -> None:
        candidates = [self.project_root / "Gebrauchsanweisung_Pokemon-Auswahl.html"]
        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root:
            candidates.append(Path(bundle_root) / "docs" / "Gebrauchsanweisung_Pokemon-Auswahl.html")
        candidates.append(Path(__file__).resolve().parents[1] / "Gebrauchsanweisung_Pokemon-Auswahl.html")
        manual = next((path for path in candidates if path.is_file()), None)
        if manual is None:
            messagebox.showwarning(
                self.t("manual_missing_title"), self.t("manual_missing"), parent=self
            )
            return
        open_path(manual)

    def import_to_s1(self, show_result: bool = True) -> None:
        ready = [item for item in self.items if item.status == "Bereit" and item.destination]
        if not ready:
            if show_result:
                messagebox.showinfo(
                    self.t("no_import_title"),
                    self.t("no_import"),
                    parent=self,
                )
            else:
                self.set_status(self.t("no_import"))
            return
        ensure_layout(self.project_root)
        project_root = self.project_root
        language = self.language
        config_snapshot = self._backup_config_snapshot()

        def operation():
            backup = create_backup(
                project_root,
                "Vor Übernahme in den Arbeitsbestand",
                APP_VERSION,
                config_snapshot=config_snapshot,
                keep=BACKUP_KEEP,
            )
            results: list[tuple[ImportItem, bool, str]] = []
            for item in ready:
                try:
                    assert item.destination is not None
                    item.destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item.source, item.destination)
                    results.append(
                        (item, True, translate(language, "copied_to_s1", name=item.destination.name))
                    )
                except (OSError, AssertionError) as error:
                    results.append((item, False, str(error)))
            return backup, results

        def success(result) -> None:
            backup, results = result
            copied = 0
            errors: list[str] = []
            for item, successful, message in results:
                if successful:
                    item.status = "Übernommen"
                    item.message = message
                    copied += 1
                else:
                    item.status = "Fehler"
                    item.message = message
                    errors.append(f"{item.source.name}: {message}")
            self.refresh_tree()
            self.refresh_project_info()
            self.set_status(self.t("copied_status", count=copied))
            self.log_event(
                "dateien_uebernommen",
                anzahl=copied,
                fehler=errors,
                sicherung=str(backup.path),
            )
            if errors:
                messagebox.showerror(self.t("copy_error_title"), "\n".join(errors), parent=self)
            elif show_result:
                messagebox.showinfo(
                    self.t("copy_done_title"),
                    self.t("copy_done", count=copied),
                    parent=self,
                )

        self._run_in_background(operation, success, self._backup_error)

    def update_s1(self) -> None:
        ensure_layout(self.project_root)
        project_root = self.project_root
        config_snapshot = self._backup_config_snapshot()

        def operation():
            backup = create_backup(
                project_root,
                "Vor Aktualisierung der Druckauswahl",
                APP_VERSION,
                config_snapshot=config_snapshot,
                keep=BACKUP_KEEP,
            )
            return backup, update_s1(project_root)

        def success(result) -> None:
            backup, report = result
            self.refresh_project_info()
            self.set_status(
                self.t(
                    "updated_status",
                    active=report["active_count"],
                    new=report["new_entry_count"],
                )
            )
            self.log_event("s1_aktualisiert", sicherung=str(backup.path), **report)
            messagebox.showinfo(
                self.t("updated_title"),
                self.t(
                    "updated_info",
                    active=report["active_count"],
                    new=report["new_entry_count"],
                    missing=report["missing_count"],
                ),
                parent=self,
            )

        def error(error: Exception, details: str) -> None:
            self.log_event(
                "s1_aktualisierung_fehler",
                fehler=str(error),
                traceback=details,
            )
            self.set_status(self.t("update_failed_status", error=error))
            messagebox.showerror(self.t("update_failed_title"), str(error), parent=self)

        self._run_in_background(operation, success, error)

    def open_selection(self) -> None:
        html = self.project_root / "Pokemon-Bilder-Auswahl.html"
        if not html.is_file():
            messagebox.showwarning(
                self.t("selection_missing_title"),
                self.t("selection_missing"),
                parent=self,
            )
            return
        open_path(html)

    def open_log(self) -> None:
        ensure_layout(self.project_root)
        log_path = self.project_root / "Protokolle" / "pokemon-manager.jsonl"
        if not log_path.exists():
            log_path.write_text("", encoding="utf-8")
        open_path(log_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lokaler Pokémon-Manager für Julians Bildbestand.")
    parser.add_argument("--project-root", type=Path, help="Arbeitsordner für einen Test- oder Startlauf")
    args = parser.parse_args()
    app = PokemonManagerApp(args.project_root)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
