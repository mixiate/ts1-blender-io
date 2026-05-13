"""Export to The Sims 1 files."""

import itertools
import pathlib
from typing import TYPE_CHECKING

import bpy
import mathutils
from bpy_extras import anim_utils

from . import export_mesh, utils
from .ts1_formats import bcf, bmf, cfp, cmx, property_list, skn
from .utils import ExportError

if TYPE_CHECKING:
    from .ts1_formats.skeleton import Skeleton


def export_skin(directory: pathlib.Path, mesh_format: str, obj: bpy.types.Object, *, apply_modifiers: bool) -> None:
    """Export the object's mesh to a BMF or SKN file."""
    default_texture = "x"
    if len(obj.data.materials) > 0:
        default_texture = obj.data.materials[0].name

    bmf_mesh = export_mesh.export_mesh(obj, apply_modifiers=apply_modifiers)

    bmf_file = bmf.Bmf(
        obj.name,
        default_texture,
        bmf_mesh,
    )

    match mesh_format:
        case 'bmf':
            bmf.write_file(directory / (obj.name + ".bmf"), bmf_file)
        case 'skn':
            skn.write_file(directory / (obj.name + ".skn"), bmf_file)
        case _:
            error_message = f"Unknown mesh format {mesh_format}"
            raise ExportError(error_message)


def export_suit(
    directory: pathlib.Path,
    mesh_format: str,
    suit_name: str,
    suit_type: int,
    objects: list[bpy.types.Object],
    *,
    apply_modifiers: bool,
) -> bcf.Suit:
    """Create a BCF suit from the list of objects, and export the meshes of the objects."""
    skins = []
    for obj in objects:
        bone_name = obj.get("Bone Name")
        if bone_name is None:
            error_message = f"{obj.name} object does not have a Bone Name custom property"
            raise ExportError(error_message)

        if not obj.parent or obj.parent.type != 'ARMATURE':
            error_message = f"{obj.name} object is not parented to an armature"
            raise ExportError(error_message)

        if bone_name not in obj.parent.data.bones:
            error_message = f"{obj.name} bone name {bone_name} is not a bone in the parent armature"
            raise ExportError(error_message)

        expected_object_name_prefix = f"xskin-{suit_name}-{bone_name}-"
        if not obj.name.lower().startswith(expected_object_name_prefix.lower()):
            error_message = (
                f"{obj.name} object name is invalid. It's name should start with {expected_object_name_prefix}"
            )
            raise ExportError(error_message)

        skins.append(
            bcf.Skin(
                bone_name,
                obj.name,
                obj.get("Censor Flags", 0),
                0,
            ),
        )

        export_skin(directory, mesh_format, obj, apply_modifiers=apply_modifiers)

    return bcf.Suit(
        suit_name,
        suit_type,
        0,
        skins,
    )


def export_skills(
    armature_object: bpy.types.Object,
    output_directory: pathlib.Path,
    *,
    compress_cfp: bool,
) -> list[bcf.Skill]:
    """Export all the animations in the given armature to CFP files and return the corresponding BCF skills."""
    skills: list[bcf.Skill] = []

    if armature_object.animation_data is None:
        return []

    for nla_track in armature_object.animation_data.nla_tracks:
        for strip in nla_track.strips:
            cfp_values = cfp.Cfp([], [], [], [], [], [], [])

            distance = strip.action.get("Distance", 0.0)

            skill = bcf.Skill(
                strip.action.name,
                nla_track.name,
                round((strip.action.frame_end) * 33.3333333),
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

            skills.append(skill)

            cfp_file_path = output_directory / (nla_track.name + ".cfp")
            cfp.write_file(
                cfp_file_path,
                cfp_values,
                compress=compress_cfp,
            )

    return skills


def export_files(
    context: bpy.types.Context,
    file_path: pathlib.Path,
    mesh_format: str,
    *,
    export_meshes: bool,
    export_animations: bool,
    compress_cfp: bool,
    apply_modifiers: bool,
) -> None:
    """Export all the meshes and animations in the scene to the selected file."""
    if context.active_object is not None and context.active_object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode='OBJECT')

    skeletons: list[Skeleton] = []
    suits: list[bcf.Suit] = []
    skills: list[bcf.Skill] = []

    if export_meshes:
        for collection in context.scene.collection.children:
            objects = [obj for obj in collection.objects if obj.type == 'MESH']
            if len(objects) == 0:
                continue

            suits.append(
                export_suit(
                    file_path.parent,
                    mesh_format,
                    collection.name,
                    collection.get("Suit Type", 0),
                    objects,
                    apply_modifiers=apply_modifiers,
                ),
            )

    if export_animations:
        for armature_object in [obj for obj in context.scene.objects if obj.type == 'ARMATURE']:
            skills.extend(export_skills(armature_object, file_path.parent, compress_cfp=compress_cfp))

    bcf_desc = bcf.Bcf(skeletons, suits, skills)

    match file_path.suffix:
        case ".cmx":
            cmx.write_file(file_path, bcf_desc)
        case ".bcf":
            bcf.write_file(file_path, bcf_desc)
