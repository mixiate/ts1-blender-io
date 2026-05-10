"""BMF format tests."""

from pathlib import Path

from ts1_formats import bmf


def test_bmf(tmp_path: Path, files_directory: str) -> None:
    """Test reading, writing and rereading all bmf files in the specified directory."""
    file_list = Path(files_directory).rglob("*.bmf")

    for file_path in file_list:
        bmf_file = bmf.read_file(file_path)

        output_file_path = tmp_path / file_path.name

        bmf.write_file(output_file_path, bmf_file)
        output_bmf_file = bmf.read_file(output_file_path)

        assert bmf_file == output_bmf_file
