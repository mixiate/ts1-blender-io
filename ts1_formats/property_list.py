"""Read and write The Sims property lists."""

import dataclasses
import struct
import typing

from . import pascal_string


@dataclasses.dataclass
class Property:
    """A property."""

    name: str
    value: str


def read_properties(file: typing.BinaryIO, endianness: str) -> list[Property]:
    """Read properties from a stream."""
    count = struct.unpack(endianness + 'I', file.read(4))[0]
    return [
        Property(
            pascal_string.read_string(file),
            pascal_string.read_string(file),
        )
        for _ in range(count)
    ]


def write_properties(file: typing.BinaryIO, properties: list[Property], endianness: str) -> None:
    """Write properties to a stream."""
    file.write(struct.pack(endianness + 'I', len(properties)))
    for prop in properties:
        pascal_string.write_string(file, prop.name)
        pascal_string.write_string(file, prop.value)


@dataclasses.dataclass
class PropertyList:
    """A property list."""

    properties: list[Property]


def read_property_lists(file: typing.BinaryIO, endianness: str) -> list[PropertyList]:
    """Read property lists from a stream."""
    count = struct.unpack(endianness + 'I', file.read(4))[0]
    return [
        PropertyList(
            read_properties(file, endianness),
        )
        for _ in range(count)
    ]


def write_property_lists(file: typing.BinaryIO, property_lists: list[PropertyList], endianness: str) -> None:
    """Write property lists to a stream."""
    file.write(struct.pack(endianness + 'I', len(property_lists)))
    for property_list in property_lists:
        write_properties(file, property_list.properties, endianness)


@dataclasses.dataclass
class TimeProperty:
    """A time property."""

    time: int
    events: list[Property]
