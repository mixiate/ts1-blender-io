"""Export to The Sims 1 files"""

import bpy
import copy
import math


from . import bcf
from . import bmf
from . import cfp
from . import cmx
from . import skn
from . import utils


class ExportError(Exception):
    """General purpose export error"""


def export_skin(context, directory, mesh_format, obj) -> None:
    mesh = obj.data
    uv_layer = mesh.uv_layers[0]

    new_vertices = []
    new_faces = []

    # create unique vertices and faces
    for triangle in mesh.loop_triangles:
        face = []
        for loop_index in triangle.loops:
            vertex_index = mesh.loops[loop_index].vertex_index

            if len(mesh.vertices[vertex_index].groups) == 0:
                error_message = f"{obj.name} mesh has vertices that are not in a vertex group"
                raise ExportError(error_message)

            MAX_VERTEX_GROUP_COUNT = 2

            if len(mesh.vertices[vertex_index].groups) > MAX_VERTEX_GROUP_COUNT:
                error_message = f"{obj.name} mesh has vertices in more than 2 vertex groups"
                raise ExportError(error_message)

            vertex = (
                mesh.vertices[vertex_index].co,
                mesh.loops[loop_index].normal,
                uv_layer.data[loop_index].uv,
                mesh.vertices[vertex_index].groups[0].group,
                mesh.vertices[vertex_index].groups[1] if len(mesh.vertices[vertex_index].groups) > 1 else None,
            )

            if vertex not in new_vertices:
                new_vertices.append(vertex)

            vertex_index = new_vertices.index(vertex)
            face.append(vertex_index)

        new_faces.append(face)

    bones = []
    bone_bindings = []
    blends = []
    vertices = []
    uvs = []
    faces = []

    armature = obj.parent.data

    vertex_index_map = []

    # create main vertices
    for vertex_group in obj.vertex_groups:
        vertex_group_vertices = []
        vertex_group_uvs = []

        armature_bone = armature.bones.get(vertex_group.name)
        if armature_bone is None:
            error_message = (
                f"Vertex group {vertex_group.name} in {obj.name} is not a bone in armature {obj.parent.name}"
            )
            raise ExportError(error_message)

        bone_matrix = (armature_bone.matrix_local @ utils.BONE_ROTATION_OFFSET_INVERTED).inverted()
        normal_bone_matrix = bone_matrix.to_quaternion().to_matrix().to_4x4()

        for vertex_index, vertex in enumerate(new_vertices):
            if vertex_group.index == vertex[3]:
                vertex_position = (bone_matrix @ vertex[0]) * utils.BONE_SCALE
                vertex_normal = normal_bone_matrix @ vertex[1]
                vertex_group_vertices.append(bmf.Vertex(vertex_position.xzy, vertex_normal.xzy))

                vertex_uvs = (vertex[2][0], -vertex[2][1])
                vertex_group_uvs.append(vertex_uvs)

                vertex_index_map.append(vertex_index)

        bone_bindings.append(
            bmf.BoneBinding(
                len(bones),
                len(vertices),
                len(vertex_group_vertices),
                -1,
                0,
            )
        )
        bones.append(vertex_group.name)

        vertices += vertex_group_vertices
        uvs += vertex_group_uvs

    # create blended vertices
    blended_vertices = []
    for vertex_group_index, vertex_group in enumerate(obj.vertex_groups):
        vertex_group_vertices = []

        armature_bone = armature.bones[vertex_group.name]
        bone_matrix = (armature_bone.matrix_local @ utils.BONE_ROTATION_OFFSET_INVERTED).inverted()
        normal_bone_matrix = bone_matrix.to_quaternion().to_matrix().to_4x4()

        for vertex_index, vertex in enumerate(new_vertices):
            if vertex[4] is not None and vertex[4].group == vertex_group_index:
                vertex_position = (bone_matrix @ vertex[0]) * utils.BONE_SCALE
                vertex_normal = normal_bone_matrix @ vertex[1]
                vertex_group_vertices.append(bmf.Vertex(vertex_position.xzy, vertex_normal.xzy))

                weight = int(vertex[4].weight * math.pow(2, 15))
                blends.append(bmf.Blend(weight, vertex_index_map.index(vertex_index)))

        if len(vertex_group_vertices) > 0:
            bone_bindings[vertex_group_index].blended_vertex_index = len(blended_vertices)
            bone_bindings[vertex_group_index].blended_vertex_count = len(vertex_group_vertices)

            blended_vertices += vertex_group_vertices

    vertices += blended_vertices

    for face in new_faces:
        faces.append(
            (
                vertex_index_map.index(face[2]),
                vertex_index_map.index(face[1]),
                vertex_index_map.index(face[0]),
            )
        )

    default_texture = "x"
    if len(obj.data.materials) > 0:
        default_texture = obj.data.materials[0].name

    bmf_file = bmf.Bmf(
        obj.name,
        default_texture,
        bones,
        faces,
        bone_bindings,
        uvs,
        blends,
        vertices,
    )

    match mesh_format:
        case 'bmf':
            bmf.write_file(directory / (obj.name + ".bmf"), bmf_file)
        case 'skn':
            skn.write_file(directory / (obj.name + ".skn"), bmf_file)
        case _:
            error_message = f"Unknown mesh format {mesh_format}"
            raise ExportError(error_message)


