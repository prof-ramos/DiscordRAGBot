"""File-related utility functions."""

import hashlib
from pathlib import Path
from typing import Optional

from src.constants import HASH_ALGORITHM, HASH_CHUNK_SIZE, SUPPORTED_DOCUMENT_TYPES


def calculate_file_hash(
    file_path: Path,
    algorithm: str = HASH_ALGORITHM,
    chunk_size: int = HASH_CHUNK_SIZE,
) -> str:
    """Calculate hash of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: SHA-256)
        chunk_size: Size of chunks to read (default: 4096 bytes)

    Returns:
        Hexadecimal hash string

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
        ValueError: If algorithm is invalid

    Example:
        >>> path = Path("document.pdf")
        >>> hash_value = calculate_file_hash(path)
        >>> print(f"File hash: {hash_value[:8]}...")
        File hash: a1b2c3d4...
    """
    try:
        hash_obj = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Invalid hash algorithm: {algorithm}") from e

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def ensure_directory_exists(directory: Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        directory: Path to directory

    Returns:
        The directory path (for chaining)

    Example:
        >>> data_dir = ensure_directory_exists(Path("data"))
        >>> print(f"Directory ready: {data_dir}")
        Directory ready: data
    """
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes.

    Args:
        file_path: Path to file

    Returns:
        File size in MB (rounded to 2 decimal places)

    Raises:
        FileNotFoundError: If file doesn't exist

    Example:
        >>> size = get_file_size_mb(Path("large_document.pdf"))
        >>> print(f"File size: {size} MB")
        File size: 2.45 MB
    """
    size_bytes = file_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    return round(size_mb, 2)


def is_file_type_supported(
    file_path: Path,
    supported_types: Optional[set[str]] = None,
) -> bool:
    """Check if file type is supported.

    Args:
        file_path: Path to file
        supported_types: Set of supported extensions (default: PDF, TXT, MD)

    Returns:
        True if file type is supported

    Example:
        >>> is_supported = is_file_type_supported(Path("doc.pdf"))
        >>> print(f"Supported: {is_supported}")
        Supported: True
    """
    if supported_types is None:
        supported_types = SUPPORTED_DOCUMENT_TYPES

    return file_path.suffix.lower() in supported_types


def get_relative_path(file_path: Path, base_path: Path) -> str:
    """Get relative path from base path.

    Args:
        file_path: Full file path
        base_path: Base directory path

    Returns:
        Relative path as string

    Example:
        >>> rel_path = get_relative_path(
        ...     Path("/home/user/data/docs/file.pdf"),
        ...     Path("/home/user/data")
        ... )
        >>> print(rel_path)
        docs/file.pdf
    """
    try:
        return str(file_path.relative_to(base_path))
    except ValueError:
        # If paths don't have common base, return full path
        return str(file_path)


def count_files_in_directory(
    directory: Path,
    pattern: str = "*",
    recursive: bool = True,
) -> int:
    """Count files in a directory matching a pattern.

    Args:
        directory: Directory to search
        pattern: Glob pattern (default: all files)
        recursive: Search recursively (default: True)

    Returns:
        Number of matching files

    Example:
        >>> pdf_count = count_files_in_directory(Path("data"), "*.pdf")
        >>> print(f"Found {pdf_count} PDF files")
        Found 42 PDF files
    """
    if recursive:
        return len(list(directory.rglob(pattern)))
    return len(list(directory.glob(pattern)))
