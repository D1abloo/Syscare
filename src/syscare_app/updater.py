from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from packaging.version import InvalidVersion, Version


@dataclass
class UpdateInfo:
    available: bool
    message: str
    latest_version: str = ""
    url: str = ""
    can_git_pull: bool = False


def _run_git(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        completed = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, timeout=60, check=False)
        output = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part)
        return completed.returncode, output
    except Exception as exc:
        return 1, str(exc)


def repo_url(cwd: Path) -> str:
    configured = os.getenv("SYSCARE_REPO_URL", "").strip()
    if configured:
        return configured
    code, output = _run_git(["remote", "get-url", "origin"], cwd)
    return output.strip() if code == 0 else ""


def _github_api_url(url: str) -> str:
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)", url)
    if not match:
        return ""
    owner = match.group("owner")
    repo = match.group("repo")
    return f"https://api.github.com/repos/{owner}/{repo}/releases/latest"


def check_updates(current_version: str, cwd: Path) -> UpdateInfo:
    url = repo_url(cwd)
    if not url:
        return UpdateInfo(False, "No hay repositorio configurado. Define SYSCARE_REPO_URL o ejecuta la app desde un clon Git.")

    api_url = _github_api_url(url)
    if api_url:
        try:
            with urllib.request.urlopen(api_url, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
            tag = str(payload.get("tag_name") or payload.get("name") or "").lstrip("v")
            html_url = str(payload.get("html_url") or url)
            try:
                if Version(tag) > Version(current_version):
                    return UpdateInfo(True, f"Version {tag} disponible.", tag, html_url)
            except InvalidVersion:
                return UpdateInfo(True, f"Ultima version publicada: {tag}", tag, html_url)
            return UpdateInfo(False, "Ya tienes la ultima version publicada.", tag, html_url)
        except Exception as exc:
            return UpdateInfo(False, f"No se pudo consultar GitHub Releases: {exc}", url=url)

    code, output = _run_git(["fetch", "--dry-run", "origin"], cwd)
    if code == 0 and output:
        return UpdateInfo(True, "Hay cambios remotos disponibles en el repositorio.", url=url, can_git_pull=True)
    if code == 0:
        return UpdateInfo(False, "El repositorio local parece estar actualizado.", url=url)
    return UpdateInfo(False, f"No se pudo comprobar el repositorio: {output}", url=url)


def install_git_update(cwd: Path) -> tuple[bool, str]:
    code, output = _run_git(["pull", "--ff-only"], cwd)
    return code == 0, output
