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


def read_string_16(stream: typing.BinaryIO, endianness: str) -> str:
    """Read a pascal string with 2 byte length from a stream."""
    length = struct.unpack(endianness + 'H', stream.read(2))[0]
    return stream.read(length).decode("windows-1252")


def write_string_16(stream: typing.BinaryIO, string: str, endianness: str) -> None:
    """Write a pascal string with 2 byte length to a stream."""
    stream.write(struct.pack(endianness + 'H', len(string)))
    stream.write(string.encode("windows-1252"))
