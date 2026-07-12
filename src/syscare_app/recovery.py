from __future__ import annotations

import configparser
import os
import shutil
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

from .system import HOME, current_platform


@dataclass
class RecoverableFile:
    name: str
    trash_path: str
    original_path: str
    deleted_at: str
    size: int


@dataclass(frozen=True)
class TrashRoot:
    files: Path
    info: Path
    label: str


def trash_roots(include_volumes: bool = True) -> list[TrashRoot]:
    uid = str(os.getuid())
    candidates = [
        TrashRoot(HOME / ".local" / "share" / "Trash" / "files", HOME / ".local" / "share" / "Trash" / "info", "Papelera freedesktop del usuario"),
        TrashRoot(HOME / ".Trash" / "files", HOME / ".Trash" / "info", "Papelera de usuario"),
        TrashRoot(HOME / ".Trash", HOME / ".Trash" / "info", "Papelera de usuario macOS"),
    ]
    if include_volumes:
        candidates.extend(_volume_trash_roots(uid))

    roots: list[TrashRoot] = []
    seen: set[Path] = set()
    for root in candidates:
        try:
            files = root.files.expanduser().resolve()
        except OSError:
            files = root.files.expanduser()
        if files in seen or not files.exists() or not files.is_dir():
            continue
        seen.add(files)
        roots.append(TrashRoot(files, root.info.expanduser(), root.label))
    return roots


def _volume_trash_roots(uid: str) -> list[TrashRoot]:
    roots: list[TrashRoot] = []
    mount_parents = [Path("/Volumes"), Path("/media") / os.getenv("USER", ""), Path("/run/media") / os.getenv("USER", ""), Path("/mnt")]
    for parent in mount_parents:
        if not parent.exists():
            continue
        try:
            volumes = list(parent.iterdir())
        except OSError:
            continue
        for volume in volumes:
            roots.extend(
                [
                    TrashRoot(volume / ".Trashes" / uid, volume / ".Trashes" / uid / "info", f"Papelera de {volume.name}"),
                    TrashRoot(volume / ".Trashes" / uid / "files", volume / ".Trashes" / uid / "info", f"Papelera freedesktop de {volume.name}"),
                    TrashRoot(volume / f".Trash-{uid}" / "files", volume / f".Trash-{uid}" / "info", f"Papelera de {volume.name}"),
                    TrashRoot(volume / ".Trash" / uid / "files", volume / ".Trash" / uid / "info", f"Papelera compartida de {volume.name}"),
                    TrashRoot(volume / ".Trash", volume / ".Trash" / "info", f"Papelera de {volume.name}"),
                ]
            )
    return roots


def scan_locations(include_volumes: bool = True) -> list[str]:
    return [str(root.files) for root in trash_roots(include_volumes=include_volumes)]


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
    for root in trash_roots(include_volumes=include_volumes):
        try:
            entries = list(root.files.iterdir())
        except OSError:
            continue
        for path in entries:
            if path.name in {".DS_Store", "info"}:
                continue
            if needle and needle not in path.name.lower():
                continue
            original, deleted_at = _trash_info(path, root.info)
            if folder is not None and original and not _original_inside_folder(original, folder):
                continue
            if folder is not None and not original and needle and needle not in path.name.lower():
                continue
            results.append(
                RecoverableFile(
                    path.name,
                    str(path),
                    original or _fallback_original_hint(path, root),
                    deleted_at,
                    _size(path),
                )
            )
    return sorted(results, key=lambda item: item.name.lower())


def _fallback_original_hint(path: Path, root: TrashRoot) -> str:
    if current_platform() == "darwin":
        return f"Origen no disponible en metadatos de macOS ({root.label})"
    return f"Origen no disponible ({root.label})"


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
    if target is None and file.original_path and not file.original_path.startswith("Origen no disponible"):
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
        for info in _info_candidates(source):
            if info.exists():
                info.unlink(missing_ok=True)
        return True, f"Recuperado en {target}"
    except OSError as exc:
        return False, str(exc)


def _info_candidates(source: Path) -> list[Path]:
    return [
        source.parent.parent / "info" / f"{source.name}.trashinfo",
        source.parent / "info" / f"{source.name}.trashinfo",
        source.parent / f"{source.name}.trashinfo",
    ]
