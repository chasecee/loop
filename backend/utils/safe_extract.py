from __future__ import annotations

"""Secure archive extraction helpers.

These helpers ensure
1. No member ends up outside the target directory (zip-slip / tar-slip).
2. Symlinks and hard-links are refused.

Usage:
    from utils.safe_extract import safe_extract_tar, safe_extract_zip
    safe_extract_tar(tar_file_obj, target_path)
"""

import os
from pathlib import Path
import tarfile
import zipfile
from typing import Union

class ArchiveExtractionError(Exception):
    """Raised when an unsafe archive member is detected."""
    pass


def _is_within_directory(base: Path, target: Path) -> bool:
    """Return True if *target* is inside *base*."""
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False


def safe_extract_tar(tar: tarfile.TarFile, path: Union[str, Path]) -> None:
    """Safely extract a tar/tar.gz archive to *path*.

    Refuses entries that attempt directory traversal or that are
    links (symlink or hard-link).
    """
    dest_dir = Path(path).resolve()
    for member in tar.getmembers():
        member_path = dest_dir / member.name

        # Disallow absolute paths or traversal outside dest_dir
        if member.name.startswith("/") or not _is_within_directory(dest_dir, member_path.resolve()):
            raise ArchiveExtractionError(f"Unsafe path detected in tar member: {member.name}")

        # Refuse symlinks / hardlinks
        if member.islnk() or member.issym():
            raise ArchiveExtractionError(f"Refusing to extract link: {member.name}")

    tar.extractall(dest_dir)


def safe_extract_zip(zip_file: zipfile.ZipFile, path: Union[str, Path]) -> None:
    """Safely extract a ZIP archive to *path* (no traversal, no links)."""
    dest_dir = Path(path).resolve()
    for info in zip_file.infolist():
        member_path = dest_dir / info.filename

        # Disallow absolute paths or traversal outside dest_dir
        if info.filename.startswith("/") or ".." in Path(info.filename).parts or not _is_within_directory(dest_dir, member_path.resolve()):
            raise ArchiveExtractionError(f"Unsafe path detected in zip member: {info.filename}")

        # Refuse Unix symlinks (mode 0o120000)
        if (info.external_attr >> 16) & 0o120000 == 0o120000:
            raise ArchiveExtractionError(f"Refusing to extract symlink: {info.filename}")

    zip_file.extractall(dest_dir)