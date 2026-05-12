"""Read and write The Sims Online anim files."""

import dataclasses
import pathlib
import struct
import typing

from ts1_formats import pascal_string, property_list
from ts1_formats.error import FileReadError


@dataclasses.dataclass
class TimeProperty:
    """A time property."""

    time: int
    property_lists: list[property_list.PropertyList]


def read_time_properties(stream: typing.BinaryIO) -> list[TimeProperty]:
    """Read time properties from a stream."""
    count = struct.unpack('>I', stream.read(4))[0]
    return [
        TimeProperty(
            struct.unpack('>I', stream.read(4))[0],
            property_list.read_property_lists(stream, '>'),
        )
        for _ in range(count)
    ]


def write_time_properties(stream: typing.BinaryIO, time_properties: list[TimeProperty]) -> None:
    """Write time properties to a stream."""
    stream.write(struct.pack('>I', len(time_properties)))
    for time_property in time_properties:
        stream.write(struct.pack('>I', time_property.time))
        property_list.write_property_lists(stream, time_property.property_lists, '>')


@dataclasses.dataclass
class TimePropertyList:
    """A time property list."""

    time_properties: list[TimeProperty]


def read_time_property_lists(stream: typing.BinaryIO) -> list[TimePropertyList]:
    """Read time property lists from a stream."""
    count = struct.unpack('>I', stream.read(4))[0]
    return [
        TimePropertyList(
            read_time_properties(stream),
        )
        for _ in range(count)
    ]


def write_time_property_lists(stream: typing.BinaryIO, time_property_lists: list[TimePropertyList]) -> None:
    """Write time property lists to a stream."""
    stream.write(struct.pack('>I', len(time_property_lists)))
    for time_property_list in time_property_lists:
        write_time_properties(stream, time_property_list.time_properties)


@dataclasses.dataclass
class Motion:
    """An anim motion."""

    bone_name: str
    frame_count: int
    duration: float
    uses_positions: bool
    uses_rotations: bool
    position_offset: int
    rotation_offset: int
    property_lists: list[property_list.PropertyList]
    time_property_lists: list[TimePropertyList]


def read_motion(stream: typing.BinaryIO) -> Motion:
    """Read an anim motion from a stream."""
    stream.read(4)

    bone_name = pascal_string.read_string(stream)
    frame_count = struct.unpack('>I', stream.read(4))[0]
    duration = struct.unpack('<f', stream.read(4))[0]
    uses_positions = struct.unpack('<B', stream.read(1))[0] != 0
    uses_rotations = struct.unpack('<B', stream.read(1))[0] != 0
    position_offset = struct.unpack('>i', stream.read(4))[0]
    rotation_offset = struct.unpack('>i', stream.read(4))[0]

    has_property_lists = struct.unpack('<B', stream.read(1))[0]
    property_lists = property_list.read_property_lists(stream, '>') if has_property_lists else []

    has_time_property_lists = struct.unpack('<B', stream.read(1))[0]
    time_property_lists = read_time_property_lists(stream) if has_time_property_lists else []

    return Motion(
        bone_name,
        frame_count,
        duration,
        uses_positions,
        uses_rotations,
        position_offset,
        rotation_offset,
        property_lists,
        time_property_lists,
    )


def write_motion(stream: typing.BinaryIO, motion: Motion) -> None:
    """Write a motion to a stream."""
    stream.write(struct.pack('>I', 1))
    pascal_string.write_string(stream, motion.bone_name)
    stream.write(struct.pack('>I', motion.frame_count))
    stream.write(struct.pack('<f', motion.duration))
    stream.write(struct.pack('B', motion.uses_positions))
    stream.write(struct.pack('B', motion.uses_rotations))
    stream.write(struct.pack('>i', motion.position_offset))
    stream.write(struct.pack('>i', motion.rotation_offset))

    stream.write(struct.pack('B', len(motion.property_lists) != 0))
    if len(motion.property_lists):
        property_list.write_property_lists(stream, motion.property_lists, '>')

    stream.write(struct.pack('B', len(motion.time_property_lists) != 0))
    if len(motion.time_property_lists):
        write_time_property_lists(stream, motion.time_property_lists)


def write_translation(stream: typing.BinaryIO, translation: tuple[float, float, float]) -> None:
    """Write a translation to a stream."""
    stream.write(struct.pack('<3f', *translation))


def write_rotation(stream: typing.BinaryIO, rotation: tuple[float, float, float, float]) -> None:
    """Write a rotation to a stream."""
    stream.write(struct.pack('<4f', *rotation))


@dataclasses.dataclass
class Anim:
    """Description of an anim stream."""

    name: str
    duration: float
    distance: float
    moves: bool
    translations: list[tuple[float, float, float]]
    rotations: list[tuple[float, float, float, float]]
    motions: list[Motion]


def read_anim(stream: typing.BinaryIO) -> Anim:
    """Read an anim from a stream."""
    version = struct.unpack('>I', stream.read(4))[0]
    if version != 0x02:
        raise FileReadError

    name = pascal_string.read_string_16(stream, '>')

    duration = struct.unpack('<f', stream.read(4))[0]
    distance = struct.unpack('<f', stream.read(4))[0]
    moves = struct.unpack('<b', stream.read(1))[0] != 0

    translation_count = struct.unpack('>I', stream.read(4))[0]
    translations = [struct.unpack('<3f', stream.read(12)) for _ in range(translation_count)]

    rotation_count = struct.unpack('>I', stream.read(4))[0]
    rotations = [struct.unpack('<4f', stream.read(16)) for _ in range(rotation_count)]

    motions_count = struct.unpack('>I', stream.read(4))[0]
    motions = [read_motion(stream) for _ in range(motions_count)]

    return Anim(
        name,
        duration,
        distance,
        moves,
        translations,
        rotations,
        motions,
    )


def write_anim(stream: typing.BinaryIO, animation: Anim) -> None:
    """Write an anim to a stream."""
    stream.write(struct.pack('>I', 0x02))

    pascal_string.write_string_16(stream, animation.name, '>')

    stream.write(struct.pack('<f', animation.duration))
    stream.write(struct.pack('<f', animation.distance))
    stream.write(struct.pack('B', animation.moves))

    stream.write(struct.pack('>I', len(animation.translations)))
    for translation in animation.translations:
        write_translation(stream, translation)

    stream.write(struct.pack('>I', len(animation.rotations)))
    for rotation in animation.rotations:
        write_rotation(stream, rotation)

    stream.write(struct.pack('>I', len(animation.motions)))
    for motion in animation.motions:
        write_motion(stream, motion)


def read_file(file_path: pathlib.Path) -> Anim:
    """Read an anim file."""
    try:
        with file_path.open(mode='rb') as file:
            anim = read_anim(file)

            if len(file.read(1)) != 0:
                raise FileReadError

            return anim

    except (OSError, struct.error) as exception:
        raise FileReadError from exception


def write_file(file_path: pathlib.Path, animation: Anim) -> None:
    """Write an anim file."""
    with file_path.open('wb') as file:
        write_anim(file, animation)
