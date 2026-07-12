from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from packaging.version import InvalidVersion, Version

DEFAULT_REPO_URL = "https://github.com/D1abloo/Syscare"


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
    return output.strip() if code == 0 else DEFAULT_REPO_URL


def _github_api_url(url: str) -> str:
    owner_repo = _github_owner_repo(url)
    if not owner_repo:
        return ""
    owner, repo = owner_repo
    return f"https://api.github.com/repos/{owner}/{repo}/releases/latest"


def _github_owner_repo(url: str) -> tuple[str, str] | None:
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)", url)
    if not match:
        return None
    owner = match.group("owner")
    repo = match.group("repo")
    return owner, repo


def _github_json(api_url: str) -> dict:
    request = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github+json", "User-Agent": "SysCare"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def check_updates(current_version: str, cwd: Path) -> UpdateInfo:
    url = repo_url(cwd)
    if not url:
        return UpdateInfo(False, "No hay repositorio configurado. Define SYSCARE_REPO_URL o ejecuta la app desde un clon Git.")

    api_url = _github_api_url(url)
    owner_repo = _github_owner_repo(url)
    if api_url and owner_repo:
        try:
            payload = _github_json(api_url)
            tag = str(payload.get("tag_name") or payload.get("name") or "").lstrip("v")
            html_url = str(payload.get("html_url") or url)
            try:
                if Version(tag) > Version(current_version):
                    return UpdateInfo(True, f"Version {tag} disponible.", tag, html_url)
            except InvalidVersion:
                return UpdateInfo(True, f"Ultima version publicada: {tag}", tag, html_url)
            return UpdateInfo(False, "Ya tienes la ultima version publicada.", tag, html_url)
        except Exception as exc:
            release_error = str(exc)
        owner, repo = owner_repo
        try:
            payload = _github_json(f"https://api.github.com/repos/{owner}/{repo}/commits/main")
            latest_sha = str(payload.get("sha", ""))[:12]
            html_url = str(payload.get("html_url") or url)
            code, local_sha = _run_git(["rev-parse", "--short=12", "HEAD"], cwd)
            if code == 0 and latest_sha and latest_sha != local_sha.strip():
                return UpdateInfo(True, f"Hay cambios nuevos en GitHub ({latest_sha}).", latest_sha, html_url, can_git_pull=True)
            if latest_sha:
                return UpdateInfo(False, f"GitHub no muestra cambios nuevos. Ultimo commit: {latest_sha}.", latest_sha, html_url)
            return UpdateInfo(False, "GitHub respondio sin informacion de commit.", url=url)
        except Exception as exc:
            return UpdateInfo(False, f"No se pudo consultar GitHub. Releases: {release_error}. Commits: {exc}", url=url)

    return UpdateInfo(False, "El repositorio configurado no es de GitHub. Define SYSCARE_REPO_URL con una URL de GitHub.", url=url)


def install_git_update(cwd: Path) -> tuple[bool, str]:
    code, output = _run_git(["pull", "--ff-only"], cwd)
    return code == 0, output
