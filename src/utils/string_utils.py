"""String manipulation utility functions."""

import re
from pathlib import Path
from typing import Final

from src.constants import DISCORD_MAX_MESSAGE_LENGTH

# Characters that are not allowed in filenames
INVALID_FILENAME_CHARS: Final[str] = r'[<>:"/\\|?*]'


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length.

    Args:
        text: String to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add if truncated (default: "...")

    Returns:
        Truncated string

    Example:
        >>> truncate_string("This is a very long string", 15)
        'This is a ve...'
    """
    if len(text) <= max_length:
        return text

    # Account for suffix length
    actual_max = max_length - len(suffix)
    if actual_max < 1:
        return suffix[:max_length]

    return text[:actual_max] + suffix


def split_long_message(
    message: str,
    max_length: int = DISCORD_MAX_MESSAGE_LENGTH,
) -> list[str]:
    """Split a long message into chunks that fit Discord's limit.

    Args:
        message: Message to split
        max_length: Maximum length per chunk (default: 2000)

    Returns:
        List of message chunks

    Example:
        >>> long_text = "A" * 5000
        >>> chunks = split_long_message(long_text)
        >>> print(f"Split into {len(chunks)} chunks")
        Split into 3 chunks
    """
    if len(message) <= max_length:
        return [message]

    chunks: list[str] = []
    current_pos = 0

    while current_pos < len(message):
        # Get chunk
        chunk = message[current_pos : current_pos + max_length]

        # If not the last chunk, try to break at newline
        if current_pos + max_length < len(message):
            # Find last newline in chunk
            last_newline = chunk.rfind("\n")
            if last_newline > max_length // 2:  # Only if reasonably far in
                chunk = chunk[: last_newline + 1]
                current_pos += last_newline + 1
            else:
                current_pos += max_length
        else:
            current_pos += len(chunk)

        chunks.append(chunk)

    return chunks


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text.

    - Removes leading/trailing whitespace
    - Converts multiple spaces to single space
    - Converts multiple newlines to double newline

    Args:
        text: Text to normalize

    Returns:
        Normalized text

    Example:
        >>> normalize_whitespace("Hello    world\\n\\n\\nFoo")
        'Hello world\\n\\nFoo'
    """
    # Remove leading/trailing whitespace
    text = text.strip()

    # Replace multiple spaces with single space
    text = re.sub(r" +", " ", text)

    # Replace multiple newlines with double newline
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """Sanitize a filename by removing invalid characters.

    Args:
        filename: Original filename
        replacement: Character to replace invalid chars (default: "_")

    Returns:
        Sanitized filename

    Example:
        >>> sanitize_filename("my:file<name>.txt")
        'my_file_name_.txt'
    """
    # Replace invalid characters
    sanitized = re.sub(INVALID_FILENAME_CHARS, replacement, filename)

    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip(". ")

    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed"

    return sanitized


def extract_file_stem(file_path: Path) -> str:
    """Extract file name without extension.

    Args:
        file_path: Path to file

    Returns:
        Filename without extension

    Example:
        >>> extract_file_stem(Path("/path/to/document.pdf"))
        'document'
    """
    return file_path.stem


def format_list_with_and(items: list[str], oxford_comma: bool = True) -> str:
    """Format list of items with 'and' conjunction.

    Args:
        items: List of items
        oxford_comma: Use Oxford comma (default: True)

    Returns:
        Formatted string

    Example:
        >>> format_list_with_and(["Alice", "Bob", "Charlie"])
        'Alice, Bob, and Charlie'
        >>> format_list_with_and(["Alice", "Bob"])
        'Alice and Bob'
    """
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"

    if oxford_comma:
        return f"{', '.join(items[:-1])}, and {items[-1]}"
    return f"{', '.join(items[:-1])} and {items[-1]}"


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    """Return singular or plural form based on count.

    Args:
        count: Number to check
        singular: Singular form
        plural: Plural form (default: singular + "s")

    Returns:
        Appropriate form with count

    Example:
        >>> pluralize(1, "file")
        '1 file'
        >>> pluralize(5, "file")
        '5 files'
        >>> pluralize(2, "query", "queries")
        '2 queries'
    """
    if plural is None:
        plural = singular + "s"

    word = singular if count == 1 else plural
    return f"{count} {word}"


def mask_sensitive_string(value: str, visible_chars: int = 4) -> str:
    """Mask a sensitive string, showing only first/last few characters.

    Args:
        value: String to mask
        visible_chars: Number of characters to show on each end

    Returns:
        Masked string

    Example:
        >>> mask_sensitive_string("sk-1234567890abcdef")
        'sk-1***************def'
    """
    if len(value) <= visible_chars * 2:
        return "*" * len(value)

    start = value[:visible_chars]
    end = value[-visible_chars:]
    masked_length = len(value) - (visible_chars * 2)

    return f"{start}{'*' * masked_length}{end}"


def strip_markdown(text: str) -> str:
    """Remove basic Markdown formatting from text.

    Args:
        text: Text with Markdown formatting

    Returns:
        Plain text

    Example:
        >>> strip_markdown("**Bold** and *italic* text")
        'Bold and italic text'
    """
    # Remove bold
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)

    # Remove italic
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)

    # Remove code blocks
    text = re.sub(r"`(.+?)`", r"\1", text)

    # Remove headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Remove links but keep text
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)

    return text
