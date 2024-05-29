from . import bcf


def read_properties(file):
    count = int(file.readline())
    properties = []
    for i in range(count):
        properties.append(
            bcf.Property(
                file.readline().strip(),
                file.readline().strip(),
            )
        )
    return properties


def write_properties(file, properties):
    file.write(str(len(properties)) + "\n")
    for prop in properties:
        file.write(prop.name + "\n")
        file.write(prop.value + "\n")


def read_property_lists(file):
    count = int(file.readline())
    property_lists = []
    for i in range(count):
        property_lists.append(
            bcf.PropertyList(
                read_properties(file),
            )
        )
    return property_lists


def write_property_lists(file, property_lists):
    file.write(str(len(property_lists)) + "\n")
    for property_list in property_lists:
        write_properties(file, property_list.properties)


def read_time_properties(file):
    count = int(file.readline())
    time_properties = []
    for i in range(count):
        time_properties.append(
            bcf.TimeProperty(
                int(file.readline()),
                read_properties(file),
            )
        )
    return time_properties


def write_time_properties(file, time_properties):
    file.write(str(len(time_properties)) + "\n")
    for time_property in time_properties:
        file.write(str(time_property.time) + "\n")
        write_properties(file, time_property.events)


def read_time_property_lists(file):
    count = int(file.readline())
    time_property_lists = []
    for i in range(count):
        time_property_lists.append(
            bcf.TimePropertyList(
                read_time_properties(file),
            )
        )
    return time_property_lists


def write_time_property_lists(file, time_property_lists):
    file.write(str(len(time_property_lists)) + "\n")
    for time_property_list in time_property_lists:
        write_time_properties(file, time_property_list.time_properties)


def read_motions(file):
    count = int(file.readline())
    motions = []
    for i in range(count):
        motions.append(
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
        )
    return motions


def write_motions(file, motions):
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


def read_skills(file):
    count = int(file.readline())
    skills = []
    for i in range(count):
        skills.append(
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
        )
    return skills


def write_skills(file, skills):
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


def read_skins(file):
    count = int(file.readline())
    skins = []
    for i in range(count):
        skins.append(
            bcf.Skin(
                file.readline().strip(),
                file.readline().strip(),
                int(file.readline()),
                int(file.readline()),
            )
        )
    return skins


def write_skins(file, skins):
    file.write(str(len(skins)) + "\n")
    for skin in skins:
        file.write(skin.bone_name + "\n")
        file.write(skin.skin_name + "\n")
        file.write(str(skin.censor_flags) + "\n")
        file.write(str(skin.unknown) + "\n")


def read_suits(file):
    count = int(file.readline())
    suits = []
    for i in range(count):
        suits.append(
            bcf.Suit(
                file.readline().strip(),
                int(file.readline()),
                int(file.readline()),
                read_skins(file),
            )
        )
    return suits


def write_suits(file, suits):
    file.write(str(len(suits)) + "\n")
    for suit in suits:
        file.write(suit.name + "\n")
        file.write(str(suit.suit_type) + "\n")
        file.write(str(suit.unknown) + "\n")
        write_skins(file, suit.skins)


def read_bones(file):
    count = int(file.readline())
    bones = []
    for i in range(count):
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
            )
        )
    return bones


def write_bones(file, bones):
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


def read_skeletons(file):
    count = int(file.readline())
    skeletons = []
    for i in range(count):
        skeletons.append(
            bcf.Skeleton(
                file.readline().strip(),
                read_bones(file),
            )
        )
    return skeletons


def write_skeletons(file, skeletons):
    file.write(str(len(skeletons)) + "\n")
    for skeleton in skeletons:
        file.write(skeleton.name + "\n")
        write_bones(file, skeleton.bones)


def read_cmx(file):
    return bcf.Bcf(
        read_skeletons(file),
        read_suits(file),
        read_skills(file),
    )


def write_cmx(file, cmx):
    file.write("// Exported with TS1 Blender IO\n")
    file.write("version 300\n")
    write_skeletons(file, cmx.skeletons)
    write_suits(file, cmx.suits)
    write_skills(file, cmx.skills)


def read_file(file_path):
    with file_path.open() as file:
        if not file.readline().strip().startswith("//"):
            raise Exception("Could not read cmx file " + file_path)
        if file.readline().strip() != "version 300":
            raise Exception("Could not read cmx file " + file_path)

        cmx = read_cmx(file)

        if file.readline() != "":
            raise Exception("data left unread at end of " + file_path)

        return cmx


def write_file(file_path, cmx):
    with file_path.open('w') as file:
        write_cmx(file, cmx)
