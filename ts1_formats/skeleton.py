"""Read and write The Sims skeletons."""

import dataclasses
import struct
import typing

from . import pascal_string
from . import property_list


@dataclasses.dataclass
class Bone:
    """Skeleton bone."""

    name: str
    parent: str
    property_lists: list[property_list.PropertyList]
    position_x: float
    position_y: float
    position_z: float
    rotation_x: float
    rotation_y: float
    rotation_z: float
    rotation_w: float
    translate: int
    rotate: int
    blend_suits: int
    wiggle_value: float
    wiggle_power: float


def read_bones(stream: typing.BinaryIO) -> list[Bone]:
    """Read bones from a stream."""
    count = struct.unpack('<I', stream.read(4))[0]
    return [
        Bone(
            pascal_string.read_string(stream),
            pascal_string.read_string(stream),
            property_list.read_property_lists(stream, '<'),
            struct.unpack('<f', stream.read(4))[0],
            struct.unpack('<f', stream.read(4))[0],
            struct.unpack('<f', stream.read(4))[0],
            struct.unpack('<f', stream.read(4))[0],
            struct.unpack('<f', stream.read(4))[0],
            struct.unpack('<f', stream.read(4))[0],
            struct.unpack('<f', stream.read(4))[0],
            struct.unpack('<I', stream.read(4))[0],
            struct.unpack('<I', stream.read(4))[0],
            struct.unpack('<I', stream.read(4))[0],
            struct.unpack('<f', stream.read(4))[0],
            struct.unpack('<f', stream.read(4))[0],
        )
        for _ in range(count)
    ]


def write_bones(stream: typing.BinaryIO, bones: list[Bone]) -> None:
    """Write bones to a stream."""
    stream.write(struct.pack('<I', len(bones)))
    for bone in bones:
        pascal_string.write_string(stream, bone.name)
        pascal_string.write_string(stream, bone.parent)
        property_list.write_property_lists(stream, bone.property_lists, '<')
        stream.write(struct.pack('<f', bone.position_x))
        stream.write(struct.pack('<f', bone.position_y))
        stream.write(struct.pack('<f', bone.position_z))
        stream.write(struct.pack('<f', bone.rotation_x))
        stream.write(struct.pack('<f', bone.rotation_y))
        stream.write(struct.pack('<f', bone.rotation_z))
        stream.write(struct.pack('<f', bone.rotation_w))
        stream.write(struct.pack('<I', bone.translate))
        stream.write(struct.pack('<I', bone.rotate))
        stream.write(struct.pack('<I', bone.blend_suits))
        stream.write(struct.pack('<f', bone.wiggle_value))
        stream.write(struct.pack('<f', bone.wiggle_power))


@dataclasses.dataclass
class Skeleton:
    """The Sims skeleton."""

    name: str
    bones: list[Bone]


def read_skeletons(stream: typing.BinaryIO) -> list[Skeleton]:
    """Read skeletons from a stream."""
    count = struct.unpack('<I', stream.read(4))[0]
    return [
        Skeleton(
            pascal_string.read_string(stream),
            read_bones(stream),
        )
        for _ in range(count)
    ]


def write_skeletons(stream: typing.BinaryIO, skeletons: list[Skeleton]) -> None:
    """Write skeletons to a stream."""
    stream.write(struct.pack('<I', len(skeletons)))
    for skeleton in skeletons:
        pascal_string.write_string(stream, skeleton.name)
        write_bones(stream, skeleton.bones)
