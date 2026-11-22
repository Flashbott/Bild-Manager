"""Versioned project backups and safe restore operations for Pokémon-Manager."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


BACKUP_FORMAT_VERSION = 1
BACKUP_FOLDER_NAME = "Backups"
BACKUP_INFO_NAME = "backup-info.json"
MANIFEST_NAME = "manifest.json"
SNAPSHOT_NAME_PATTERN = re.compile(r"^\d{8}-\d{6}(?:-\d+)?$")
SNAPSHOT_ROOTS = ("S1", "Index")
SNAPSHOT_FILES = ("Pokemon-Bilder-Auswahl.html",)


@dataclass(frozen=True)
class BackupInfo:
    path: Path
    created_at: str
    reason: str
    file_count: int
    size_bytes: int
    valid: bool


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _safe_relative_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"Unsicherer Sicherungspfad: {relative}") from error
    return candidate


def _project_files(project_root: Path) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for root_name in SNAPSHOT_ROOTS:
        source_root = project_root / root_name
        if not source_root.is_dir():
            continue
        for source in sorted(source_root.rglob("*")):
            if source.is_file():
                relative = source.relative_to(project_root).as_posix()
                files.append((source, relative))
    for file_name in SNAPSHOT_FILES:
        source = project_root / file_name
        if source.is_file():
            files.append((source, source.relative_to(project_root).as_posix()))
    return files


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Ungültige JSON-Datei: {path.name}")
    return payload


def _manifest_for_backup(backup_path: Path) -> dict:
    manifest = _load_json(backup_path / MANIFEST_NAME)
    if manifest.get("format_version") != BACKUP_FORMAT_VERSION:
        raise ValueError("Nicht unterstützte Sicherungsversion.")
    files = manifest.get("files")
    if not isinstance(files, list):
        raise ValueError("Sicherungsmanifest enthält keine Dateiliste.")
    return manifest


def verify_backup(backup_path: Path) -> dict:
    """Verify all files and hashes recorded by a backup manifest."""
    backup_path = backup_path.resolve()
    manifest = _manifest_for_backup(backup_path)
    total_size = 0
    verified_files = 0
    for entry in manifest["files"]:
        if not isinstance(entry, dict):
            raise ValueError("Ungültiger Eintrag im Sicherungsmanifest.")
        relative = entry.get("path")
        expected_hash = entry.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected_hash, str):
            raise ValueError("Sicherungsmanifest enthält unvollständige Daten.")
        source = _safe_relative_path(backup_path, relative)
        if not source.is_file():
            raise FileNotFoundError(f"Datei fehlt in Sicherung: {relative}")
        actual_hash = _hash_file(source)
        if actual_hash != expected_hash:
            raise ValueError(f"Prüfsumme stimmt nicht: {relative}")
        total_size += source.stat().st_size
        verified_files += 1
    return {"file_count": verified_files, "size_bytes": total_size}


def _snapshot_name() -> str:
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    return timestamp


def create_backup(
    project_root: Path,
    reason: str,
    app_version: str,
    config_snapshot: dict | None = None,
    keep: int = 5,
) -> BackupInfo:
    """Create a complete copy-based snapshot and prune only known old snapshots."""
    project_root = project_root.resolve()
    backup_root = project_root / BACKUP_FOLDER_NAME
    backup_root.mkdir(parents=True, exist_ok=True)
    base_name = _snapshot_name()
    final_path = backup_root / base_name
    suffix = 2
    while final_path.exists():
        final_path = backup_root / f"{base_name}-{suffix}"
        suffix += 1
    staging_path = backup_root / f".{final_path.name}.tmp-{uuid.uuid4().hex}"
    staging_path.mkdir(parents=True, exist_ok=False)

    records: list[dict] = []
    try:
        for source, relative in _project_files(project_root):
            destination = _safe_relative_path(staging_path, relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            records.append(
                {
                    "path": relative,
                    "size_bytes": destination.stat().st_size,
                    "sha256": _hash_file(destination),
                }
            )

        created_at = datetime.now().astimezone().isoformat(timespec="seconds")
        manifest = {
            "format_version": BACKUP_FORMAT_VERSION,
            "created_at": created_at,
            "reason": reason,
            "files": records,
        }
        _write_json(staging_path / MANIFEST_NAME, manifest)
        _write_json(
            staging_path / BACKUP_INFO_NAME,
            {
                "format_version": BACKUP_FORMAT_VERSION,
                "created_at": created_at,
                "reason": reason,
                "app_version": app_version,
                "file_count": len(records),
                "size_bytes": sum(item["size_bytes"] for item in records),
                "config": config_snapshot or {},
            },
        )
        os.replace(staging_path, final_path)
    except Exception:
        shutil.rmtree(staging_path, ignore_errors=True)
        raise

    prune_backups(project_root, keep=keep)
    return backup_info(final_path)


def _is_snapshot_directory(path: Path) -> bool:
    return path.is_dir() and bool(SNAPSHOT_NAME_PATTERN.fullmatch(path.name))


def list_backups(project_root: Path) -> list[BackupInfo]:
    backup_root = project_root.resolve() / BACKUP_FOLDER_NAME
    if not backup_root.is_dir():
        return []
    result: list[BackupInfo] = []
    for path in sorted(backup_root.iterdir(), reverse=True):
        if _is_snapshot_directory(path):
            try:
                result.append(backup_info(path))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
    return result


def backup_info(path: Path) -> BackupInfo:
    path = path.resolve()
    info = _load_json(path / BACKUP_INFO_NAME)
    verification = verify_backup(path)
    return BackupInfo(
        path=path,
        created_at=str(info.get("created_at", "")),
        reason=str(info.get("reason", "")),
        file_count=int(verification["file_count"]),
        size_bytes=int(verification["size_bytes"]),
        valid=True,
    )


def prune_backups(project_root: Path, keep: int = 5) -> list[Path]:
    if keep < 1:
        raise ValueError("Mindestens eine Sicherung muss behalten werden.")
    backup_root = project_root.resolve() / BACKUP_FOLDER_NAME
    if not backup_root.is_dir():
        return []
    candidates = [
        path
        for path in backup_root.iterdir()
        if _is_snapshot_directory(path)
        and (path / MANIFEST_NAME).is_file()
        and (path / BACKUP_INFO_NAME).is_file()
    ]
    candidates.sort(key=lambda path: path.name, reverse=True)
    removed: list[Path] = []
    for path in candidates[keep:]:
        shutil.rmtree(path)
        removed.append(path)
    return removed


def restore_backup(project_root: Path, backup_path: Path) -> BackupInfo:
    """Restore S1, Index and the generated HTML with a rollback on failure."""
    project_root = project_root.resolve()
    backup_root = (project_root / BACKUP_FOLDER_NAME).resolve()
    backup_path = backup_path.resolve()
    try:
        backup_path.relative_to(backup_root)
    except ValueError as error:
        raise ValueError("Die ausgewählte Sicherung gehört nicht zu diesem Projekt.") from error

    info = backup_info(backup_path)
    manifest = _manifest_for_backup(backup_path)
    token = uuid.uuid4().hex
    staging = project_root / f".restore-staging-{token}"
    old_root = project_root / f".restore-old-{token}"
    staging.mkdir(parents=True, exist_ok=False)
    old_root.mkdir(parents=True, exist_ok=False)
    html_relative = SNAPSHOT_FILES[0]
    html_present = False

    try:
        (staging / "S1").mkdir()
        (staging / "Index").mkdir()
        for entry in manifest["files"]:
            relative = entry["path"]
            source = _safe_relative_path(backup_path, relative)
            destination = _safe_relative_path(staging, relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            if relative == html_relative:
                html_present = True

        swapped: list[tuple[Path, Path, bool]] = []

        def swap(target: Path, replacement: Path) -> None:
            old = old_root / target.name
            had_target = target.exists()
            if had_target:
                target.rename(old)
            try:
                replacement.rename(target)
            except Exception:
                if had_target and old.exists():
                    old.rename(target)
                raise
            swapped.append((target, old, had_target))

        try:
            swap(project_root / "S1", staging / "S1")
            swap(project_root / "Index", staging / "Index")
            html_target = project_root / html_relative
            html_replacement = staging / html_relative
            if html_target.exists():
                html_target.rename(old_root / html_target.name)
                html_had_target = True
            else:
                html_had_target = False
            if html_present:
                try:
                    html_replacement.rename(html_target)
                except Exception:
                    if html_had_target and (old_root / html_target.name).exists():
                        (old_root / html_target.name).rename(html_target)
                    raise
            swapped.append((html_target, old_root / html_target.name, html_had_target))
        except Exception:
            for target, old, had_target in reversed(swapped):
                if target.is_dir():
                    shutil.rmtree(target, ignore_errors=True)
                elif target.exists():
                    target.unlink()
                if had_target and old.exists():
                    old.rename(target)
            raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
        shutil.rmtree(old_root, ignore_errors=True)

    return info


def format_backup_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size_bytes} B"
