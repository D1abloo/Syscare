from __future__ import annotations

import shutil
import subprocess
import platform
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PackageManager:
    key: str
    name: str
    search: tuple[str, ...]
    install: tuple[str, ...]
    uninstall: tuple[str, ...]
    list_installed: tuple[str, ...]
    needs_privilege: bool = False
    platforms: tuple[str, ...] = ("linux", "darwin")


MANAGERS = [
    PackageManager("brew", "Homebrew", ("brew", "search"), ("brew", "install"), ("brew", "uninstall"), ("brew", "list", "--versions"), platforms=("darwin", "linux")),
    PackageManager("port", "MacPorts", ("port", "search"), ("port", "install"), ("port", "uninstall"), ("port", "installed"), True, ("darwin",)),
    PackageManager("apt", "APT", ("apt-cache", "search"), ("apt", "install", "-y"), ("apt", "remove", "-y"), ("dpkg-query", "-W", "-f=${Package}\\t${Version}\\n"), True, ("linux",)),
    PackageManager("dnf", "DNF", ("dnf", "search"), ("dnf", "install", "-y"), ("dnf", "remove", "-y"), ("dnf", "list", "installed"), True, ("linux",)),
    PackageManager("yum", "YUM", ("yum", "search"), ("yum", "install", "-y"), ("yum", "remove", "-y"), ("yum", "list", "installed"), True, ("linux",)),
    PackageManager("zypper", "Zypper", ("zypper", "search"), ("zypper", "--non-interactive", "install"), ("zypper", "--non-interactive", "remove"), ("zypper", "search", "--installed-only"), True, ("linux",)),
    PackageManager("pacman", "Pacman", ("pacman", "-Ss"), ("pacman", "-S", "--noconfirm"), ("pacman", "-Rns", "--noconfirm"), ("pacman", "-Q"), True, ("linux",)),
    PackageManager("snap", "Snap", ("snap", "find"), ("snap", "install"), ("snap", "remove"), ("snap", "list"), True, ("linux",)),
    PackageManager("flatpak", "Flatpak", ("flatpak", "search"), ("flatpak", "install", "-y"), ("flatpak", "uninstall", "-y"), ("flatpak", "list", "--app"), False, ("linux",)),
]


def command_path() -> str:
    existing = [part for part in os.environ.get("PATH", "").split(os.pathsep) if part]
    common = [
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
        str(Path.home() / ".local" / "bin"),
    ]
    merged: list[str] = []
    for path in [*existing, *common]:
        if path not in merged:
            merged.append(path)
    return os.pathsep.join(merged)


def _which(command: str) -> str | None:
    return shutil.which(command, path=command_path())


def available_managers() -> list[PackageManager]:
    system = platform.system().lower()
    available = []
    for manager in MANAGERS:
        if system not in manager.platforms:
            continue
        if _which(manager.search[0]) and _which(manager.install[0]):
            available.append(manager)
    return available


def with_privilege(manager: PackageManager, command: list[str]) -> list[str]:
    if not manager.needs_privilege:
        return command
    if shutil.which("pkexec"):
        return ["pkexec", *command]
    if shutil.which("sudo"):
        return ["sudo", *command]
    return command


def run_command(command: list[str], timeout: int = 180) -> tuple[int, str]:
    try:
        env = {**os.environ, "PATH": command_path()}
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False, env=env)
        output = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part)
        return completed.returncode, output
    except FileNotFoundError:
        return 127, f"No se encontro el comando: {command[0]}"
    except subprocess.TimeoutExpired:
        return 124, "La operacion tardo demasiado y fue detenida."


def search(manager: PackageManager, query: str) -> tuple[int, str]:
    return run_command([*manager.search, query], timeout=90)


def list_installed(manager: PackageManager) -> tuple[int, str]:
    return run_command(list(manager.list_installed), timeout=90)


def install(manager: PackageManager, package_name: str) -> tuple[int, str]:
    return run_command(with_privilege(manager, [*manager.install, package_name]), timeout=900)


def uninstall(manager: PackageManager, package_name: str) -> tuple[int, str]:
    return run_command(with_privilege(manager, [*manager.uninstall, package_name]), timeout=900)
