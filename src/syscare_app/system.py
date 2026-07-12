from __future__ import annotations

import os
import platform
import plistlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import psutil

try:
    from send2trash import send2trash
except Exception:  # pragma: no cover - optional fallback
    send2trash = None


HOME = Path.home().resolve()


@dataclass(frozen=True)
class CleanupTarget:
    key: str
    name: str
    category: str
    description: str
    paths: tuple[Path, ...]
    risky: bool = False


@dataclass
class CleanupReport:
    target: CleanupTarget
    size: int
    items: int
    errors: list[str]


@dataclass
class AppEntry:
    name: str
    source: str
    identifier: str
    path: str
    version: str = ""


def format_bytes(value: int) -> str:
    amount = float(max(value, 0))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024 or unit == "TB":
            return f"{amount:.1f} {unit}" if unit != "B" else f"{int(amount)} B"
        amount /= 1024
    return f"{amount:.1f} TB"


def current_platform() -> str:
    return platform.system().lower()


def cleanup_targets() -> list[CleanupTarget]:
    system = current_platform()
    targets: list[CleanupTarget] = []

    common_tmp = tuple(Path(p) for p in (os.getenv("TMPDIR"), "/tmp", "/var/tmp") if p)
    targets.append(
        CleanupTarget(
            "temp",
            "Temporales de usuario",
            "Temporales",
            "Archivos temporales accesibles para tu usuario.",
            common_tmp,
        )
    )

    if system == "darwin":
        targets.extend(
            [
                CleanupTarget(
                    "user_cache",
                    "Caché de macOS",
                    "Caché",
                    "Contenido de ~/Library/Caches.",
                    (HOME / "Library" / "Caches",),
                ),
                CleanupTarget(
                    "logs",
                    "Logs de usuario",
                    "Logs",
                    "Registros en ~/Library/Logs.",
                    (HOME / "Library" / "Logs",),
                ),
                CleanupTarget(
                    "diagnostics",
                    "Informes de diagnostico",
                    "Mantenimiento",
                    "Reportes de fallos y diagnostico de usuario.",
                    (
                        HOME / "Library" / "Logs" / "DiagnosticReports",
                        HOME / "Library" / "Application Support" / "CrashReporter",
                    ),
                ),
                CleanupTarget(
                    "saved_state",
                    "Estados guardados",
                    "Mantenimiento",
                    "Ventanas y estados guardados por apps al cerrarse.",
                    (HOME / "Library" / "Saved Application State",),
                    risky=True,
                ),
                CleanupTarget(
                    "quicklook_cache",
                    "Caché Quick Look",
                    "Mantenimiento",
                    "Miniaturas y previsualizaciones generadas por macOS.",
                    (
                        HOME / "Library" / "Caches" / "com.apple.QuickLook.thumbnailcache",
                        HOME / "Library" / "Caches" / "QuickLook",
                    ),
                ),
                CleanupTarget(
                    "trash",
                    "Papelera de macOS",
                    "Limpieza",
                    "Contenido de ~/.Trash. Libera espacio de forma permanente.",
                    (HOME / ".Trash",),
                    risky=True,
                ),
                CleanupTarget(
                    "browser_cache",
                    "Caché de navegadores",
                    "Navegadores",
                    "Cachés de Chrome, Chromium, Brave, Edge, Firefox y Safari.",
                    tuple(
                        p
                        for p in (
                            HOME / "Library" / "Caches" / "Google" / "Chrome",
                            HOME / "Library" / "Caches" / "Chromium",
                            HOME / "Library" / "Caches" / "BraveSoftware",
                            HOME / "Library" / "Caches" / "Microsoft Edge",
                            HOME / "Library" / "Caches" / "Firefox",
                            HOME / "Library" / "Caches" / "com.apple.Safari",
                        )
                    ),
                ),
                CleanupTarget(
                    "cookies",
                    "Cookies de navegadores",
                    "Privacidad",
                    "Archivos de cookies. Puede cerrar sesiones abiertas.",
                    tuple(
                        p
                        for p in (
                            HOME / "Library" / "Cookies",
                            HOME / "Library" / "Application Support" / "Google" / "Chrome",
                            HOME / "Library" / "Application Support" / "BraveSoftware",
                            HOME / "Library" / "Application Support" / "Microsoft Edge",
                            HOME / "Library" / "Safari",
                        )
                    ),
                    risky=True,
                ),
            ]
        )
    else:
        targets.extend(
            [
                CleanupTarget(
                    "user_cache",
                    "Caché de Linux",
                    "Caché",
                    "Contenido de ~/.cache.",
                    (HOME / ".cache",),
                ),
                CleanupTarget(
                    "trash",
                    "Papelera local",
                    "Limpieza",
                    "Archivos de ~/.local/share/Trash/files.",
                    (HOME / ".local" / "share" / "Trash" / "files",),
                    risky=True,
                ),
                CleanupTarget(
                    "thumbnails",
                    "Miniaturas",
                    "Mantenimiento",
                    "Cache de miniaturas del escritorio y explorador de archivos.",
                    (HOME / ".cache" / "thumbnails",),
                ),
                CleanupTarget(
                    "recent_files",
                    "Recientes y metadatos",
                    "Mantenimiento",
                    "Listas de archivos recientes del entorno de escritorio.",
                    (
                        HOME / ".local" / "share" / "recently-used.xbel",
                        HOME / ".local" / "share" / "gvfs-metadata",
                    ),
                    risky=True,
                ),
                CleanupTarget(
                    "browser_cache",
                    "Caché de navegadores",
                    "Navegadores",
                    "Cachés de Firefox, Chrome, Chromium, Brave y Edge.",
                    tuple(
                        p
                        for p in (
                            HOME / ".cache" / "mozilla" / "firefox",
                            HOME / ".cache" / "google-chrome",
                            HOME / ".cache" / "chromium",
                            HOME / ".cache" / "BraveSoftware",
                            HOME / ".cache" / "microsoft-edge",
                        )
                    ),
                ),
                CleanupTarget(
                    "cookies",
                    "Cookies de navegadores",
                    "Privacidad",
                    "Archivos de cookies. Puede cerrar sesiones abiertas.",
                    tuple(
                        p
                        for p in (
                            HOME / ".mozilla" / "firefox",
                            HOME / ".config" / "google-chrome",
                            HOME / ".config" / "chromium",
                            HOME / ".config" / "BraveSoftware",
                            HOME / ".config" / "microsoft-edge",
                        )
                    ),
                    risky=True,
                ),
            ]
        )
    return targets


