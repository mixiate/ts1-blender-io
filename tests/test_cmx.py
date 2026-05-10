"""CMX format tests."""

from pathlib import Path

from ts1_formats import cmx


def test_cmx(tmp_path: Path, files_directory: str) -> None:
    """Test reading, writing and rereading all cmx files in the specified directory."""
    file_list = Path(files_directory).rglob("*.cmx")

    for file_path in file_list:
        cmx_file = cmx.read_file(file_path)

        output_file_path = tmp_path / file_path.name

        cmx.write_file(output_file_path, cmx_file)
        output_cmx_file = cmx.read_file(output_file_path)

        assert cmx_file == output_cmx_file
