"""Export to The Sims 1 files."""

import pathlib
from typing import TYPE_CHECKING

import bpy

from . import export_animation, export_mesh
from .ts1_formats import bcf, bmf, cfp, cmx, skn
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
            skill, cfp_values = export_animation.export_animation(armature_object, strip, nla_track.name)

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
