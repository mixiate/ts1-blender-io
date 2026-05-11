"""BMF format tests."""

import io
import multiprocessing
from pathlib import Path
import pytest

from ts1_formats import bmf


def roundtrip_bmf(file_path: Path) -> None:
    """Test reading, writing and rereading a bmf file."""
    bmf_file = bmf.read_file(file_path)

    byte_stream = io.BytesIO()
    bmf.write_bmf(byte_stream, bmf_file)

    assert byte_stream.tell() == file_path.stat().st_size

    byte_stream.seek(0)
    output_bmf_file = bmf.read_bmf(byte_stream)

    assert bmf_file == output_bmf_file


def test_bmf(files_directory: str | None) -> None:
    """Test reading, writing and rereading all bmf files in the specified directory."""
    if files_directory is None:
        pytest.skip("No file directory specified")

    file_list = Path(files_directory).rglob("*.bmf")

    pool = multiprocessing.Pool(None)
    pool.map(roundtrip_bmf, file_list)
