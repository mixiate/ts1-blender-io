"""MESH format tests."""

import io
import multiprocessing
from pathlib import Path

import pytest

from ts1_formats import mesh


def roundtrip_mesh(file_path: Path) -> None:
    """Test reading, writing and rereading a mesh file."""
    input_mesh = mesh.read_file(file_path)

    byte_stream = io.BytesIO()
    mesh.write_mesh(byte_stream, input_mesh)

    assert byte_stream.tell() == file_path.stat().st_size

    byte_stream.seek(0)
    output_mesh = mesh.read_mesh(byte_stream)

    assert input_mesh == output_mesh


def test_mesh(files_directory: str | None) -> None:
    """Test reading, writing and rereading all mesh files in the specified directory."""
    if files_directory is None:
        pytest.skip("No file directory specified")

    file_list = Path(files_directory).rglob("*.mesh")

    pool = multiprocessing.Pool(None)
    pool.map(roundtrip_mesh, file_list)
