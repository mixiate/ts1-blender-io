import bpy
import copy
import math
import mathutils
import os

from . import bcf
from . import cfp
from . import cmx
from . import utils

def export_files(context, file_path, compress_cfp):
    skeletons = list()
    suits = list()
    skills = list()

    for armature in bpy.data.armatures:
        armature_object = bpy.data.objects[armature.name]

        for track in armature_object.animation_data.nla_tracks:
            for strip in track.strips:
                armature_object.animation_data.action = strip.action

                positions_x = list()
                positions_y = list()
                positions_z = list()

                rotations_x = list()
                rotations_y = list()
                rotations_z = list()
                rotations_w = list()

                skill = bcf.Skill(
                    strip.action.name,
                    track.name,
                    math.floor((strip.action.frame_end) * 33.3333333),
                    strip.action["distance"],
                    1 if strip.action["distance"] != 0.0 else 0,
                    0,
                    0,
                    list(),
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
                        list(),
                        list(),
                    )

                    for frame in range(int(strip.action.frame_start), int(strip.action.frame_end) + 1):
                        for fcu in strip.action.fcurves:
                            if fcu.data_path == bone.path_from_id("location"):
                                if frame in (p.co.x for p in fcu.keyframe_points):
                                    motion.positions_used_flag = 1
                            if fcu.data_path == bone.path_from_id("rotation_quaternion"):
                                if frame in (p.co.x for p in fcu.keyframe_points):
                                    motion.rotations_used_flag = 1

                    if not motion.positions_used_flag and not motion.rotations_used_flag:
                        continue

                    original_current_frame = bpy.context.scene.frame_current

                    for frame in range(int(strip.action.frame_start), int(strip.action.frame_end) + 1):
                        bpy.context.scene.frame_set(frame)

                        if motion.positions_used_flag:
                            position = copy.copy(bone.head)
                            if bone.parent is not None:
                                position = bone.parent.matrix.inverted() @ bone.head
                                position = utils.BONE_ROTATION_OFFSET @ position
                            position *= utils.BONE_SCALE
                            positions_x.append(position.x)
                            positions_y.append(position.z) # swap y and z
                            positions_z.append(position.y)
                        if motion.rotations_used_flag:
                            rotation = bone.matrix @ utils.BONE_ROTATION_OFFSET.inverted()
                            if bone.parent is not None:
                                rotation = (bone.parent.matrix @ utils.BONE_ROTATION_OFFSET.inverted()).inverted() @ rotation
                            rotation = rotation.to_quaternion()
                            rotations_x.append(rotation.x)
                            rotations_y.append(rotation.z) # swap y and z
                            rotations_z.append(rotation.y)
                            rotations_w.append(rotation.w)

                    bpy.context.scene.frame_set(original_current_frame)

                    # there's never more than one time property list in official animations
                    time_property_list = bcf.TimePropertyList(list())

                    for frame in range(int(strip.action.frame_start), int(strip.action.frame_end) + 1):
                        markers = [x for x in strip.action.pose_markers if x.frame == frame]
                        if len(markers) == 0:
                            continue

                        time = int(round((frame - int(strip.action.frame_start)) * 33.33333))
                        events = list()

                        for marker in markers:
                            event_strings = marker.name.split(";")
                            for event_string in event_strings:
                                event_components = event_string.split()
                                if not event_components[0] == bone.name:
                                    continue
                                events.append(bcf.Property(
                                    event_components[1],
                                    event_components[2],
                                ))

                        if len(events) == 0:
                            continue

                        time_property = bcf.TimeProperty(
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

                skill.position_count = len(positions_x)
                skill.rotation_count = len(rotations_x)

                skills.append(skill)

                cfp_file_path = os.path.join(os.path.dirname(file_path), track.name + ".cfp")
                cfp.write_file(
                    cfp_file_path,
                    compress_cfp,
                    positions_x,
                    positions_y,
                    positions_z,
                    rotations_x,
                    rotations_y,
                    rotations_z,
                    rotations_w
                )

    bcf_desc = bcf.Bcf(
        skeletons,
        suits,
        skills
    )

    match os.path.splitext(file_path)[1]:
        case ".cmx":
            cmx.write_file(file_path, bcf_desc)
        case ".bcf":
            bcf.write_file(file_path, bcf_desc)
