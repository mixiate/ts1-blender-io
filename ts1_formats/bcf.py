"""Read and write The Sims 1 BCF files."""

import dataclasses
import pathlib
import struct
import typing

from . import error, pascal_string, property_list, skeleton


@dataclasses.dataclass
class TimeProperty:
    """A BCF time property."""

    time: int
    events: list[property_list.Property]


def read_time_properties(file: typing.BinaryIO) -> list[TimeProperty]:
    """Read BCF time properties from a file."""
    count = struct.unpack('<I', file.read(4))[0]
    return [
        TimeProperty(
            struct.unpack('<I', file.read(4))[0],
            property_list.read_properties(file, '<'),
        )
        for _ in range(count)
    ]


def write_time_properties(file: typing.BinaryIO, time_properties: list[TimeProperty]) -> None:
    """Write BCF time properties to a file."""
    file.write(struct.pack('<I', len(time_properties)))
    for time_property in time_properties:
        file.write(struct.pack('<I', time_property.time))
        property_list.write_properties(file, time_property.events, '<')


@dataclasses.dataclass
class TimePropertyList:
    """A BCF time property list."""

    time_properties: list[TimeProperty]


def read_time_property_lists(file: typing.BinaryIO) -> list[TimePropertyList]:
    """Read BCF time property lists from a file."""
    count = struct.unpack('<I', file.read(4))[0]
    return [
        TimePropertyList(
            read_time_properties(file),
        )
        for _ in range(count)
    ]


def write_time_property_lists(file: typing.BinaryIO, time_property_lists: list[TimePropertyList]) -> None:
    """Write BCF time property lists to a file."""
    file.write(struct.pack('<I', len(time_property_lists)))
    for time_property_list in time_property_lists:
        write_time_properties(file, time_property_list.time_properties)


@dataclasses.dataclass
class Motion:
    """A BCF motion."""

    bone_name: str
    frame_count: int
    duration: float
    positions_used_flag: int
    rotations_used_flag: int
    position_offset: int
    rotation_offset: int
    property_lists: list[property_list.PropertyList]
    time_property_lists: list[TimePropertyList]


def read_motions(file: typing.BinaryIO) -> list[Motion]:
    """Read BCF motions from a file."""
    count = struct.unpack('<I', file.read(4))[0]
    return [
        Motion(
            pascal_string.read_string(file),
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<f', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<i', file.read(4))[0],
            struct.unpack('<i', file.read(4))[0],
            property_list.read_property_lists(file, '<'),
            read_time_property_lists(file),
        )
        for _ in range(count)
    ]


def write_motions(file: typing.BinaryIO, motions: list[Motion]) -> None:
    """Write BCF motions to a file."""
    file.write(struct.pack('<I', len(motions)))
    for motion in motions:
        pascal_string.write_string(file, motion.bone_name)
        file.write(struct.pack('<I', motion.frame_count))
        file.write(struct.pack('<f', motion.duration))
        file.write(struct.pack('<I', motion.positions_used_flag))
        file.write(struct.pack('<I', motion.rotations_used_flag))
        file.write(struct.pack('<i', motion.position_offset))
        file.write(struct.pack('<i', motion.rotation_offset))
        property_list.write_property_lists(file, motion.property_lists, '<')
        write_time_property_lists(file, motion.time_property_lists)


@dataclasses.dataclass
class Skill:
    """A BCF skill."""

    skill_name: str
    animation_name: str
    duration: float
    distance: float
    moving_flag: int
    position_count: int
    rotation_count: int
    motions: list[Motion]


def read_skills(file: typing.BinaryIO) -> list[Skill]:
    """Read BCF skills from a file."""
    count = struct.unpack('<I', file.read(4))[0]
    return [
        Skill(
            pascal_string.read_string(file),
            pascal_string.read_string(file),
            struct.unpack('<f', file.read(4))[0],
            struct.unpack('<f', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
            read_motions(file),
        )
        for _ in range(count)
    ]


def write_skills(file: typing.BinaryIO, skills: list[Skill]) -> None:
    """Write BCF skills to a file."""
    file.write(struct.pack('<I', len(skills)))
    for skill in skills:
        pascal_string.write_string(file, skill.skill_name)
        pascal_string.write_string(file, skill.animation_name)
        file.write(struct.pack('<f', skill.duration))
        file.write(struct.pack('<f', skill.distance))
        file.write(struct.pack('<I', skill.moving_flag))
        file.write(struct.pack('<I', skill.position_count))
        file.write(struct.pack('<I', skill.rotation_count))
        write_motions(file, skill.motions)


@dataclasses.dataclass
class Skin:
    """A BCF skin."""

    bone_name: str
    skin_name: str
    censor_flags: int
    unknown: int


def read_skins(file: typing.BinaryIO) -> list[Skin]:
    """Read BCF skins from a file."""
    count = struct.unpack('<I', file.read(4))[0]
    return [
        Skin(
            pascal_string.read_string(file),
            pascal_string.read_string(file),
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
        )
        for _ in range(count)
    ]


def write_skins(file: typing.BinaryIO, skins: list[Skin]) -> None:
    """Write BCF skins to a file."""
    file.write(struct.pack('<I', len(skins)))
    for skin in skins:
        pascal_string.write_string(file, skin.bone_name)
        pascal_string.write_string(file, skin.skin_name)
        file.write(struct.pack('<I', skin.censor_flags))
        file.write(struct.pack('<I', skin.unknown))


@dataclasses.dataclass
class Suit:
    """A BCF suit."""

    name: str
    suit_type: int
    unknown: int
    skins: list[Skin]


def read_suits(file: typing.BinaryIO) -> list[Suit]:
    """Read BCF suits from a file."""
    count = struct.unpack('<I', file.read(4))[0]
    return [
        Suit(
            pascal_string.read_string(file),
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
            read_skins(file),
        )
        for _ in range(count)
    ]


def write_suits(file: typing.BinaryIO, suits: list[Suit]) -> None:
    """Write BCF suits to a file."""
    file.write(struct.pack('<I', len(suits)))
    for suit in suits:
        pascal_string.write_string(file, suit.name)
        file.write(struct.pack('<I', suit.suit_type))
        file.write(struct.pack('<I', suit.unknown))
        write_skins(file, suit.skins)


@dataclasses.dataclass
class Bcf:
    """Description of a BCF file."""

    skeletons: list[skeleton.Skeleton]
    suits: list[Suit]
    skills: list[Skill]


def read_bcf(file: typing.BinaryIO) -> Bcf:
    """Read a BCF from a file."""
    return Bcf(
        skeleton.read_skeletons(file, '<'),
        read_suits(file),
        read_skills(file),
    )


def write_bcf(file: typing.BinaryIO, bcf: Bcf) -> None:
    """Write a BCF to a file."""
    skeleton.write_skeletons(file, bcf.skeletons, '<')
    write_suits(file, bcf.suits)
    write_skills(file, bcf.skills)


def read_file(file_path: pathlib.Path) -> Bcf:
    """Read a file as a BCF."""
    try:
        with file_path.open(mode='rb') as file:
            bcf = read_bcf(file)

            if len(file.read(1)) != 0:
                raise error.FileReadError

            return bcf

    except (OSError, struct.error) as exception:
        raise error.FileReadError from exception


def write_file(file_path: pathlib.Path, bcf: Bcf) -> None:
    """Write a BCF to a file."""
    with file_path.open('wb') as file:
        write_bcf(file, bcf)
