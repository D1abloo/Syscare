from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from .system import HOME, current_platform, format_bytes, performance_snapshot, run_process


@dataclass(frozen=True)
class MaintenanceItem:
    key: str
    title: str
    category: str
    description: str
    command: tuple[str, ...] = ()
    risky: bool = False


@dataclass
class Issue:
    kind: str
    path: str
    detail: str
    size: int = 0


def maintenance_items() -> list[MaintenanceItem]:
    items = [
        MaintenanceItem(
            "memory_optimize",
            "Optimizar memoria RAM",
            "Rendimiento",
            "Libera memoria inactiva y caches reclamables del sistema. macOS gestiona la RAM automaticamente; usalo si una app pesada acaba de cerrarse.",
            _memory_command(),
            risky=True,
        ),
        MaintenanceItem(
            "dns",
            "Vaciar cache DNS",
            "Red",
            "Limpia resoluciones DNS cacheadas para corregir errores de navegacion.",
            _dns_command(),
        ),
        MaintenanceItem(
            "font_cache",
            "Reconstruir cache de fuentes",
            "Sistema",
            "Actualiza la cache de fuentes si hay errores visuales o tipografias que no cargan.",
            ("fc-cache", "-f"),
        ),
        MaintenanceItem(
            "pip_cache",
            "Limpiar cache de pip",
            "Desarrollo",
            "Elimina paquetes descargados cacheados por pip para liberar espacio.",
            (sys.executable, "-m", "pip", "cache", "purge"),
        ),
        MaintenanceItem(
            "npm_cache",
            "Verificar cache de npm",
            "Desarrollo",
            "Repara y compacta la cache de npm si Node.js esta instalado.",
            ("npm", "cache", "verify"),
        ),
        MaintenanceItem(
            "docker_prune",
            "Limpiar Docker",
            "Contenedores",
            "Elimina contenedores parados, redes sin uso, imagenes colgantes y cache de build.",
            ("docker", "system", "prune", "-f"),
            risky=True,
        ),
    ]
    if current_platform() == "darwin":
        items.extend(
            [
                MaintenanceItem(
                    "quicklook",
                    "Reiniciar Quick Look",
                    "macOS",
                    "Limpia y reinicia la cache de previsualizaciones de macOS.",
                    ("qlmanage", "-r", "cache"),
                ),
                MaintenanceItem(
                    "preferences_daemon",
                    "Reiniciar preferencias",
                    "macOS",
                    "Reinicia cfprefsd para refrescar preferencias de usuario sin reiniciar sesion.",
                    ("killall", "cfprefsd"),
                ),
                MaintenanceItem(
                    "launchservices",
                    "Reconstruir LaunchServices",
                    "macOS",
                    "Repara asociaciones de apps y entradas de Abrir con.",
                    _launchservices_command(),
                    risky=True,
                ),
                MaintenanceItem(
                    "xcode_derived",
                    "Limpiar DerivedData de Xcode",
                    "Desarrollo",
                    "Elimina builds temporales de Xcode en ~/Library/Developer/Xcode/DerivedData.",
                    ("rm", "-rf", str(HOME / "Library" / "Developer" / "Xcode" / "DerivedData")),
                    risky=True,
                ),
                MaintenanceItem(
                    "brew_cleanup",
                    "Limpiar Homebrew",
                    "Paquetes",
                    "Elimina versiones antiguas y descargas cacheadas por Homebrew.",
                    ("brew", "cleanup", "-s"),
                ),
                MaintenanceItem(
                    "brew_autoremove",
                    "Homebrew autoremove",
                    "Paquetes",
                    "Elimina dependencias de Homebrew que ya no necesita ningun paquete instalado.",
                    ("brew", "autoremove"),
                    risky=True,
                ),
                MaintenanceItem(
                    "spotlight",
                    "Reindexar Spotlight usuario",
                    "Busqueda",
                    "Solicita una reindexacion de tu carpeta de usuario.",
                    ("mdutil", "-E", str(HOME)),
                    risky=True,
                ),
            ]
        )
    else:
        items.extend(
            [
                MaintenanceItem(
                    "apt_autoremove",
                    "APT autoremove",
                    "Paquetes",
                    "Elimina dependencias instaladas automaticamente que ya no se usan.",
                    ("apt", "autoremove", "-y"),
                    risky=True,
                ),
                MaintenanceItem(
                    "apt_clean",
                    "APT clean",
                    "Paquetes",
                    "Limpia paquetes descargados en la cache local de APT.",
                    ("apt", "clean"),
                    risky=True,
                ),
                MaintenanceItem(
                    "dnf_clean",
                    "DNF clean",
                    "Paquetes",
                    "Limpia metadata y paquetes cacheados por DNF.",
                    ("dnf", "clean", "all"),
                    risky=True,
                ),
                MaintenanceItem(
                    "pacman_cache",
                    "Pacman cache",
                    "Paquetes",
                    "Reduce la cache de paquetes de Pacman si paccache esta instalado.",
                    ("paccache", "-r"),
                    risky=True,
                ),
                MaintenanceItem(
                    "flatpak_unused",
                    "Flatpak no usados",
                    "Paquetes",
                    "Elimina runtimes Flatpak que ya no son necesarios.",
                    ("flatpak", "uninstall", "--unused", "-y"),
                    risky=True,
                ),
                MaintenanceItem(
                    "journal_vacuum",
                    "Reducir journal",
                    "Logs",
                    "Reduce los logs de systemd journal a los ultimos 7 dias.",
                    ("journalctl", "--vacuum-time=7d"),
                    risky=True,
                ),
            ]
        )
    return [item for item in items if _command_available(item.command)]


