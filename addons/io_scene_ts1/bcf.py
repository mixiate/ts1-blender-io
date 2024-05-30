"""Read and write The Sims 1 BCF files."""

import dataclasses
import pathlib
import struct
import typing


from . import utils


@dataclasses.dataclass
class Property:
    """A BCF property."""

    name: str
    value: str


def read_properties(file: typing.BinaryIO) -> list[Property]:
    """Read BCF properties from a file."""
    count = struct.unpack('<I', file.read(4))[0]
    return [
        Property(
            utils.read_string(file),
            utils.read_string(file),
        )
        for _ in range(count)
    ]


def write_properties(file: typing.BinaryIO, properties: list[Property]) -> None:
    """Write BCF properties to a file."""
    file.write(struct.pack('<I', len(properties)))
    for prop in properties:
        utils.write_string(file, prop.name)
        utils.write_string(file, prop.value)


@dataclasses.dataclass
class PropertyList:
    """A BCF property list."""

    properties: list[Property]


def read_property_lists(file: typing.BinaryIO) -> list[PropertyList]:
    """Read BCF property lists from a file."""
    count = struct.unpack('<I', file.read(4))[0]
    return [
        PropertyList(
            read_properties(file),
        )
        for _ in range(count)
    ]


def write_property_lists(file: typing.BinaryIO, property_lists: list[PropertyList]) -> None:
    """Write BCF property lists to a file."""
    file.write(struct.pack('<I', len(property_lists)))
    for property_list in property_lists:
        write_properties(file, property_list.properties)


@dataclasses.dataclass
class TimeProperty:
    """A BCF time property."""

    time: int
    events: list[Property]


def read_time_properties(file: typing.BinaryIO) -> list[TimeProperty]:
    """Read BCF time properties from a file."""
    count = struct.unpack('<I', file.read(4))[0]
    return [
        TimeProperty(
            struct.unpack('<I', file.read(4))[0],
            read_properties(file),
        )
        for _ in range(count)
    ]


def write_time_properties(file: typing.BinaryIO, time_properties: list[TimeProperty]) -> None:
    """Write BCF time properties to a file."""
    file.write(struct.pack('<I', len(time_properties)))
    for time_property in time_properties:
        file.write(struct.pack('<I', time_property.time))
        write_properties(file, time_property.events)


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
    property_lists: list[PropertyList]
    time_property_lists: list[TimePropertyList]


def read_motions(file: typing.BinaryIO) -> list[Motion]:
    """Read BCF motions from a file."""
    count = struct.unpack('<I', file.read(4))[0]
    return [
        Motion(
            utils.read_string(file),
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<f', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<i', file.read(4))[0],
            struct.unpack('<i', file.read(4))[0],
            read_property_lists(file),
            read_time_property_lists(file),
        )
        for _ in range(count)
    ]


def write_motions(file: typing.BinaryIO, motions: list[Motion]) -> None:
    """Write BCF motions to a file."""
    file.write(struct.pack('<I', len(motions)))
    for motion in motions:
        utils.write_string(file, motion.bone_name)
        file.write(struct.pack('<I', motion.frame_count))
        file.write(struct.pack('<f', motion.duration))
        file.write(struct.pack('<I', motion.positions_used_flag))
        file.write(struct.pack('<I', motion.rotations_used_flag))
        file.write(struct.pack('<i', motion.position_offset))
        file.write(struct.pack('<i', motion.rotation_offset))
        write_property_lists(file, motion.property_lists)
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
            utils.read_string(file),
            utils.read_string(file),
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
        utils.write_string(file, skill.skill_name)
        utils.write_string(file, skill.animation_name)
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
            utils.read_string(file),
            utils.read_string(file),
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
        )
        for _ in range(count)
    ]


def write_skins(file: typing.BinaryIO, skins: list[Skin]) -> None:
    """Write BCF skins to a file."""
    file.write(struct.pack('<I', len(skins)))
    for skin in skins:
        utils.write_string(file, skin.bone_name)
        utils.write_string(file, skin.skin_name)
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
            utils.read_string(file),
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
        utils.write_string(file, suit.name)
        file.write(struct.pack('<I', suit.suit_type))
        file.write(struct.pack('<I', suit.unknown))
        write_skins(file, suit.skins)


