"""Export Blender animation to The Sims animation."""

import itertools

import bpy
import mathutils
from bpy_extras import anim_utils

from . import utils
from .ts1_formats import bcf, cfp, property_list


def export_animation(
    armature_object: bpy.types.Object, strip: bpy.types.NlaStrip, name: str
) -> tuple[bcf.Skill, cfp.Cfp]:
    """Export the animation in the strip to a Skill and cfp."""
    cfp_values = cfp.Cfp([], [], [], [], [], [], [])

    distance = strip.action.get("Distance", 0.0)

    skill = bcf.Skill(
        strip.action.name,
        name,
        round((strip.action.frame_end) * 33.3333333),
        distance,
        distance != 0.0,
        0,
        0,
        [],
    )

    for bone in armature_object.pose.bones:
        motion = bcf.Motion(
            bone.name,
            int(strip.action.frame_end - strip.action.frame_start) + 1,
            skill.duration,
            0,
            0,
            0,
            0,
            [],
            [],
        )

        location_data_path = bone.path_from_id("location")
        rotation_data_path = bone.path_from_id("rotation_quaternion")

        if bpy.app.version[0] >= 5:
            fcurves = anim_utils.action_get_channelbag_for_slot(strip.action, strip.action_slot).fcurves
        else:
            fcurves = strip.action.fcurves

        if fcurves.find(location_data_path):
            motion.positions_used_flag = 1
        if fcurves.find(rotation_data_path):
            motion.rotations_used_flag = 1

        if not motion.positions_used_flag and not motion.rotations_used_flag:
            continue

        locations = []
        rotations = []

        for frame in range(int(strip.action.frame_start), int(strip.action.frame_end) + 1):
            if motion.positions_used_flag:
                locations.append(
                    mathutils.Vector(
                        (
                            fcurves.find(location_data_path, index=0).evaluate(frame),
                            fcurves.find(location_data_path, index=1).evaluate(frame),
                            fcurves.find(location_data_path, index=2).evaluate(frame),
                        ),
                    )
                )

            if motion.rotations_used_flag:
                rotations.append(
                    mathutils.Quaternion(
                        (
                            fcurves.find(rotation_data_path, index=0).evaluate(frame),
                            fcurves.find(rotation_data_path, index=1).evaluate(frame),
                            fcurves.find(rotation_data_path, index=2).evaluate(frame),
                            fcurves.find(rotation_data_path, index=3).evaluate(frame),
                        ),
                    )
                )

        if all(location == mathutils.Vector() for location in locations):
            motion.positions_used_flag = False

        if all(rotation == mathutils.Quaternion() for rotation in rotations):
            motion.rotations_used_flag = False

        if not motion.positions_used_flag and not motion.rotations_used_flag:
            continue

        parent_bone_matrix = mathutils.Matrix()
        if bone.parent:
            parent_bone_matrix = bone.parent.bone.matrix_local @ utils.BONE_ROTATION_OFFSET_INVERTED

        for translation, rotation in itertools.zip_longest(locations, rotations):
            translation_matrix = mathutils.Matrix()
            if translation:
                translation_matrix = mathutils.Matrix.Translation(translation)

            rotation_matrix = mathutils.Matrix()
            if rotation:
                rotation_matrix = rotation.to_matrix().to_4x4()

            bone_matrix = bone.bone.convert_local_to_pose(
                translation_matrix @ rotation_matrix,
                bone.bone.matrix_local,
            )
            bone_matrix = parent_bone_matrix.inverted() @ bone_matrix
            bone_matrix @= utils.BONE_ROTATION_OFFSET_INVERTED

            if motion.positions_used_flag:
                final_translation = bone_matrix.to_translation() * utils.BONE_SCALE
                cfp_values.positions_x.append(final_translation.x)
                cfp_values.positions_y.append(final_translation.z)  # swap y and z
                cfp_values.positions_z.append(final_translation.y)
            if motion.rotations_used_flag:
                final_rotation = bone_matrix.to_quaternion()
                cfp_values.rotations_x.append(final_rotation.x)
                cfp_values.rotations_y.append(final_rotation.z)  # swap y and z
                cfp_values.rotations_z.append(final_rotation.y)
                cfp_values.rotations_w.append(final_rotation.w)

        # there's never more than one time property list in official animations
        time_property_list = bcf.TimePropertyList([])

        for frame in range(int(strip.action.frame_start), int(strip.action.frame_end) + 1):
            markers = [x for x in strip.action.pose_markers if x.frame == frame]
            if len(markers) == 0:
                continue

            time = round((frame - int(strip.action.frame_start)) * 33.33333)
            events = []

            for marker in markers:
                event_strings = marker.name.split(";")
                for event_string in event_strings:
                    event_components = event_string.split()
                    if event_components[0] != bone.name:
                        continue
                    events.append(
                        property_list.Property(
                            event_components[1],
                            event_components[2],
                        ),
                    )

            if len(events) == 0:
                continue

            time_property = property_list.TimeProperty(
                time,
                events,
            )
            time_property_list.time_properties.append(time_property)

        if len(time_property_list.time_properties) > 0:
            motion.time_property_lists.append(time_property_list)

        motion.position_offset = -1
        motion.rotation_offset = -1

        skill.motions.append(motion)

    position_offset = 0
    rotation_offset = 0
    for motion in skill.motions:
        if motion.positions_used_flag:
            motion.position_offset = position_offset
            position_offset += motion.frame_count
        if motion.rotations_used_flag:
            motion.rotation_offset = rotation_offset
            rotation_offset += motion.frame_count

    skill.position_count = len(cfp_values.positions_x)
    skill.rotation_count = len(cfp_values.rotations_x)

    return (skill, cfp_values)
