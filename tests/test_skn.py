"""SKN format tests."""

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


def test_skn(tmp_path: Path, files_directory: str | None) -> None:
    """Test reading, writing and rereading all skn files in the specified directory."""
    if files_directory is None:
        pytest.skip("No file directory specified")

    file_list = Path(files_directory).rglob("*.skn")

    for file_path in file_list:
        skn_file = skn.read_file(file_path)

        output_file_path = tmp_path / file_path.name

        skn.write_file(output_file_path, skn_file)
        output_skn_file = skn.read_file(output_file_path)

        compare_skns(skn_file, output_skn_file)
