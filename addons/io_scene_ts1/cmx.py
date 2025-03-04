"""Read and write The Sims 1 CMX files."""

import pathlib
import typing


from . import bcf
from . import utils


def read_properties(file: typing.TextIO) -> list[bcf.Property]:
    """Read BCF properties from a CMX file."""
    count = int(file.readline())
    return [
        bcf.Property(
            file.readline().strip(),
            file.readline().strip(),
        )
        for _ in range(count)
    ]


def write_properties(file: typing.TextIO, properties: list[bcf.Property]) -> None:
    """Write BCF properties to a CMX file."""
    file.write(str(len(properties)) + "\n")
    for prop in properties:
        file.write(prop.name + "\n")
        file.write(prop.value + "\n")


def read_property_lists(file: typing.TextIO) -> list[bcf.PropertyList]:
    """Read BCF property lists from a CMX file."""
    count = int(file.readline())
    return [
        bcf.PropertyList(
            read_properties(file),
        )
        for _ in range(count)
    ]


def write_property_lists(file: typing.TextIO, property_lists: list[bcf.PropertyList]) -> None:
    """Write BCF property lists to a CMX file."""
    file.write(str(len(property_lists)) + "\n")
    for property_list in property_lists:
        write_properties(file, property_list.properties)


def read_time_properties(file: typing.TextIO) -> list[bcf.TimeProperty]:
    """Read BCF time properties from a CMX file."""
    count = int(file.readline())
    return [
        bcf.TimeProperty(
            int(file.readline()),
            read_properties(file),
        )
        for _ in range(count)
    ]


def write_time_properties(file: typing.TextIO, time_properties: list[bcf.TimeProperty]) -> None:
    """Write BCF time properties to a CMX file."""
    file.write(str(len(time_properties)) + "\n")
    for time_property in time_properties:
        file.write(str(time_property.time) + "\n")
        write_properties(file, time_property.events)


def read_time_property_lists(file: typing.TextIO) -> list[bcf.TimePropertyList]:
    """Read BCF time property lists from a CMX file."""
    count = int(file.readline())
    return [
        bcf.TimePropertyList(
            read_time_properties(file),
        )
        for _ in range(count)
    ]


def write_time_property_lists(file: typing.TextIO, time_property_lists: list[bcf.TimePropertyList]) -> None:
    """Write BCF time property lists to a CMX file."""
    file.write(str(len(time_property_lists)) + "\n")
    for time_property_list in time_property_lists:
        write_time_properties(file, time_property_list.time_properties)


def read_motions(file: typing.TextIO) -> list[bcf.Motion]:
    """Read BCF motions from a CMX file."""
    count = int(file.readline())
    return [
        bcf.Motion(
            file.readline().strip(),
            int(file.readline()),
            float(file.readline()),
            int(file.readline()),
            int(file.readline()),
            int(file.readline()),
            int(file.readline()),
            read_property_lists(file),
            read_time_property_lists(file),
        )
        for _ in range(count)
    ]


def write_motions(file: typing.TextIO, motions: list[bcf.Motion]) -> None:
    """Write BCF motions to a CMX file."""
    file.write(str(len(motions)) + "\n")
    for motion in motions:
        file.write(motion.bone_name + "\n")
        file.write(str(motion.frame_count) + "\n")
        file.write(str(motion.duration) + "\n")
        file.write(str(motion.positions_used_flag) + "\n")
        file.write(str(motion.rotations_used_flag) + "\n")
        file.write(str(motion.position_offset) + "\n")
        file.write(str(motion.rotation_offset) + "\n")
        write_property_lists(file, motion.property_lists)
        write_time_property_lists(file, motion.time_property_lists)


def read_skills(file: typing.TextIO) -> list[bcf.Skill]:
    """Read BCF skills from a CMX file."""
    count = int(file.readline())
    return [
        bcf.Skill(
            file.readline().strip(),
            file.readline().strip(),
            float(file.readline()),
            float(file.readline()),
            int(file.readline()),
            int(file.readline()),
            int(file.readline()),
            read_motions(file),
        )
        for _ in range(count)
    ]


def write_skills(file: typing.TextIO, skills: list[bcf.Skill]) -> None:
    """Write BCF skills to a CMX file."""
    file.write(str(len(skills)) + "\n")
    for skill in skills:
        file.write(skill.skill_name + "\n")
        file.write(skill.animation_name + "\n")
        file.write(str(skill.duration) + "\n")
        file.write(str(skill.distance) + "\n")
        file.write(str(skill.moving_flag) + "\n")
        file.write(str(skill.position_count) + "\n")
        file.write(str(skill.rotation_count) + "\n")
        write_motions(file, skill.motions)


def read_skins(file: typing.TextIO) -> list[bcf.Skin]:
    """Read BCF skins from a CMX file."""
    count = int(file.readline())
    return [
        bcf.Skin(
            file.readline().strip(),
            file.readline().strip(),
            int(file.readline()),
            int(file.readline()),
        )
        for _ in range(count)
    ]


