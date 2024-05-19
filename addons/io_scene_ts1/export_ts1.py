import bpy
import copy
import math
import mathutils
import os

from . import bcf
from . import cfp
from . import utils

def export_files(context, file_path, compress_cfp):
    animation_file = {}

    animation_file["skeletons"] = list()
    animation_file["suits"] = list()
    animation_file["skills"] = list()

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

                skill = {}
                skill["skill_name"] = strip.action.name
                skill["animation_name"] = track.name
                skill["duration"] = math.floor((strip.action.frame_end - 1) * 33.3333333)
                skill["distance"] = strip.action["distance"]
                skill["moving_flag"] = 1 if strip.action["distance"] != 0.0 else 0
                skill["motions"] = list()

                for bone in armature_object.pose.bones:
                    motion = {}
                    motion["bone_name"] = bone.name
                    motion["frame_count"] = int(strip.action.frame_end - strip.action.frame_start) + 1
                    motion["duration"] = skill["duration"]
                    motion["positions_used_flag"] = 0
                    motion["rotations_used_flag"] = 0
                    motion["property_count"] = 0
                    motion["properties"] = list()
                    motion["time_properties"] = list()

                    for frame in range(int(strip.action.frame_start), int(strip.action.frame_end) + 1):
                        for fcu in strip.action.fcurves:
                            if fcu.data_path == bone.path_from_id("location"):
                                if frame in (p.co.x for p in fcu.keyframe_points):
                                    motion["positions_used_flag"] = 1
                            if fcu.data_path == bone.path_from_id("rotation_quaternion"):
                                if frame in (p.co.x for p in fcu.keyframe_points):
                                    motion["rotations_used_flag"] = 1

                    if not motion["positions_used_flag"] and not motion["rotations_used_flag"]:
                        continue

                    original_current_frame = bpy.context.scene.frame_current

                    for frame in range(int(strip.action.frame_start), int(strip.action.frame_end) + 1):
                        bpy.context.scene.frame_set(frame)

                        if motion["positions_used_flag"]:
                            position = copy.copy(bone.head)
                            if bone.parent is not None:
                                position = bone.parent.matrix.inverted() @ bone.head
                                position = utils.BONE_ROTATION_OFFSET @ position
                            position *= utils.BONE_SCALE
                            positions_x.append(position.x)
                            positions_y.append(position.z) # swap y and z
                            positions_z.append(position.y)
                        if motion["rotations_used_flag"]:
                            rotation = bone.matrix @ utils.BONE_ROTATION_OFFSET.inverted()
                            if bone.parent is not None:
                                rotation = (bone.parent.matrix @ utils.BONE_ROTATION_OFFSET.inverted()).inverted() @ rotation
                            rotation = rotation.to_quaternion()
                            rotations_x.append(rotation.x)
                            rotations_y.append(rotation.z) # swap y and z
                            rotations_z.append(rotation.y)
                            rotations_w.append(rotation.w)

                    bpy.context.scene.frame_set(original_current_frame)

                    time_properties = {}
                    time_properties["properties"] = list()

                    for marker in strip.action.pose_markers:
                        marker_components = marker.name.split()
                        if marker_components[0] == bone.name:
                            event = {}
                            event["name"] = marker_components[1]
                            event["value"] = marker_components[2]

                            time_property = {}
                            time_property["time"] = int(round((marker.frame - int(strip.action.frame_start)) * 33.33333))
                            time_property["event_count"] = 1
                            time_property["events"] = [event]

                            time_properties["properties"].append(time_property)

                    if len(time_properties["properties"]) > 0:
                        time_properties["count"] = len(time_properties["properties"])
                        motion["time_properties"].append(time_properties)

                    motion["time_property_count"] = len(motion["time_properties"])

                    motion["position_offset"] = 4294967295
                    motion["rotation_offset"] = 4294967295

                    skill["motions"].append(motion)

                position_offset = 0
                rotation_offset = 0
                for motion in skill["motions"]:
                    if motion["positions_used_flag"]:
                        motion["position_offset"] = position_offset
                        position_offset += motion["frame_count"]
                    if motion["rotations_used_flag"]:
                        motion["rotation_offset"] = rotation_offset
                        rotation_offset += motion["frame_count"]

                skill["position_count"] = len(positions_x)
                skill["rotation_count"] = len(rotations_x)

                skill["motion_count"] = len(skill["motions"])
                animation_file["skills"].append(skill)

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

    animation_file["skeleton_count"] = len(animation_file["skeletons"])
    animation_file["suit_count"] = len(animation_file["suits"])
    animation_file["skill_count"] = len(animation_file["skills"])

    file = open(file_path + ".bcf", "wb")
    file.write(bcf.bcf_struct().build(animation_file))
