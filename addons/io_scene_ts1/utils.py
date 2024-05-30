"""Utility functions and classes."""

import math
import mathutils
import struct
import typing


BONE_SCALE = 3.0
BONE_ROTATION_OFFSET = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'Z')
BONE_ROTATION_OFFSET_INVERTED = BONE_ROTATION_OFFSET.inverted()


def read_string(file: typing.BinaryIO) -> str:
    """Read a pascal string from a file."""
    length = struct.unpack('<B', file.read(1))[0]
    return struct.unpack("%ds" % length, file.read(length))[0].decode("windows-1252")


def write_string(file: typing.BinaryIO, string: str) -> None:
    """Write a pascal string to a file."""
    file.write(struct.pack('<B', len(string)))
    file.write(string.encode("windows-1252"))


class FileReadError(Exception):
    """General purpose file read error."""