def _safe_to_touch(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        return False
    tmp_roots = {Path("/tmp"), Path("/var/tmp"), Path(tempfile.gettempdir())}
    tmp_env = os.getenv("TMPDIR")
    if tmp_env:
        tmp_roots.add(Path(tmp_env))
    if resolved == HOME or resolved == Path("/"):
        return False
    if resolved.is_relative_to(HOME):
        return True
    in_tmp = any(resolved == root or resolved.is_relative_to(root) for root in tmp_roots)
    if not in_tmp:
        return False
    try:
        return resolved == Path(tempfile.gettempdir()).resolve() or resolved.stat().st_uid == os.getuid()
    except OSError:
        return False


def _iter_existing(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        try:
            if path.exists() and _safe_to_touch(path):
                yield path
        except OSError:
            continue


def _cookie_files(root: Path) -> Iterable[Path]:
    names = {"cookies", "cookies-journal", "cookies.sqlite", "cookies.sqlite-wal", "cookies.sqlite-shm"}
    if root.is_file() and root.name.lower() in names:
        yield root
        return
    if not root.is_dir():
        return
    try:
        children = root.rglob("*")
        for child in children:
            try:
                if child.is_file() and child.name.lower() in names:
                    yield child
            except OSError:
                continue
    except OSError:
        return


def _walk_target_paths(target: CleanupTarget) -> Iterable[Path]:
    for root in _iter_existing(target.paths):
        if target.key == "cookies":
            yield from _cookie_files(root)
        elif root.is_file():
            yield root
        elif root.is_dir():
            try:
                for child in root.iterdir():
                    yield child
            except OSError:
                continue


def _path_size(path: Path) -> tuple[int, int, list[str]]:
    total = 0
    count = 0
    errors: list[str] = []
    try:
        if path.is_file() or path.is_symlink():
            return path.stat().st_size, 1, []
        for root, dirs, files in os.walk(path, topdown=True, onerror=lambda e: errors.append(str(e))):
            root_path = Path(root)
            dirs[:] = [d for d in dirs if not (root_path / d).is_symlink()]
            for filename in files:
                file_path = root_path / filename
                try:
                    total += file_path.stat().st_size
                    count += 1
                except OSError as exc:
                    errors.append(f"{file_path}: {exc}")
            count += len(dirs)
    except OSError as exc:
        errors.append(f"{path}: {exc}")
    return total, count, errors


def scan_target(target: CleanupTarget) -> CleanupReport:
    size = 0
    items = 0
    errors: list[str] = []
    for path in _walk_target_paths(target):
        chunk_size, chunk_items, chunk_errors = _path_size(path)
        size += chunk_size
        items += chunk_items
        errors.extend(chunk_errors[:5])
    return CleanupReport(target, size, items, errors)


def delete_target(target: CleanupTarget) -> CleanupReport:
    before = scan_target(target)
    errors = list(before.errors)
    for path in _walk_target_paths(target):
        if not _safe_to_touch(path):
            errors.append(f"Ruta omitida por seguridad: {path}")
            continue
        try:
            _delete_path(path)
        except OSError as exc:
            errors.append(f"{path}: {exc}")
        except Exception as exc:
            errors.append(f"{path}: {exc}")
    return CleanupReport(target, before.size, before.items, errors)


def _delete_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def performance_snapshot() -> dict[str, object]:
    disk = psutil.disk_usage(str(HOME.anchor or "/"))
    memory = psutil.virtual_memory()
    battery = psutil.sensors_battery()
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "memory_percent": memory.percent,
        "memory_used": memory.used,
        "memory_total": memory.total,
        "disk_percent": disk.percent,
        "disk_used": disk.used,
        "disk_total": disk.total,
        "battery": battery.percent if battery else None,
    }


def temperature_snapshot() -> list[tuple[str, float | None]]:
    try:
        sensors = psutil.sensors_temperatures(fahrenheit=False)
    except (AttributeError, OSError):
        sensors = {}
    readings: list[tuple[str, float | None]] = []
    for sensor_name, entries in sensors.items():
        for entry in entries:
            label = entry.label or sensor_name
            readings.append((label, entry.current))
    if not readings and current_platform() == "darwin":
        readings.extend(_macos_thermal_snapshot())
    return readings


def _macos_thermal_snapshot() -> list[tuple[str, float | None]]:
    code, output = run_process(["pmset", "-g", "therm"], timeout=8)
    if code != 0 or not output:
        return []
    readings: list[tuple[str, float | None]] = []
    for line in output.splitlines():
        clean = " ".join(line.strip().split())
        if clean == "Note: No thermal warning level has been recorded":
            readings.append(("Estado termico: normal", None))
        elif clean == "Note: No performance warning level has been recorded":
            readings.append(("Rendimiento termico: normal", None))
        elif "CPU_Scheduler_Limit" in clean:
            readings.append((clean.replace("CPU_Scheduler_Limit", "Planificador CPU").replace(" = ", ": "), None))
        elif "CPU_Speed_Limit" in clean:
            readings.append((clean.replace("CPU_Speed_Limit", "Limite velocidad CPU").replace(" = ", ": "), None))
    return readings[:6]


def list_installed_apps() -> list[AppEntry]:
    system = current_platform()
    if system == "darwin":
        return _list_macos_apps()
    return _list_linux_apps()


def _list_macos_apps() -> list[AppEntry]:
    apps: list[AppEntry] = []
    for root in (Path("/Applications"), HOME / "Applications"):
        if not root.exists():
            continue
        for app in sorted(root.glob("*.app")):
            info = _macos_app_info(app)
            apps.append(AppEntry(info["name"], "macOS App", info["bundle_id"], str(app), info["version"]))
    return apps


def _macos_app_info(app: Path) -> dict[str, str]:
    info_path = app / "Contents" / "Info.plist"
    fallback = {"name": app.stem, "bundle_id": app.name, "version": ""}
    try:
        with info_path.open("rb") as handle:
            payload = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException):
        return fallback
    name = str(
        payload.get("CFBundleDisplayName")
        or payload.get("CFBundleName")
        or payload.get("CFBundleExecutable")
        or app.stem
    )
    bundle_id = str(payload.get("CFBundleIdentifier") or app.name)
    version = str(payload.get("CFBundleShortVersionString") or payload.get("CFBundleVersion") or "")
    return {"name": name, "bundle_id": bundle_id, "version": version}


