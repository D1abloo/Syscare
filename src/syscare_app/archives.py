from __future__ import annotations

import shutil
from pathlib import Path


def compress_folder(source: Path, destination: Path, archive_format: str = "zip") -> Path:
    if not source.exists() or not source.is_dir():
        raise ValueError("Selecciona una carpeta existente para comprimir.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    base_name = destination.with_suffix("")
    output = shutil.make_archive(str(base_name), archive_format, root_dir=source.parent, base_dir=source.name)
    return Path(output)


def extract_archive(source: Path, destination: Path) -> Path:
    if not source.exists() or not source.is_file():
        raise ValueError("Selecciona un archivo comprimido existente.")
    destination.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(source), str(destination))
    return destination
