from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class PackageManager:
    key: str
    name: str
    search: tuple[str, ...]
    install: tuple[str, ...]
    uninstall: tuple[str, ...]
    list_installed: tuple[str, ...]
    needs_privilege: bool = False


MANAGERS = [
    PackageManager("brew", "Homebrew", ("brew", "search"), ("brew", "install"), ("brew", "uninstall"), ("brew", "list", "--versions")),
    PackageManager("apt", "APT", ("apt-cache", "search"), ("apt", "install", "-y"), ("apt", "remove", "-y"), ("dpkg-query", "-W", "-f=${Package}\\t${Version}\\n"), True),
    PackageManager("dnf", "DNF", ("dnf", "search"), ("dnf", "install", "-y"), ("dnf", "remove", "-y"), ("dnf", "list", "installed"), True),
    PackageManager("pacman", "Pacman", ("pacman", "-Ss"), ("pacman", "-S", "--noconfirm"), ("pacman", "-Rns", "--noconfirm"), ("pacman", "-Q"), True),
    PackageManager("snap", "Snap", ("snap", "find"), ("snap", "install"), ("snap", "remove"), ("snap", "list"), True),
    PackageManager("flatpak", "Flatpak", ("flatpak", "search"), ("flatpak", "install", "-y"), ("flatpak", "uninstall", "-y"), ("flatpak", "list", "--app"), False),
]


def available_managers() -> list[PackageManager]:
    available = []
    for manager in MANAGERS:
        if shutil.which(manager.search[0]) and shutil.which(manager.install[0]):
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
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
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
