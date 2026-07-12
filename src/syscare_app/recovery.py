from __future__ import annotations

import configparser
import os
import shutil
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

from .system import HOME


@dataclass
class RecoverableFile:
    name: str
    trash_path: str
    original_path: str
    deleted_at: str
    size: int


def trash_roots(include_volumes: bool = True) -> list[tuple[Path, Path]]:
    roots = [
        (HOME / ".local" / "share" / "Trash" / "files", HOME / ".local" / "share" / "Trash" / "info"),
        (HOME / ".Trash" / "files", HOME / ".Trash" / "info"),
        (HOME / ".Trash", HOME / ".Trash" / "info"),
    ]
    volumes = Path("/Volumes")
    if include_volumes and volumes.exists():
        for volume in volumes.iterdir():
            roots.append((volume / ".Trashes" / str(os.getuid()), volume / ".Trashes" / str(os.getuid()) / "info"))
    return [(files, info) for files, info in roots if files.exists()]


def scan_recoverable(query: str = "") -> list[RecoverableFile]:
    needle = query.strip().lower()
    return _scan_recoverable(needle, None, include_volumes=False)


def scan_recoverable_all_disks(query: str = "") -> list[RecoverableFile]:
    needle = query.strip().lower()
    return _scan_recoverable(needle, None, include_volumes=True)


def scan_recoverable_in_folder(query: str, folder: Path) -> list[RecoverableFile]:
    needle = query.strip().lower()
    try:
        folder_resolved = folder.expanduser().resolve()
    except OSError:
        folder_resolved = folder.expanduser()
    return _scan_recoverable(needle, folder_resolved, include_volumes=True)


def _scan_recoverable(needle: str, folder: Path | None, include_volumes: bool) -> list[RecoverableFile]:
    results: list[RecoverableFile] = []
    for files_root, info_root in trash_roots(include_volumes=include_volumes):
        try:
            entries = list(files_root.iterdir())
        except OSError:
            continue
        for path in entries:
            if path.name in {".DS_Store", "info"}:
                continue
            if needle and needle not in path.name.lower():
                continue
            original, deleted_at = _trash_info(path, info_root)
            if folder is not None and not _original_inside_folder(original, folder):
                continue
            results.append(
                RecoverableFile(
                    path.name,
                    str(path),
                    original,
                    deleted_at,
                    _size(path),
                )
            )
    return sorted(results, key=lambda item: item.name.lower())


def _original_inside_folder(original_path: str, folder: Path) -> bool:
    if not original_path:
        return False
    try:
        original = Path(original_path).expanduser().resolve()
        return original == folder or original.is_relative_to(folder)
    except OSError:
        return False


def _trash_info(path: Path, info_root: Path) -> tuple[str, str]:
    info_file = info_root / f"{path.name}.trashinfo"
    if not info_file.exists():
        return "", ""
    parser = configparser.ConfigParser()
    try:
        parser.read(info_file)
        section = parser["Trash Info"]
        raw_path = section.get("Path", "")
        deleted_at = section.get("DeletionDate", "")
        return urllib.parse.unquote(raw_path), deleted_at
    except Exception:
        return "", ""


def _size(path: Path) -> int:
    try:
        if path.is_file() or path.is_symlink():
            return path.stat().st_size
        total = 0
        for child in path.rglob("*"):
            if child.is_file():
                total += child.stat().st_size
        return total
    except OSError:
        return 0


def recover_file(file: RecoverableFile, destination: Path | None = None) -> tuple[bool, str]:
    source = Path(file.trash_path)
    if not source.exists():
        return False, "El archivo ya no esta en la papelera."
    target = destination
    if target is None and file.original_path:
        target = Path(file.original_path).expanduser()
    if target is None:
        target = HOME / "Recovered" / source.name
    if target.is_dir():
        target = target / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        stem = target.stem
        suffix = target.suffix
        counter = 1
        while target.exists():
            target = target.with_name(f"{stem}-recuperado-{counter}{suffix}")
            counter += 1
    try:
        shutil.move(str(source), str(target))
        info = Path(file.trash_path).parent.parent / "info" / f"{source.name}.trashinfo"
        if info.exists():
            info.unlink(missing_ok=True)
        return True, f"Recuperado en {target}"
    except OSError as exc:
        return False, str(exc)
