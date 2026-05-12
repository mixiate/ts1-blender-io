"""The Sims Online anim format tests."""

import io
import multiprocessing
from pathlib import Path

import pytest

from ts1_formats import anim


def roundtrip_anim(file_path: Path) -> None:
    """Test reading, writing and rereading an anim file."""
    input_anim = anim.read_file(file_path)

    byte_stream = io.BytesIO()
    anim.write_anim(byte_stream, input_anim)

    assert byte_stream.tell() == file_path.stat().st_size

    byte_stream.seek(0)
    output_anim = anim.read_anim(byte_stream)

    assert input_anim == output_anim


def test_anim(files_directory: str | None) -> None:
    """Test reading, writing and rereading all anim files in the specified directory."""
    if files_directory is None:
        pytest.skip("No file directory specified")

    file_list = Path(files_directory).rglob("*.anim")

    pool = multiprocessing.Pool(None)
    pool.map(roundtrip_anim, file_list)