@dataclasses.dataclass
class Bone:
    """A BCF bone."""

    name: str
    parent: str
    property_lists: list[PropertyList]
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


def read_bones(file: typing.BinaryIO) -> list[Bone]:
    """Read BCF bones from a file."""
    count = struct.unpack('<I', file.read(4))[0]
    return [
        Bone(
            utils.read_string(file),
            utils.read_string(file),
            read_property_lists(file),
            struct.unpack('<f', file.read(4))[0],
            struct.unpack('<f', file.read(4))[0],
            struct.unpack('<f', file.read(4))[0],
            struct.unpack('<f', file.read(4))[0],
            struct.unpack('<f', file.read(4))[0],
            struct.unpack('<f', file.read(4))[0],
            struct.unpack('<f', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<f', file.read(4))[0],
            struct.unpack('<f', file.read(4))[0],
        )
        for _ in range(count)
    ]


def write_bones(file: typing.BinaryIO, bones: list[Bone]) -> None:
    """Write BCF bones to a file."""
    file.write(struct.pack('<I', len(bones)))
    for bone in bones:
        utils.write_string(file, bone.name)
        utils.write_string(file, bone.parent)
        write_property_lists(file, bone.property_lists)
        file.write(struct.pack('<f', bone.position_x))
        file.write(struct.pack('<f', bone.position_y))
        file.write(struct.pack('<f', bone.position_z))
        file.write(struct.pack('<f', bone.rotation_x))
        file.write(struct.pack('<f', bone.rotation_y))
        file.write(struct.pack('<f', bone.rotation_z))
        file.write(struct.pack('<f', bone.rotation_w))
        file.write(struct.pack('<I', bone.translate))
        file.write(struct.pack('<I', bone.rotate))
        file.write(struct.pack('<I', bone.blend_suits))
        file.write(struct.pack('<f', bone.wiggle_value))
        file.write(struct.pack('<f', bone.wiggle_power))


@dataclasses.dataclass
class Skeleton:
    """A BCF skeleton."""

    name: str
    bones: list[Bone]


def read_skeletons(file: typing.BinaryIO) -> list[Skeleton]:
    """Read BCF skeletons from a file."""
    count = struct.unpack('<I', file.read(4))[0]
    return [
        Skeleton(
            utils.read_string(file),
            read_bones(file),
        )
        for _ in range(count)
    ]


def write_skeletons(file: typing.BinaryIO, skeletons: list[Skeleton]) -> None:
    """Write BCF skeletons to a file."""
    file.write(struct.pack('<I', len(skeletons)))
    for skeleton in skeletons:
        utils.write_string(file, skeleton.name)
        write_bones(file, skeleton.bones)


@dataclasses.dataclass
class Bcf:
    """Description of a BCF file."""

    skeletons: list[Skeleton]
    suits: list[Suit]
    skills: list[Skill]


def read_bcf(file: typing.BinaryIO) -> Bcf:
    """Read a BCF from a file."""
    return Bcf(
        read_skeletons(file),
        read_suits(file),
        read_skills(file),
    )


def write_bcf(file: typing.BinaryIO, bcf: Bcf) -> None:
    """Write a BCF to a file."""
    write_skeletons(file, bcf.skeletons)
    write_suits(file, bcf.suits)
    write_skills(file, bcf.skills)


def read_file(file_path: pathlib.Path) -> Bcf:
    """Read a file as a BCF."""
    try:
        with file_path.open(mode='rb') as file:
            bcf = read_bcf(file)

            if len(file.read(1)) != 0:
                raise utils.FileReadError

            return bcf

    except (OSError, struct.error) as exception:
        raise utils.FileReadError from exception


def write_file(file_path: pathlib.Path, bcf: Bcf) -> None:
    """Write a BCF to a file."""
    with file_path.open('wb') as file:
        write_bcf(file, bcf)
