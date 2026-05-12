"""Read and write The Sims Online mesh files."""

import pathlib
import struct
import typing

from ts1_formats import bmf
from ts1_formats.error import FileReadError


def read_mesh(stream: typing.BinaryIO) -> bmf.Mesh:
    """Read a mesh file from a stream."""
    version = struct.unpack('>I', stream.read(4))[0]
    if version != 2:
        raise FileReadError

    return bmf.read_mesh(stream, '>')


def write_mesh(stream: typing.BinaryIO, mesh: bmf.Mesh) -> None:
    """Write a mesh file to a stream."""
    stream.write(struct.pack('>I', 2))  # version
    bmf.write_mesh(stream, mesh, '>')


def read_file(file_path: pathlib.Path) -> bmf.Mesh:
    """Read a mesh file."""
    try:
        with file_path.open(mode='rb') as file:
            mesh = read_mesh(file)

            if len(file.read(1)) != 0:
                raise FileReadError

            return mesh

    except (OSError, struct.error) as exception:
        raise FileReadError from exception


def write_file(file_path: pathlib.Path, mesh: bmf.Mesh) -> None:
    """Write a mesh file."""
    with file_path.open('wb') as file:
        write_mesh(file, mesh)
