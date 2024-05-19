def bcf_struct():
    import construct

    prop = construct.Struct(
        "name" / construct.PascalString(construct.Int8ul, "ascii"),
        "value" / construct.PascalString(construct.Int8ul, "ascii"),
    )

    properties = construct.Struct(
        "count" / construct.Int32ul,
        "properties" / construct.Array(construct.this.count, prop),
    )

    time_property_event = construct.Struct(
        "name" / construct.PascalString(construct.Int8ul, "ascii"),
        "value" / construct.PascalString(construct.Int8ul, "ascii"),
    )

    time_property = construct.Struct(
        "time" / construct.Int32ul,
        "event_count" / construct.Int32ul,
        "events" / construct.Array(construct.this.event_count, time_property_event),
    )

    time_properties = construct.Struct(
        "count" / construct.Int32ul,
        "properties" / construct.Array(construct.this.count, time_property),
    )

    motion = construct.Struct(
        "bone_name" / construct.PascalString(construct.Int8ul, "ascii"),
        "frame_count" / construct.Int32ul,
        "duration" / construct.Float32l,
        "positions_used_flag" / construct.Int32ul,
        "rotations_used_flag" / construct.Int32ul,
        "position_offset" / construct.Int32ul,
        "rotation_offset" / construct.Int32ul,
        "property_count" / construct.Int32ul,
        "properties" / construct.Array(construct.this.property_count, properties),
        "time_property_count" / construct.Int32ul,
        "time_properties" / construct.Array(construct.this.time_property_count, time_properties),
    )

    skill = construct.Struct(
        "skill_name" / construct.PascalString(construct.Int8ul, "ascii"),
        "animation_name" / construct.PascalString(construct.Int8ul, "ascii"),
        "duration" / construct.Float32l,
        "distance" / construct.Int32ul,
        "moving_flag" / construct.Int32ul,
        "position_count" / construct.Int32ul,
        "rotation_count" / construct.Int32ul,
        "motion_count" / construct.Int32ul,
        "motions" / construct.Array(construct.this.motion_count, motion),
    )

    skin = construct.Struct(
        "bone_name" / construct.PascalString(construct.Int8ul, "ascii"),
        "skin_name" / construct.PascalString(construct.Int8ul, "ascii"),
        "censor_flags" / construct.Int32ul,
        "unknown" / construct.Int32ul,
    )

    suit = construct.Struct(
        "name" / construct.PascalString(construct.Int8ul, "ascii"),
        "type" / construct.Int32ul,
        "unknown" / construct.Int32ul,
        "skin_count" / construct.Int32ul,
        "skins" / construct.Array(construct.this.skin_count, skin),
    )

    bone = construct.Struct(
        "name" / construct.PascalString(construct.Int8ul, "ascii"),
        "parent" / construct.PascalString(construct.Int8ul, "ascii"),
        "property_count" / construct.Int32ul,
        "properties" / construct.Array(construct.this.property_count, properties),
        "position_x" / construct.Float32l,
        "position_y" / construct.Float32l,
        "position_z" / construct.Float32l,
        "rotation_x" / construct.Float32l,
        "rotation_y" / construct.Float32l,
        "rotation_z" / construct.Float32l,
        "rotation_w" / construct.Float32l,
        "translate" / construct.Int32ul,
        "rotate" / construct.Int32ul,
        "blend_suits" / construct.Int32ul,
        "wiggle_value" / construct.Float32l,
        "wiggle_power" / construct.Float32l,
    )

    skeleton = construct.Struct(
        "name" / construct.PascalString(construct.Int8ul, "ascii"),
        "bone_count" / construct.Int32ul,
        "bones" / construct.Array(construct.this.bone_count, bone),
    )

    cmx_bcf_struct = construct.Struct(
        "skeleton_count" / construct.Int32ul,
        "skeletons" / construct.Array(construct.this.skeleton_count, skeleton),
        "suit_count" / construct.Int32ul,
        "suits" / construct.Array(construct.this.suit_count, suit),
        "skill_count" / construct.Int32ul,
        "skills" / construct.Array(construct.this.skill_count, skill),
    )

    return cmx_bcf_struct
