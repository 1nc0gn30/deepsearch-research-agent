"""
compat.py - Cross-Platform Compatibility Layer for DeepSearch Research Agent.

Pure Python 3.9–3.13 stdlib compatibility utilities supporting Linux, macOS,
Windows, and Termux (Android). Handles UTF-8 stream normalization, atomic file I/O,
POSIX path helpers, browser launching, and platform diagnostics.
"""

from __future__ import annotations

import io
import os
import platform
import re
import shutil
import sys
import tempfile
import urllib.parse
import webbrowser
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Optional, Union


# ---------------------------------------------------------------------------
# Platform Detection & Diagnostics
# ---------------------------------------------------------------------------

def is_termux() -> bool:
    """Check if the current runtime environment is Termux on Android."""
    return bool(
        os.environ.get("TERMUX_VERSION")
        or "com.termux" in os.environ.get("PREFIX", "")
        or "/data/data/com.termux" in os.environ.get("PATH", "")
    )


def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform.startswith("win") or os.name == "nt"


def is_macos() -> bool:
    """Check if running on macOS (Darwin)."""
    return sys.platform == "darwin"


def is_linux() -> bool:
    """Check if running on standard Linux (excluding pure Termux if distinguished)."""
    return sys.platform.startswith("linux")


def supports_color() -> bool:
    """Check if the current terminal supports ANSI escape color codes."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    if is_windows():
        return (
            os.environ.get("WT_SESSION") is not None
            or os.environ.get("ANSICON") is not None
            or "TERM" in os.environ
        )
    return True


def get_platform_info() -> Dict[str, Any]:
    """
    Retrieve comprehensive platform diagnostics.
    
    Returns:
        Dict containing OS, architecture, python version, terminal features,
        and platform flags.
    """
    term_width = 80
    term_height = 24
    try:
        size = shutil.get_terminal_size()
        term_width = size.columns
        term_height = size.lines
    except Exception:
        pass

    return {
        "os_name": os.name,
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "is_termux": is_termux(),
        "is_windows": is_windows(),
        "is_macos": is_macos(),
        "is_linux": is_linux(),
        "supports_color": supports_color(),
        "terminal_size": {"columns": term_width, "lines": term_height},
        "default_encoding": sys.getdefaultencoding(),
        "filesystem_encoding": sys.getfilesystemencoding(),
        "stdout_encoding": getattr(sys.stdout, "encoding", "utf-8") or "utf-8",
    }


# ---------------------------------------------------------------------------
# UTF-8 Stream Handling
# ---------------------------------------------------------------------------

def ensure_utf8(text_or_bytes: Union[str, bytes], errors: str = "replace") -> str:
    """Ensure that the input is converted to a clean UTF-8 string."""
    if isinstance(text_or_bytes, bytes):
        return text_or_bytes.decode("utf-8", errors=errors)
    return str(text_or_bytes)


def setup_utf8_output() -> None:
    """
    Reconfigure standard output and standard error streams to UTF-8 encoding
    if supported by the runtime.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def safe_print(*args: Any, sep: str = " ", end: str = "\n", file: Optional[Any] = None) -> None:
    """
    Print safely avoiding UnicodeEncodeError across diverse platform consoles.
    """
    target = file or sys.stdout
    text = sep.join(str(arg) for arg in args) + end
    try:
        target.write(text)
        target.flush()
    except UnicodeEncodeError:
        encoding = getattr(target, "encoding", "utf-8") or "utf-8"
        encoded = text.encode(encoding, errors="replace").decode(encoding)
        target.write(encoded)
        target.flush()
    except Exception:
        # Fallback to standard print
        print(*args, sep=sep, end=end, file=file)


# ---------------------------------------------------------------------------
# Atomic File I/O
# ---------------------------------------------------------------------------

def atomic_write_text(
    filepath: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    make_parents: bool = True,
    errors: str = "replace",
) -> Path:
    """
    Atomically write text content to a file using a temporary staging file.
    Ensures that partially written files are never exposed in case of a crash.

    Args:
        filepath: Target file path.
        content: String content to write.
        encoding: File encoding (default: 'utf-8').
        make_parents: Automatically create parent directories if missing.
        errors: Encoding error handling strategy.

    Returns:
        Path to the written file.
    """
    target_path = Path(filepath).resolve()
    if make_parents:
        target_path.parent.mkdir(parents=True, exist_ok=True)

    # Use same directory for temp file to ensure atomic rename across filesystem boundaries
    temp_dir = target_path.parent
    temp_fd, temp_name = tempfile.mkstemp(
        prefix=f".tmp_{target_path.name}_",
        dir=str(temp_dir),
        text=True,
    )
    try:
        with open(temp_fd, "w", encoding=encoding, errors=errors) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        # Atomic replace
        os.replace(temp_name, str(target_path))
    except Exception:
        if os.path.exists(temp_name):
            try:
                os.remove(temp_name)
            except OSError:
                pass
        raise

    return target_path


