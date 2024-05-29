import dataclasses
import struct


from . import utils


@dataclasses.dataclass
class Property:
    name: str
    value: str


def read_properties(file):
    count = struct.unpack('<I', file.read(4))[0]
    properties = []
    for i in range(count):
        properties.append(
            Property(
                utils.read_string(file),
                utils.read_string(file),
            )
        )
    return properties


def write_properties(file, properties):
    file.write(struct.pack('<I', len(properties)))
    for prop in properties:
        utils.write_string(file, prop.name)
        utils.write_string(file, prop.value)


@dataclasses.dataclass
class PropertyList:
    properties: list[Property]


def read_property_lists(file):
    count = struct.unpack('<I', file.read(4))[0]
    property_lists = []
    for i in range(count):
        property_lists.append(
            PropertyList(
                read_properties(file),
            )
        )
    return property_lists


def write_property_lists(file, property_lists):
    file.write(struct.pack('<I', len(property_lists)))
    for property_list in property_lists:
        write_properties(file, property_list.properties)


@dataclasses.dataclass
class TimeProperty:
    time: int
    events: list[Property]


def read_time_properties(file):
    count = struct.unpack('<I', file.read(4))[0]
    time_properties = []
    for i in range(count):
        time_properties.append(
            TimeProperty(
                struct.unpack('<I', file.read(4))[0],
                read_properties(file),
            )
        )
    return time_properties


def write_time_properties(file, time_properties):
    file.write(struct.pack('<I', len(time_properties)))
    for time_property in time_properties:
        file.write(struct.pack('<I', time_property.time))
        write_properties(file, time_property.events)


@dataclasses.dataclass
class TimePropertyList:
    time_properties: list[TimeProperty]


def read_time_property_lists(file):
    count = struct.unpack('<I', file.read(4))[0]
    time_property_lists = []
    for i in range(count):
        time_property_lists.append(
            TimePropertyList(
                read_time_properties(file),
            )
        )
    return time_property_lists


def write_time_property_lists(file, time_property_lists):
    file.write(struct.pack('<I', len(time_property_lists)))
    for time_property_list in time_property_lists:
        write_time_properties(file, time_property_list.time_properties)


@dataclasses.dataclass
class Motion:
    bone_name: str
    frame_count: int
    duration: float
    positions_used_flag: int
    rotations_used_flag: int
    position_offset: int
    rotation_offset: int
    property_lists: list[PropertyList]
    time_property_lists: list[TimePropertyList]


def read_motions(file):
    count = struct.unpack('<I', file.read(4))[0]
    motions = []
    for i in range(count):
        motions.append(
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
        )
    return motions


def write_motions(file, motions):
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
    skill_name: str
    animation_name: str
    duration: float
    distance: float
    moving_flag: int
    position_count: int
    rotation_count: int
    motions: list[Motion]


def read_skills(file):
    count = struct.unpack('<I', file.read(4))[0]
    skills = []
    for i in range(count):
        skills.append(
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
        )
    return skills


def write_skills(file, skills):
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
    bone_name: str
    skin_name: str
    censor_flags: int
    unknown: int


def read_skins(file):
    count = struct.unpack('<I', file.read(4))[0]
    skins = []
    for i in range(count):
        skins.append(
            Skin(
                utils.read_string(file),
                utils.read_string(file),
                struct.unpack('<I', file.read(4))[0],
                struct.unpack('<I', file.read(4))[0],
            )
        )
    return skins


def write_skins(file, skins):
    file.write(struct.pack('<I', len(skins)))
    for skin in skins:
        utils.write_string(file, skin.bone_name)
        utils.write_string(file, skin.skin_name)
        file.write(struct.pack('<I', skin.censor_flags))
        file.write(struct.pack('<I', skin.unknown))


@dataclasses.dataclass
class Suit:
    name: str
    suit_type: int
    unknown: int
    skins: list[Skin]


def read_suits(file):
    count = struct.unpack('<I', file.read(4))[0]
    suits = []
    for i in range(count):
        suits.append(
            Suit(
                utils.read_string(file),
                struct.unpack('<I', file.read(4))[0],
                struct.unpack('<I', file.read(4))[0],
                read_skins(file),
            )
        )
    return suits


def write_suits(file, suits):
    file.write(struct.pack('<I', len(suits)))
    for suit in suits:
        utils.write_string(file, suit.name)
        file.write(struct.pack('<I', suit.suit_type))
        file.write(struct.pack('<I', suit.unknown))
        write_skins(file, suit.skins)


@dataclasses.dataclass
class Bone:
    name: str
    parent: str
    properties: list[PropertyList]
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


def read_bones(file):
    count = struct.unpack('<I', file.read(4))[0]
    bones = []
    for i in range(count):
        bones.append(
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
        )
    return bones


def write_bones(file, bones):
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
    name: str
    bones: list[Bone]


def read_skeletons(file):
    count = struct.unpack('<I', file.read(4))[0]
    skeletons = []
    for i in range(count):
        skeletons.append(
            Skeleton(
                utils.read_string(file),
                read_bones(file),
            )
        )
    return skeletons


def write_skeletons(file, skeletons):
    file.write(struct.pack('<I', len(skeletons)))
    for skeleton in skeletons:
        utils.write_string(file, skeleton.name)
        write_bones(file, skeleton.bones)


@dataclasses.dataclass
class Bcf:
    skeletons: list[Skeleton]
    suits: list[Bone]
    skills: list[Skill]


def read_bcf(file):
    return Bcf(
        read_skeletons(file),
        read_suits(file),
        read_skills(file),
    )


def write_bcf(file, bcf):
    write_skeletons(file, bcf.skeletons)
    write_suits(file, bcf.suits)
    write_skills(file, bcf.skills)


def read_file(file_path):
    with file_path.open(mode='rb') as file:
        bcf = read_bcf(file)

        try:
            file.read(1)
            raise Exception("data left unread at end of " + file_path)
        except Exception as _:
            pass

        return bcf


def write_file(file_path, bcf):
    with file_path.open('wb') as file:
        write_bcf(file, bcf)
