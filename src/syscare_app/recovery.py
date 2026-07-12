from __future__ import annotations

import configparser
import json
import os
import shutil
import subprocess
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


@dataclass
class RecoveryScanReport:
    files: list[RecoverableFile]
    locations: list[str]
    errors: list[str]


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
    return _scan_recoverable_report(needle, None, include_volumes=False).files


def scan_recoverable_all_disks(query: str = "") -> list[RecoverableFile]:
    needle = query.strip().lower()
    return _scan_recoverable_report(needle, None, include_volumes=True).files


def scan_recoverable_in_folder(query: str, folder: Path) -> list[RecoverableFile]:
    needle = query.strip().lower()
    try:
        folder_resolved = folder.expanduser().resolve()
    except OSError:
        folder_resolved = folder.expanduser()
    return _scan_recoverable_report(needle, folder_resolved, include_volumes=True).files


def scan_recoverable_report(query: str = "", folder: Path | None = None, include_volumes: bool = False) -> RecoveryScanReport:
    needle = query.strip().lower()
    folder_resolved = None
    if folder is not None:
        try:
            folder_resolved = folder.expanduser().resolve()
        except OSError:
            folder_resolved = folder.expanduser()
    return _scan_recoverable_report(needle, folder_resolved, include_volumes)


def _scan_recoverable_report(needle: str, folder: Path | None, include_volumes: bool) -> RecoveryScanReport:
    results: list[RecoverableFile] = []
    errors: list[str] = []
    locations: list[str] = []
    for root in trash_roots(include_volumes=include_volumes):
        locations.append(str(root.files))
        try:
            entries = list(root.files.iterdir())
        except OSError as exc:
            errors.append(f"{root.files}: {exc}")
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
    if current_platform() == "darwin":
        finder_files, finder_errors = _macos_finder_trash_items(needle, folder)
        errors.extend(finder_errors)
        if "Finder: Papelera de macOS" not in locations:
            locations.append("Finder: Papelera de macOS")
        by_path = {file.trash_path: file for file in results}
        for file in finder_files:
            by_path.setdefault(file.trash_path, file)
        results = list(by_path.values())
    if folder is not None:
        repository_files, repository_errors = _scan_repository_folder(needle, folder)
        errors.extend(repository_errors)
        if repository_files:
            locations.append(str(folder))
        by_path = {file.trash_path: file for file in results}
        for file in repository_files:
            by_path.setdefault(file.trash_path, file)
        results = list(by_path.values())
    return RecoveryScanReport(sorted(results, key=lambda item: item.name.lower()), locations, errors)


def _scan_repository_folder(needle: str, folder: Path) -> tuple[list[RecoverableFile], list[str]]:
    files: list[RecoverableFile] = []
    errors: list[str] = []
    try:
        iterator = folder.rglob("*")
        for path in iterator:
            if len(files) >= 2000:
                errors.append(f"{folder}: limite de 2000 candidatos alcanzado.")
                break
            try:
                if not (path.is_file() or path.is_dir()):
                    continue
            except OSError as exc:
                errors.append(f"{path}: {exc}")
                continue
            if path.name in {".DS_Store", "Thumbs.db"}:
                continue
            if needle and needle not in path.name.lower():
                continue
            files.append(
                RecoverableFile(
                    name=path.name,
                    trash_path=str(path),
                    original_path=f"Repositorio seleccionado: {folder}",
                    deleted_at="--",
                    size=_size(path),
                )
            )
    except OSError as exc:
        errors.append(f"{folder}: {exc}")
    return files, errors


def _macos_finder_trash_items(needle: str, folder: Path | None) -> tuple[list[RecoverableFile], list[str]]:
    script = """
tell application "Finder"
    set outText to ""
    set trashItems to every item of trash
    repeat with trashItem in trashItems
        set itemName to name of trashItem as text
        set itemPath to POSIX path of (trashItem as alias)
        try
            set itemSize to size of trashItem as text
        on error
            set itemSize to "0"
        end try
        set outText to outText & itemName & tab & itemPath & tab & itemSize & linefeed
    end repeat
    return outText
end tell
""".strip()
    try:
        completed = subprocess.run(["/usr/bin/osascript", "-e", script], capture_output=True, text=True, timeout=20, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return [], [f"Finder: {exc}"]
    if completed.returncode != 0:
        return [], [completed.stderr.strip() or "Finder no permitio leer la papelera."]
    files: list[RecoverableFile] = []
    for line in completed.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        name = parts[0].strip()
        trash_path = parts[1].strip()
        if not name or (needle and needle not in name.lower()):
            continue
        if folder is not None and needle and needle not in name.lower():
            continue
        try:
            size = int(parts[2]) if len(parts) > 2 and parts[2].strip() else 0
        except ValueError:
            size = 0
        files.append(
            RecoverableFile(
                name=name,
                trash_path=trash_path,
                original_path="Origen no disponible en metadatos de macOS (Finder)",
                deleted_at="--",
                size=size,
            )
        )
    return files, []


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
    try:
        source_exists = source.exists()
    except OSError:
        source_exists = False
    if not source_exists and current_platform() != "darwin":
        return False, "El archivo ya no esta en la papelera."
    target = destination
    if target is None and _has_restorable_original(file.original_path):
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
        if current_platform() == "darwin":
            ok, message = _macos_finder_move(source, target)
            if ok:
                return ok, message
        return False, str(exc)


def _info_candidates(source: Path) -> list[Path]:
    return [
        source.parent.parent / "info" / f"{source.name}.trashinfo",
        source.parent / "info" / f"{source.name}.trashinfo",
        source.parent / f"{source.name}.trashinfo",
    ]


def _has_restorable_original(original_path: str) -> bool:
    if not original_path:
        return False
    if original_path.startswith(("Origen no disponible", "Repositorio seleccionado")):
        return False
    return Path(original_path).expanduser().is_absolute()


def _macos_finder_move(source: Path, target: Path) -> tuple[bool, str]:
    target.parent.mkdir(parents=True, exist_ok=True)
    source_text = json.dumps(str(source))
    parent_text = json.dumps(str(target.parent) + "/")
    name_text = json.dumps(target.name)
    script = f"""
tell application "Finder"
    set sourceItem to POSIX file {source_text} as alias
    set targetFolder to POSIX file {parent_text} as alias
    set movedItem to move sourceItem to targetFolder
    set name of movedItem to {name_text}
end tell
""".strip()
    try:
        completed = subprocess.run(["/usr/bin/osascript", "-e", script], capture_output=True, text=True, timeout=60, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return False, f"Finder no pudo restaurar: {exc}"
    if completed.returncode != 0:
        return False, completed.stderr.strip() or "Finder no pudo restaurar el archivo."
    return True, f"Recuperado en {target}"