def _command_available(command: tuple[str, ...]) -> bool:
    if not command:
        return False
    executable = Path(command[0])
    if executable.is_absolute():
        return executable.exists() and os.access(executable, os.X_OK)
    return shutil.which(command[0]) is not None


def _dns_command() -> tuple[str, ...]:
    if current_platform() == "darwin":
        return ("dscacheutil", "-flushcache")
    if shutil.which("resolvectl"):
        return ("resolvectl", "flush-caches")
    if shutil.which("systemd-resolve"):
        return ("systemd-resolve", "--flush-caches")
    return ()


def _memory_command() -> tuple[str, ...]:
    if current_platform() == "darwin":
        purge = Path("/usr/sbin/purge")
        if purge.exists():
            return (str(purge),)
    if current_platform() == "linux" and Path("/proc/sys/vm/drop_caches").exists():
        return ("sh", "-c", "sync && echo 3 > /proc/sys/vm/drop_caches")
    return ()


def _launchservices_command() -> tuple[str, ...]:
    command = Path("/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister")
    if command.exists():
        return (str(command), "-kill", "-r", "-domain", "user")
    return ()


def run_maintenance(item: MaintenanceItem) -> tuple[int, str]:
    if not item.command:
        return 1, "No hay comando disponible para esta tarea en este sistema."
    if item.key == "memory_optimize":
        before = performance_snapshot()
        code, output = run_process(list(item.command), timeout=120)
        after = performance_snapshot()
        before_used = format_bytes(int(before["memory_used"]))
        after_used = format_bytes(int(after["memory_used"]))
        detail = output or "Memoria reclamable solicitada al sistema."
        return code, f"{detail}\n\nMemoria usada antes: {before_used}\nMemoria usada despues: {after_used}"
    command = list(item.command)
    privileged = {"apt_autoremove", "apt_clean", "dnf_clean", "journal_vacuum", "pacman_cache"}
    if item.key in privileged and os.geteuid() != 0:
        if shutil.which("pkexec"):
            command = ["pkexec", *command]
        elif shutil.which("sudo"):
            command = ["sudo", *command]
    code, output = run_process(command, timeout=900)
    if current_platform() == "darwin" and item.key == "dns" and shutil.which("killall"):
        run_process(["killall", "-HUP", "mDNSResponder"], timeout=30)
    return code, output or "Operacion completada sin salida."


def scan_invalid_entries() -> list[Issue]:
    issues: list[Issue] = []
    issues.extend(_broken_symlinks(HOME))
    if current_platform() == "darwin":
        issues.extend(_stale_launch_agents())
    else:
        issues.extend(_invalid_desktop_files())
    issues.extend(_large_downloads())
    return issues


def _broken_symlinks(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    candidates = [
        root / ".local" / "bin",
        root / ".local" / "share" / "applications",
        root / "Applications",
        root / "Library" / "LaunchAgents",
    ]
    for base in candidates:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            try:
                if path.is_symlink() and not path.exists():
                    issues.append(Issue("Enlace roto", str(path), "El destino ya no existe."))
            except OSError:
                continue
    return issues


def _invalid_desktop_files() -> list[Issue]:
    issues: list[Issue] = []
    roots = [HOME / ".local" / "share" / "applications", Path("/usr/share/applications")]
    for root in roots:
        if not root.exists():
            continue
        for desktop in root.glob("*.desktop"):
            try:
                lines = desktop.read_text(errors="ignore").splitlines()
            except OSError:
                continue
            exec_line = next((line.split("=", 1)[1] for line in lines if line.startswith("Exec=")), "")
            if not exec_line:
                issues.append(Issue("Entrada .desktop incompleta", str(desktop), "No contiene Exec=."))
                continue
            command = exec_line.split()[0].strip('"').replace("%u", "").replace("%U", "")
            if command.startswith("/") and not Path(command).exists():
                issues.append(Issue("Entrada .desktop invalida", str(desktop), f"No existe: {command}"))
    return issues


def _stale_launch_agents() -> list[Issue]:
    issues: list[Issue] = []
    roots = [HOME / "Library" / "LaunchAgents"]
    for root in roots:
        if not root.exists():
            continue
        for plist in root.glob("*.plist"):
            try:
                text = plist.read_text(errors="ignore")
            except OSError:
                continue
            if "/Applications/" in text:
                parts = [part for part in text.replace("<", "\n<").splitlines() if "/Applications/" in part]
                missing = [part for part in parts if ".app" in part and not Path(part.split(".app", 1)[0].split(">")[-1] + ".app").exists()]
                if missing:
                    issues.append(Issue("LaunchAgent posiblemente obsoleto", str(plist), "Referencia una app que no parece existir."))
    return issues


def _large_downloads() -> list[Issue]:
    issues: list[Issue] = []
    downloads = HOME / "Downloads"
    if not downloads.exists():
        return issues
    for path in downloads.iterdir():
        try:
            if path.is_file():
                size = path.stat().st_size
                if size >= 500 * 1024 * 1024:
                    issues.append(Issue("Archivo grande", str(path), f"Ocupa {format_bytes(size)} en Descargas.", size))
        except OSError:
            continue
    return issues