def export_suit(context, directory, mesh_format, suit_name, suit_type, objects):
    skins = []
    for obj in objects:
        bone_name = obj.get("Bone Name")
        if bone_name is None:
            error_message = f"{obj.name} object does not have a Bone Name custom property"
            raise ExportError(error_message)

        expected_object_name_prefix = f"xskin-{suit_name}-{bone_name}-"
        if not obj.name.startswith(expected_object_name_prefix):
            error_message = (
                f"{obj.name} object name is invalid. It's name should start with {expected_object_name_prefix}"
            )
            raise ExportError(error_message)

        if not obj.parent or obj.parent.type != 'ARMATURE':
            error_message = f"{obj.name} object is not parented to an armature"
            raise ExportError(error_message)

        skins.append(
            bcf.Skin(
                bone_name,
                obj.name,
                obj.get("Censor Flags", 0),
                0,
            )
        )

        export_skin(context, directory, mesh_format, obj)

    return bcf.Suit(
        suit_name,
        suit_type,
        0,
        skins,
    )


def export_files(context, file_path, mesh_format, compress_cfp):
    skeletons = []
    suits = []
    skills = []

    for collection in context.scene.collection.children:
        objects = [obj for obj in collection.objects if obj.type == 'MESH']
        if len(objects) == 0:
            continue

        suits.append(
            export_suit(
                context,
                file_path.parent,
                mesh_format,
                collection.name,
                collection.get("Suit Type", 0),
                objects,
            )
        )

    for armature in bpy.data.armatures:
        armature_object = bpy.data.objects[armature.name]

        if armature_object.animation_data is None:
            continue

        for track in armature_object.animation_data.nla_tracks:
            for strip in track.strips:
                armature_object.animation_data.action = strip.action

                cfp_values = cfp.Cfp([], [], [], [], [], [], [])

                distance = strip.action.get("Distance", 0.0)

                skill = bcf.Skill(
                    strip.action.name,
                    track.name,
                    math.floor((strip.action.frame_end) * 33.3333333),
                    distance,
                    1 if distance != 0.0 else 0,
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
                            cfp_values.positions_x.append(position.x)
                            cfp_values.positions_y.append(position.z)  # swap y and z
                            cfp_values.positions_z.append(position.y)
                        if motion.rotations_used_flag:
                            rotation = bone.matrix @ utils.BONE_ROTATION_OFFSET_INVERTED
                            if bone.parent is not None:
                                rotation = (
                                    bone.parent.matrix @ utils.BONE_ROTATION_OFFSET_INVERTED
                                ).inverted() @ rotation
                            rotation = rotation.to_quaternion()
                            cfp_values.rotations_x.append(rotation.x)
                            cfp_values.rotations_y.append(rotation.z)  # swap y and z
                            cfp_values.rotations_z.append(rotation.y)
                            cfp_values.rotations_w.append(rotation.w)

                    bpy.context.scene.frame_set(original_current_frame)

                    # there's never more than one time property list in official animations
                    time_property_list = bcf.TimePropertyList([])

                    for frame in range(int(strip.action.frame_start), int(strip.action.frame_end) + 1):
                        markers = [x for x in strip.action.pose_markers if x.frame == frame]
                        if len(markers) == 0:
                            continue

                        time = int(round((frame - int(strip.action.frame_start)) * 33.33333))
                        events = []

                        for marker in markers:
                            event_strings = marker.name.split(";")
                            for event_string in event_strings:
                                event_components = event_string.split()
                                if not event_components[0] == bone.name:
                                    continue
                                events.append(
                                    bcf.Property(
                                        event_components[1],
                                        event_components[2],
                                    )
                                )

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

                cfp_file_path = file_path.parent / (track.name + ".cfp")
                cfp.write_file(
                    cfp_file_path,
                    cfp_values,
                    compress=compress_cfp,
                )

    bcf_desc = bcf.Bcf(skeletons, suits, skills)

    match file_path.suffix:
        case ".cmx":
            cmx.write_file(file_path, bcf_desc)
        case ".bcf":
            bcf.write_file(file_path, bcf_desc)
