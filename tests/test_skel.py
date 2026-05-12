"""SKEL format tests."""

from pathlib import Path

import pytest

from tso_formats import skel


def test_skel(files_directory: str | None) -> None:
    """Test reading all skel files in the specified directory."""
    if files_directory is None:
        pytest.skip("No file directory specified")

    file_list = Path(files_directory).rglob("*.skel")
    for file_path in file_list:
        skel.read_file(file_path)
