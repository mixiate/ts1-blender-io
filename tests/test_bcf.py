"""BCF format tests."""

import io
import multiprocessing
from pathlib import Path

import pytest

from ts1_formats import bcf


def roundtrip_bcf(file_path: Path) -> None:
    """Test reading, writing and rereading a bcf file."""
    bcf_file = bcf.read_file(file_path)

    byte_stream = io.BytesIO()
    bcf.write_bcf(byte_stream, bcf_file)

    assert byte_stream.tell() == file_path.stat().st_size

    byte_stream.seek(0)
    output_bcf_file = bcf.read_bcf(byte_stream)

    assert bcf_file == output_bcf_file


def test_bcf(files_directory: str | None) -> None:
    """Test reading, writing and rereading all bcf files in the specified directory."""
    if files_directory is None:
        pytest.skip("No file directory specified")

    file_list = Path(files_directory).rglob("*.bcf")

    pool = multiprocessing.Pool(None)
    pool.map(roundtrip_bcf, file_list)
