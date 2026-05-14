"""Export The Sims Online files."""

import pathlib

import bpy

from . import export_animation, export_mesh
from .ts1_formats import anim, bcf, mesh, property_list


def bcf_motion_to_anim_motion(motion: bcf.Motion) -> anim.Motion:
    """Convert a bcf format motion to an anim format motion."""
    time_properties = []
    for time_property_list in motion.time_property_lists:
        for time_property in time_property_list.time_properties:
            prop_list = property_list.PropertyList(time_property.events)
            time_properties.append(anim.TimeProperty(time_property.time, [prop_list]))

    return anim.Motion(
        motion.bone_name,
        motion.frame_count,
        motion.duration,
        bool(motion.positions_used_flag),
        bool(motion.rotations_used_flag),
        motion.position_offset,
        motion.rotation_offset,
        motion.property_lists,
        [anim.TimePropertyList(time_properties)],
    )


def export_files(
    context: bpy.types.Context,
    output_directory: pathlib.Path,
    *,
    export_meshes: bool,
    export_animations: bool,
    apply_modifiers: bool,
) -> None:
    """Export all the meshes and animations in the scene."""
    if export_meshes:
        for mesh_object in [obj for obj in context.scene.objects if obj.type == 'MESH']:
            sims_mesh = export_mesh.export_mesh(mesh_object, apply_modifiers=apply_modifiers)
            mesh.write_file(output_directory / (mesh_object.name + ".mesh"), sims_mesh)

    if export_animations:
        for armature_object in [obj for obj in context.scene.objects if obj.type == 'ARMATURE' and obj.animation_data]:
            for nla_track in armature_object.animation_data.nla_tracks:
                for strip in nla_track.strips:
                    skill, cfp = export_animation.export_animation(armature_object, strip, nla_track.name)

                    trans_iter = zip(cfp.positions_x, cfp.positions_y, cfp.positions_z, strict=True)
                    translations = [(x, y, z) for x, y, z in trans_iter]
                    rot_iter = zip(cfp.rotations_x, cfp.rotations_y, cfp.rotations_z, cfp.rotations_w, strict=True)
                    rotations = [(x, y, z, w) for x, y, z, w in rot_iter]

                    animation = anim.Anim(
                        skill.animation_name,
                        skill.duration,
                        skill.distance,
                        skill.moves,
                        translations,
                        rotations,
                        [bcf_motion_to_anim_motion(x) for x in skill.motions],
                    )

                    anim.write_file(output_directory / (animation.name + ".anim"), animation)
