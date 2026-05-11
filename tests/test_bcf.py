"""BCF format tests."""

import itertools
import multiprocessing
from pathlib import Path

from ts1_formats import bcf


def roundtrip_bcf(file_path: Path, tmp_path: Path) -> None:
    """Test reading, writing and rereading a bcf file."""
    bcf_file = bcf.read_file(file_path)

    output_file_path = tmp_path / file_path.name

    bcf.write_file(output_file_path, bcf_file)
    output_bcf_file = bcf.read_file(output_file_path)

    assert bcf_file == output_bcf_file


def test_bcf(tmp_path: Path, files_directory: str) -> None:
    """Test reading, writing and rereading all bcf files in the specified directory."""
    file_list = Path(files_directory).rglob("*.bcf")

    pool = multiprocessing.Pool(None)
    pool.starmap(roundtrip_bcf, zip(file_list, itertools.repeat(tmp_path)))
