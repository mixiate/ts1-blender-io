"""SKN format tests."""

import io
import multiprocessing
from pathlib import Path
import pytest

from ts1_formats import bmf
from ts1_formats import skn


def compare_skns(a: bmf.Bmf, b: bmf.Bmf) -> None:
    """Compare two deserialized skn files.

    Skips comparing floats as they're serialized to text.
    """
    assert a.skin_name == b.skin_name
    assert a.default_texture_name == b.default_texture_name
    assert a.bones == b.bones
    assert a.faces == b.faces
    assert a.bone_bindings == b.bone_bindings
    assert a.blends == b.blends


def roundtrip_skn(file_path: Path) -> None:
    """Test reading, writing and rereading a skn file."""
    skn_file = skn.read_file(file_path)

    string_stream = io.StringIO()
    skn.write_skn(string_stream, skn_file)

    assert string_stream.tell() != 0

    string_stream.seek(0)
    output_skn_file = skn.read_skn(string_stream)

    compare_skns(skn_file, output_skn_file)


def test_skn(files_directory: str | None) -> None:
    """Test reading, writing and rereading all skn files in the specified directory."""
    if files_directory is None:
        pytest.skip("No file directory specified")

    file_list = Path(files_directory).rglob("*.skn")

    pool = multiprocessing.Pool(None)
    pool.map(roundtrip_skn, file_list)