def _desktop_name(path: Path) -> str | None:
    try:
        for line in path.read_text(errors="ignore").splitlines():
            if line.startswith("Name="):
                return line.split("=", 1)[1].strip()
    except OSError:
        return None
    return None


def _list_linux_apps() -> list[AppEntry]:
    apps: list[AppEntry] = []
    seen: set[str] = set()
    for root in (HOME / ".local" / "share" / "applications", Path("/usr/share/applications")):
        if not root.exists():
            continue
        for desktop in sorted(root.glob("*.desktop")):
            name = _desktop_name(desktop)
            if not name or name in seen:
                continue
            seen.add(name)
            apps.append(AppEntry(name, "Desktop", desktop.stem, str(desktop)))
    return apps


def uninstall_app(entry: AppEntry) -> tuple[bool, str]:
    system = current_platform()
    if system == "darwin" and entry.path.endswith(".app"):
        path = Path(entry.path)
        if not _safe_to_touch(path) and not path.is_relative_to(Path("/Applications")):
            return False, "La ruta no parece una app valida."
        try:
            if send2trash:
                send2trash(str(path))
            else:
                shutil.rmtree(path)
            return True, f"{entry.name} movida a la papelera."
        except Exception as exc:
            return False, str(exc)
    return False, "En Linux usa el panel de paquetes para desinstalar con tu gestor (apt, dnf, pacman, snap, flatpak o brew)."


def run_process(command: list[str], timeout: int = 120) -> tuple[int, str]:
    try:
        extra_paths = [
            "/opt/homebrew/bin",
            "/opt/homebrew/sbin",
            "/usr/local/bin",
            "/usr/local/sbin",
            "/opt/local/bin",
            "/usr/bin",
            "/bin",
            "/usr/sbin",
            "/sbin",
            "/snap/bin",
            str(HOME / ".local" / "bin"),
        ]
        env_path = os.pathsep.join(dict.fromkeys([*os.environ.get("PATH", "").split(os.pathsep), *extra_paths]))
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env={**os.environ, "PATH": env_path},
        )
        output = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part)
        return completed.returncode, output
    except FileNotFoundError:
        return 127, f"No se encontro el comando: {command[0]}"
    except subprocess.TimeoutExpired:
        return 124, "La operacion tardo demasiado y fue detenida."
