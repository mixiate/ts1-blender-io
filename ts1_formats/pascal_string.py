"""Read and write pascal strings."""

import struct
import typing


def read_string(stream: typing.BinaryIO) -> str:
    """Read a pascal string from a stream."""
    length = struct.unpack('B', stream.read(1))[0]
    return stream.read(length).decode("windows-1252")


def write_string(stream: typing.BinaryIO, string: str) -> None:
    """Write a pascal string to a stream."""
    stream.write(struct.pack('B', len(string)))
    stream.write(string.encode("windows-1252"))