def atomic_write_bytes(
    filepath: Union[str, Path],
    data: bytes,
    make_parents: bool = True,
) -> Path:
    """
    Atomically write binary data to a file using a temporary staging file.

    Args:
        filepath: Target file path.
        data: Byte content to write.
        make_parents: Automatically create parent directories if missing.

    Returns:
        Path to the written file.
    """
    target_path = Path(filepath).resolve()
    if make_parents:
        target_path.parent.mkdir(parents=True, exist_ok=True)

    temp_dir = target_path.parent
    temp_fd, temp_name = tempfile.mkstemp(
        prefix=f".tmp_{target_path.name}_",
        dir=str(temp_dir),
        text=False,
    )
    try:
        with open(temp_fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_name, str(target_path))
    except Exception:
        if os.path.exists(temp_name):
            try:
                os.remove(temp_name)
            except OSError:
                pass
        raise

    return target_path


# ---------------------------------------------------------------------------
# Path Helpers & Normalization
# ---------------------------------------------------------------------------

def normalize_path(path: Union[str, Path]) -> Path:
    """Normalize a path to its resolved absolute Path representation."""
    return Path(path).expanduser().resolve()


def to_posix_path(path: Union[str, Path]) -> str:
    """
    Convert any path (Windows backslashes or POSIX) to a forward-slash POSIX path string.
    Useful for URLs, JSON serialization, and cross-platform markdown links.
    """
    p = Path(path)
    return PurePosixPath(p.as_posix()).as_posix()


def ensure_dir(dir_path: Union[str, Path]) -> Path:
    """Ensure that a directory exists, creating all necessary parents."""
    path = normalize_path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(name: str, max_length: int = 120, replacement: str = "_") -> str:
    """
    Sanitize an arbitrary string into a safe cross-platform file name.
    Strips invalid characters for Windows, Linux, Android, and macOS.
    """
    # Remove characters forbidden on Windows/POSIX: < > : " / \ | ? * and control chars
    clean = re.sub(r'[\<\>\:\"\/\\\|\?\*\x00-\x1f]', replacement, name)
    # Collapse consecutive replacement chars
    clean = re.sub(re.escape(replacement) + r"+", replacement, clean)
    clean = clean.strip(" .")
    if not clean:
        clean = "unnamed"
    return clean[:max_length]


def get_app_data_dir(app_name: str = "deepsearch-research-agent") -> Path:
    """
    Get the standard application data/cache directory based on platform conventions:
    - Termux: $PREFIX/var/data or ~/.deepsearch
    - Windows: %APPDATA% or %LOCALAPPDATA%
    - macOS: ~/Library/Application Support
    - Linux: $XDG_DATA_HOME or ~/.local/share
    """
    if is_termux():
        base = os.environ.get("PREFIX", "")
        if base:
            return ensure_dir(Path(base) / "var" / "data" / app_name)
        return ensure_dir(Path.home() / f".{app_name}")

    if is_windows():
        appdata = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if appdata:
            return ensure_dir(Path(appdata) / app_name)
        return ensure_dir(Path.home() / "AppData" / "Local" / app_name)

    if is_macos():
        return ensure_dir(Path.home() / "Library" / "Application Support" / app_name)

    # Standard Linux / Unix XDG
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        return ensure_dir(Path(xdg_data) / app_name)
    return ensure_dir(Path.home() / ".local" / "share" / app_name)


# ---------------------------------------------------------------------------
# Browser Opener
# ---------------------------------------------------------------------------

def open_in_browser(url_or_path: Union[str, Path], background: bool = True) -> bool:
    """
    Open a URL or local HTML file in the default system browser across platforms.
    Handles Android Termux `termux-open-url` fallback, macOS `open`, Windows `start`,
    and standard `webbrowser`.

    Args:
        url_or_path: URL string or local Path to open.
        background: Hint to open in background if supported.

    Returns:
        True if browser opening was dispatched successfully, False otherwise.
    """
    target = str(url_or_path)
    if os.path.exists(target):
        # Convert local file path to file:// URL
        target = Path(target).resolve().as_uri()

    # Special handling for Termux Android
    if is_termux():
        try:
            import subprocess
            res = subprocess.run(["termux-open-url", target], capture_output=True, check=False)
            if res.returncode == 0:
                return True
        except Exception:
            pass

    # Standard library webbrowser
    try:
        return webbrowser.open(target, new=2 if background else 0, autoraise=not background)
    except Exception:
        return False
