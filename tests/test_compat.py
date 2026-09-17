"""
test_compat.py - Unit tests for compat.py cross-platform utilities.
"""

import io
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from deepsearch_research_agent.compat import (
    atomic_write_bytes,
    atomic_write_text,
    ensure_dir,
    ensure_utf8,
    get_app_data_dir,
    get_platform_info,
    is_linux,
    is_macos,
    is_termux,
    is_windows,
    normalize_path,
    open_in_browser,
    safe_filename,
    safe_print,
    setup_utf8_output,
    supports_color,
    to_posix_path,
)


def test_platform_detection():
    """Verify platform detection functions return boolean values."""
    assert isinstance(is_termux(), bool)
    assert isinstance(is_windows(), bool)
    assert isinstance(is_macos(), bool)
    assert isinstance(is_linux(), bool)
    assert isinstance(supports_color(), bool)


def test_get_platform_info():
    """Verify get_platform_info returns dictionary with expected keys."""
    info = get_platform_info()
    assert isinstance(info, dict)
    assert "os_name" in info
    assert "platform_system" in info
    assert "python_version" in info
    assert "terminal_size" in info
    assert "columns" in info["terminal_size"]
    assert "lines" in info["terminal_size"]


def test_ensure_utf8():
    """Verify ensure_utf8 handles strings and bytes correctly."""
    assert ensure_utf8("hello world") == "hello world"
    assert ensure_utf8(b"binary string") == "binary string"
    assert ensure_utf8("unicode \u2713") == "unicode \u2713"
    assert ensure_utf8(b"unicode \xe2\x9c\x93") == "unicode \u2713"


def test_setup_utf8_output():
    """Verify setup_utf8_output executes without error."""
    setup_utf8_output()


def test_safe_print():
    """Verify safe_print writes formatted text to custom stream."""
    buf = io.StringIO()
    safe_print("Test", 123, "Success", sep=" | ", end="\n", file=buf)
    output = buf.getvalue()
    assert output == "Test | 123 | Success\n"


def test_atomic_write_text(tmp_path):
    """Verify atomic_write_text creates parent dirs and writes content correctly."""
    target_file = tmp_path / "sub" / "nested" / "test_file.txt"
    content = "Hello, DeepSearch Research Agent!\nLine 2 \u2714"
    
    written_path = atomic_write_text(target_file, content)
    assert written_path.exists()
    assert written_path.read_text(encoding="utf-8") == content

    # Overwrite test
    new_content = "Overwritten content"
    atomic_write_text(target_file, new_content)
    assert written_path.read_text(encoding="utf-8") == new_content


def test_atomic_write_bytes(tmp_path):
    """Verify atomic_write_bytes writes binary data cleanly."""
    target_file = tmp_path / "binary" / "blob.bin"
    data = b"\x00\x01\x02\x03\xff\xfe"
    
    written_path = atomic_write_bytes(target_file, data)
    assert written_path.exists()
    assert written_path.read_bytes() == data


def test_to_posix_path():
    """Verify to_posix_path converts paths to forward slash strings."""
    assert to_posix_path("foo/bar/baz.txt") == "foo/bar/baz.txt"
    assert "/" in to_posix_path(Path("foo") / "bar")


def test_safe_filename():
    """Verify safe_filename strips illegal chars for file systems."""
    assert safe_filename('Report: "DeepSearch" <v1.0> | draft?.md') == "Report_ _DeepSearch_ _v1.0_ _ draft_.md"
    assert safe_filename("") == "unnamed"
    assert safe_filename("   ...   ") == "unnamed"
    long_name = "a" * 200
    assert len(safe_filename(long_name, max_length=50)) == 50


def test_ensure_dir(tmp_path):
    """Verify ensure_dir creates nested directories."""
    nested = tmp_path / "a" / "b" / "c"
    res = ensure_dir(nested)
    assert res.is_dir()
    assert res.exists()


def test_get_app_data_dir():
    """Verify get_app_data_dir returns a directory path that exists or can be created."""
    dir_path = get_app_data_dir("test_deepsearch_app")
    assert isinstance(dir_path, Path)
    assert dir_path.exists()


def test_open_in_browser_mock():
    """Verify open_in_browser handles URLs gracefully."""
    with patch("webbrowser.open", return_value=True):
        assert open_in_browser("https://example.com") is True