def write_skins(file: typing.TextIO, skins: list[bcf.Skin]) -> None:
    """Write BCF skins to a CMX file."""
    file.write(str(len(skins)) + "\n")
    for skin in skins:
        file.write(skin.bone_name + "\n")
        file.write(skin.skin_name + "\n")
        file.write(str(skin.censor_flags) + "\n")
        file.write(str(skin.unknown) + "\n")


def read_suits(file: typing.TextIO) -> list[bcf.Suit]:
    """Read BCF suits from a CMX file."""
    count = int(file.readline())
    return [
        bcf.Suit(
            file.readline().strip(),
            int(file.readline()),
            int(file.readline()),
            read_skins(file),
        )
        for _ in range(count)
    ]


def write_suits(file: typing.TextIO, suits: list[bcf.Suit]) -> None:
    """Write BCF suits to a CMX file."""
    file.write(str(len(suits)) + "\n")
    for suit in suits:
        file.write(suit.name + "\n")
        file.write(str(suit.suit_type) + "\n")
        file.write(str(suit.unknown) + "\n")
        write_skins(file, suit.skins)


def read_bones(file: typing.TextIO) -> list[bcf.Bone]:
    """Read BCF bones from a CMX file."""
    count = int(file.readline())
    bones = []
    for _ in range(count):
        name = file.readline().strip()
        parent = file.readline().strip()
        properties = read_property_lists(file)
        position = file.readline().strip().split("|")[1].strip().split(" ")
        quaternion = file.readline().strip().split("|")[1].strip().split(" ")
        translate = int(file.readline())
        rotate = int(file.readline())
        blend_suits = int(file.readline())
        wiggle_value = float(file.readline())
        wiggle_power = float(file.readline())
        bones.append(
            bcf.Bone(
                name,
                parent,
                properties,
                float(position[0]),
                float(position[1]),
                float(position[2]),
                float(quaternion[0]),
                float(quaternion[1]),
                float(quaternion[2]),
                float(quaternion[3]),
                translate,
                rotate,
                blend_suits,
                wiggle_value,
                wiggle_power,
            ),
        )
    return bones


def write_bones(file: typing.TextIO, bones: list[bcf.Bone]) -> None:
    """Write BCF bones to a CMX file."""
    file.write(str(len(bones)) + "\n")
    for bone in bones:
        file.write(bone.name + "\n")
        file.write(bone.parent + "\n")
        write_property_lists(file, bone.property_lists)
        file.write(f"| {bone.position_x} {bone.position_y} {bone.position_z} |\n")
        file.write(f"| {bone.rotation_x} {bone.rotation_y} {bone.rotation_z} {bone.rotation_w} |\n")
        file.write(str(bone.translate) + "\n")
        file.write(str(bone.rotate) + "\n")
        file.write(str(bone.blend_suits) + "\n")
        file.write(str(bone.wiggle_value) + "\n")
        file.write(str(bone.wiggle_power) + "\n")


def read_skeletons(file: typing.TextIO) -> list[bcf.Skeleton]:
    """Read BCF skeletons from a CMX file."""
    count = int(file.readline())
    return [
        bcf.Skeleton(
            file.readline().strip(),
            read_bones(file),
        )
        for _ in range(count)
    ]


def write_skeletons(file: typing.TextIO, skeletons: list[bcf.Skeleton]) -> None:
    """Write BCF skeletons to a CMX file."""
    file.write(str(len(skeletons)) + "\n")
    for skeleton in skeletons:
        file.write(skeleton.name + "\n")
        write_bones(file, skeleton.bones)


def read_cmx(file: typing.TextIO) -> bcf.Bcf:
    """Read a BCF from a CMX file."""
    return bcf.Bcf(
        read_skeletons(file),
        read_suits(file),
        read_skills(file),
    )


def write_cmx(file: typing.TextIO, bcf_desc: bcf.Bcf) -> None:
    """Write a BCF to a CMX file."""
    file.write("// Exported with TS1 Blender IO\n")
    file.write("version 300\n")
    write_skeletons(file, bcf_desc.skeletons)
    write_suits(file, bcf_desc.suits)
    write_skills(file, bcf_desc.skills)


def read_file(file_path: pathlib.Path) -> bcf.Bcf:
    """Read a BCF from a CMX file path."""
    try:
        with file_path.open() as file:
            if not file.readline().startswith("//"):
                raise utils.FileReadError

            if file.readline().strip() != "version 300":
                raise utils.FileReadError

            return read_cmx(file)

    except OSError as exception:
        raise utils.FileReadError from exception


def write_file(file_path: pathlib.Path, bcf_desc: bcf.Bcf) -> None:
    """Write a BCF to a CMX file path."""
    with file_path.open('w') as file:
        write_cmx(file, bcf_desc)
