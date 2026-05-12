"""Read and write The Sims skeletons."""

import dataclasses
import struct
import typing

from . import error, pascal_string, property_list


@dataclasses.dataclass
class Bone:
    """Skeleton bone."""

    name: str
    parent: str
    property_lists: list[property_list.PropertyList]
    position: tuple[float, float, float]
    rotation: tuple[float, float, float, float]
    translate: bool
    rotate: bool
    blend: bool
    wiggle_value: float
    wiggle_power: float


def read_bone(stream: typing.BinaryIO, endianness: str, *, skel_format: bool) -> Bone:
    """Read a bone from a stream."""
    if skel_format:
        version = struct.unpack(endianness + 'I', stream.read(4))[0]
        if version != 1:
            raise error.FileReadError

    name = pascal_string.read_string(stream)
    parent = pascal_string.read_string(stream)

    has_properties = bool(struct.unpack('B', stream.read(1))[0]) if skel_format else True

    return Bone(
        name,
        parent,
        property_list.read_property_lists(stream, endianness) if has_properties else [],
        struct.unpack('<3f', stream.read(12)),
        struct.unpack('<4f', stream.read(16)),
        bool(struct.unpack(endianness + 'I', stream.read(4))[0]),
        bool(struct.unpack(endianness + 'I', stream.read(4))[0]),
        bool(struct.unpack(endianness + 'I', stream.read(4))[0]),
        struct.unpack('<f', stream.read(4))[0],
        struct.unpack('<f', stream.read(4))[0],
    )


def read_bones(stream: typing.BinaryIO, endianness: str) -> list[Bone]:
    """Read bones from a stream."""
    count = struct.unpack(endianness + 'I', stream.read(4))[0]
    return [read_bone(stream, endianness, skel_format=False) for _ in range(count)]


def write_bones(stream: typing.BinaryIO, bones: list[Bone], endianness: str) -> None:
    """Write bones to a stream."""
    stream.write(struct.pack(endianness + 'I', len(bones)))
    for bone in bones:
        pascal_string.write_string(stream, bone.name)
        pascal_string.write_string(stream, bone.parent)
        property_list.write_property_lists(stream, bone.property_lists, endianness)
        stream.write(struct.pack(endianness + '3f', *bone.position))
        stream.write(struct.pack(endianness + '4f', *bone.rotation))
        stream.write(struct.pack(endianness + 'I', bone.translate))
        stream.write(struct.pack(endianness + 'I', bone.rotate))
        stream.write(struct.pack(endianness + 'I', bone.blend))
        stream.write(struct.pack(endianness + 'f', bone.wiggle_value))
        stream.write(struct.pack(endianness + 'f', bone.wiggle_power))


@dataclasses.dataclass
class Skeleton:
    """The Sims skeleton."""

    name: str
    bones: list[Bone]


def read_skeletons(stream: typing.BinaryIO, endianness: str) -> list[Skeleton]:
    """Read skeletons from a stream."""
    count = struct.unpack(endianness + 'I', stream.read(4))[0]
    return [
        Skeleton(
            pascal_string.read_string(stream),
            read_bones(stream, endianness),
        )
        for _ in range(count)
    ]


def write_skeletons(stream: typing.BinaryIO, skeletons: list[Skeleton], endianness: str) -> None:
    """Write skeletons to a stream."""
    stream.write(struct.pack(endianness + 'I', len(skeletons)))
    for skeleton in skeletons:
        pascal_string.write_string(stream, skeleton.name)
        write_bones(stream, skeleton.bones, endianness)
