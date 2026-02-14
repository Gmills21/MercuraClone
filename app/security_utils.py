"""
Security utilities for sanitizing inputs and preventing common attacks.
"""

import re
import os
from pathlib import Path
from typing import Optional


def sanitize_filename(filename: str, allow_empty: bool = False) -> Optional[str]:
    """
    Sanitize a filename to prevent path traversal attacks.
    
    Removes path separators, null bytes, and other dangerous characters.
    Returns None if the filename is invalid/empty after sanitization.
    
    Args:
        filename: The original filename
        allow_empty: If True, returns empty string instead of None
    
    Returns:
        Sanitized filename or None if invalid
    """
    if not filename:
        return "" if allow_empty else None
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Normalize path separators
    filename = filename.replace('\\', '/')
    
    # Get just the basename (remove any path components)
    filename = os.path.basename(filename)
    
    # Remove leading dots (hidden files) and dangerous characters
    filename = filename.lstrip('.')
    
    # Remove any remaining dangerous characters but keep common filename chars
    # Allow: alphanumeric, underscore, hyphen, dot, space
    filename = re.sub(r'[^\w\-. ]', '_', filename)
    
    # Limit length to prevent buffer issues
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    # Check if filename is empty after sanitization
    if not filename or filename == '.' or filename == '..':
        return "" if allow_empty else None
    
    return filename


def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """
    Validate that a file has an allowed extension.
    
    Args:
        filename: The filename to check
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.jpg'])
    
    Returns:
        True if extension is allowed
    """
    if not filename:
        return False
    
    ext = os.path.splitext(filename.lower())[1]
    return ext in allowed_extensions


def is_safe_path(base_path: str, target_path: str) -> bool:
    """
    Check if target_path is within base_path (prevents path traversal).
    
    Args:
        base_path: The allowed base directory
        target_path: The path to validate
    
    Returns:
        True if target_path is within base_path
    """
    try:
        base = Path(base_path).resolve()
        target = Path(target_path).resolve()
        return str(target).startswith(str(base))
    except (ValueError, RuntimeError):
        return False


def sanitize_email(email: str) -> Optional[str]:
    """
    Basic email sanitization and validation.
    
    Returns sanitized email or None if invalid.
    """
    if not email:
        return None
    
    # Remove whitespace and convert to lowercase
    email = email.strip().lower()
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return email
    
    return None


def sanitize_string(input_str: str, max_length: int = 1000, allow_html: bool = False) -> str:
    """
    Sanitize a string input to prevent injection attacks.
    
    Args:
        input_str: The string to sanitize
        max_length: Maximum allowed length
        allow_html: If False, strips HTML tags
    
    Returns:
        Sanitized string
    """
    if not input_str:
        return ""
    
    # Limit length
    input_str = input_str[:max_length]
    
    if not allow_html:
        # Remove HTML tags
        input_str = re.sub(r'<[^>]+>', '', input_str)
    
    # Remove null bytes
    input_str = input_str.replace('\x00', '')
    
    return input_str.strip()
