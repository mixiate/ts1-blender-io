"""BCF format tests."""

from pathlib import Path

from ts1_formats import bcf


def test_bcf(tmp_path: Path, files_directory: str) -> None:
    """Test reading, writing and rereading all bcf files in the specified directory."""
    file_list = Path(files_directory).rglob("*.bcf")

    for file_path in file_list:
        bcf_file = bcf.read_file(file_path)

        output_file_path = tmp_path / file_path.name

        bcf.write_file(output_file_path, bcf_file)
        output_bcf_file = bcf.read_file(output_file_path)

        assert bcf_file == output_bcf_file
