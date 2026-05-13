"""Import The Sims animations in to Blender."""

import logging

import bpy
import bpy_extras.anim_utils
import mathutils

from . import utils
from .ts1_formats import bcf, cfp


def create_fcurve_data(
    action: bpy.types.Action,
    channelbag,  #  noqa: ANN001
    data_path: str,
    index: int,
    count: int,
    data: list[float],
) -> None:
    """Create the fcurve data for all frames at once."""
    if bpy.app.version[0] >= 5:
        f_curve = channelbag.fcurves.new(data_path, index=index)
    else:
        f_curve = action.fcurves.new(data_path, index=index)
    f_curve.keyframe_points.add(count=count)
    f_curve.keyframe_points.foreach_set("co", data)
    f_curve.update()


MAX_TIMELINE_MARKER_NAME_LENGTH = 63  # 64 - null


def import_animation(
    context: bpy.types.Context,
    logger: logging.Logger,
    armature: bpy.types.Object,
    animation: bcf.Skill,
    cfp_data: cfp.Cfp,
) -> None:
    """Create a mesh object for the mesh."""
    if animation.skill_name in bpy.data.actions:
        return

    anim_data = armature.animation_data_create()

    action = bpy.data.actions.new(name=animation.skill_name)
    anim_data.action = action
    channelbag = None
    if bpy.app.version[0] >= 5:
        anim_data.action_slot = action.slots.new(id_type='OBJECT', name="slot")
        channelbag = bpy_extras.anim_utils.action_ensure_channelbag_for_slot(anim_data.action, anim_data.action_slot)

    action.frame_range = (1.0, animation.motions[0].frame_count)

    action["Distance"] = animation.distance

    ignored_bone_count = 0

    for motion in animation.motions:
        bone = armature.pose.bones.get(motion.bone_name)
        if bone is None:
            ignored_bone_count += 1
            continue

        parent_bone_matrix = mathutils.Matrix()
        if bone.parent:
            parent_bone_matrix = bone.parent.bone.matrix_local @ utils.BONE_ROTATION_OFFSET_INVERTED

        positions_x: list[float] = []
        positions_y: list[float] = []
        positions_z: list[float] = []
        rotations_w: list[float] = []
        rotations_x: list[float] = []
        rotations_y: list[float] = []
        rotations_z: list[float] = []

        for frame in range(motion.frame_count):
            translation = mathutils.Matrix()
            if motion.positions_used_flag:
                translation = mathutils.Matrix.Translation(
                    mathutils.Vector(
                        (
                            cfp_data.positions_x[motion.position_offset + frame] / utils.BONE_SCALE,
                            cfp_data.positions_z[motion.position_offset + frame] / utils.BONE_SCALE,  # swap y and z
                            cfp_data.positions_y[motion.position_offset + frame] / utils.BONE_SCALE,
                        ),
                    ),
                )

            rotation = mathutils.Matrix()
            if motion.rotations_used_flag:
                rotation = (
                    mathutils.Quaternion(
                        (
                            cfp_data.rotations_w[motion.rotation_offset + frame],
                            cfp_data.rotations_x[motion.rotation_offset + frame],
                            cfp_data.rotations_z[motion.rotation_offset + frame],  # swap y and z
                            cfp_data.rotations_y[motion.rotation_offset + frame],
                        ),
                    )
                    .to_matrix()
                    .to_4x4()
                )

            bone_matrix = parent_bone_matrix @ (translation @ rotation)
            bone_matrix = bone.bone.convert_local_to_pose(
                bone_matrix,
                bone.bone.matrix_local,
                invert=True,
            )
            bone_matrix @= utils.BONE_ROTATION_OFFSET

            if motion.positions_used_flag:
                translation = bone_matrix.to_translation()
                positions_x += (float(frame + 1), translation.x)
                positions_y += (float(frame + 1), translation.y)
                positions_z += (float(frame + 1), translation.z)

            if motion.rotations_used_flag:
                rotation = bone_matrix.to_quaternion()
                rotations_w += (float(frame + 1), rotation.w)
                rotations_x += (float(frame + 1), rotation.x)
                rotations_y += (float(frame + 1), rotation.y)
                rotations_z += (float(frame + 1), rotation.z)

        if motion.positions_used_flag:
            data_path = bone.path_from_id("location")
            create_fcurve_data(action, channelbag, data_path, 0, motion.frame_count, positions_x)
            create_fcurve_data(action, channelbag, data_path, 1, motion.frame_count, positions_y)
            create_fcurve_data(action, channelbag, data_path, 2, motion.frame_count, positions_z)

        if motion.rotations_used_flag:
            data_path = bone.path_from_id("rotation_quaternion")
            create_fcurve_data(action, channelbag, data_path, 0, motion.frame_count, rotations_w)
            create_fcurve_data(action, channelbag, data_path, 1, motion.frame_count, rotations_x)
            create_fcurve_data(action, channelbag, data_path, 2, motion.frame_count, rotations_y)
            create_fcurve_data(action, channelbag, data_path, 3, motion.frame_count, rotations_z)

    # create a single default keyframe for any locations or rotations not used by the animation
    for bone in armature.pose.bones:
        location_data_path = bone.path_from_id("location")
        rotation_data_path = bone.path_from_id("rotation_quaternion")

        if channelbag:
            location_fcurve = channelbag.fcurves.find(location_data_path)
            rotation_fcurve = channelbag.fcurves.find(rotation_data_path)
        else:
            location_fcurve = action.fcurves.find(location_data_path)
            rotation_fcurve = action.fcurves.find(rotation_data_path)

        if not location_fcurve:
            create_fcurve_data(action, channelbag, location_data_path, 0, 1, [1.0, 0.0])
            create_fcurve_data(action, channelbag, location_data_path, 1, 1, [1.0, 0.0])
            create_fcurve_data(action, channelbag, location_data_path, 2, 1, [1.0, 0.0])
        if not rotation_fcurve:
            create_fcurve_data(action, channelbag, rotation_data_path, 0, 1, [1.0, 1.0])
            create_fcurve_data(action, channelbag, rotation_data_path, 1, 1, [1.0, 0.0])
            create_fcurve_data(action, channelbag, rotation_data_path, 2, 1, [1.0, 0.0])
            create_fcurve_data(action, channelbag, rotation_data_path, 3, 1, [1.0, 0.0])

    if ignored_bone_count > 0:
        logger.info(f"Skipped {ignored_bone_count} unknown bones in {animation.skill_name}.")  # noqa: G004

    for motion in animation.motions:
        for time_property_list in motion.time_property_lists:
            for time_property in time_property_list.time_properties:
                for event in time_property.events:
                    event_string = f"{motion.bone_name} {event.name} {event.value}"
                    frame = round(time_property.time / 33.3333333) + 1

                    markers = [x for x in action.pose_markers if x.frame == frame]

                    if len(markers) == 0:
                        marker = action.pose_markers.new(name=event_string)
                        marker.frame = frame
                    else:
                        last_marker = action.pose_markers[-1]
                        if len(last_marker.name) + 1 + len(event_string) <= MAX_TIMELINE_MARKER_NAME_LENGTH:
                            last_marker.name = f"{last_marker.name};{event_string}"
                        else:
                            marker = action.pose_markers.new(name=event_string)
                            marker.frame = frame

    track = anim_data.nla_tracks.new(prev=None)
    track.name = animation.animation_name
    track.strips.new(animation.skill_name, 1, action)
    track.mute = True

    context.scene.render.fps = 33
    context.scene.frame_end = max(context.scene.frame_end, animation.motions[0].frame_count)
