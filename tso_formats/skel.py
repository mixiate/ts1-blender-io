"""Read and write The Sims Online skel files."""

import pathlib
import struct
import typing

from ts1_formats import pascal_string, skeleton
from ts1_formats.error import FileReadError


def read_skel(stream: typing.BinaryIO) -> skeleton.Skeleton:
    """Read a skel from a stream."""
    version = struct.unpack('>I', stream.read(4))[0]
    if version != 1:
        raise FileReadError

    name = pascal_string.read_string(stream)

    bone_count = struct.unpack('>H', stream.read(2))[0]
    bones = [skeleton.read_bone(stream, '>', skel_format=True) for _ in range(bone_count)]

    return skeleton.Skeleton(name, bones)


def read_file(file_path: pathlib.Path) -> skeleton.Skeleton:
    """Read a skel file."""
    try:
        with file_path.open(mode='rb') as file:
            skel = read_skel(file)

            if len(file.read(1)) != 0:
                raise FileReadError

            return skel

    except (OSError, struct.error) as exception:
        raise FileReadError from exception
