"""Import The Sims Online files."""

import logging
import pathlib

import bpy

from . import import_animation, import_mesh, import_skeleton
from .ts1_formats import anim, bcf, mesh, property_list, skel
from .ts1_formats.error import FileReadError


def anim_motion_to_bcf_motion(motion: anim.Motion) -> bcf.Motion:
    """Convert an anim format motion to a bcf format motion."""
    time_properties = []
    for time_property_list in motion.time_property_lists:
        for time_property in time_property_list.time_properties:
            for prop_list in time_property.property_lists:
                time_properties.append(property_list.TimeProperty(time_property.time, prop_list.properties))  #  noqa: PERF401

    return bcf.Motion(
        motion.bone_name,
        motion.frame_count,
        motion.duration,
        motion.uses_positions,
        motion.uses_rotations,
        motion.position_offset,
        motion.rotation_offset,
        motion.property_lists,
        [bcf.TimePropertyList(time_properties)],
    )


def import_animations(file_paths: list[pathlib.Path], context: bpy.types.Context, logger: logging.Logger) -> None:
    """Import all the anim files in the list of files."""
    active_object = context.view_layer.objects.active

    anim_file_paths = [x for x in file_paths if x.suffix.lower() == ".anim"]
    if anim_file_paths and (active_object is None or active_object.type != 'ARMATURE'):
        logger.info("Please select an armature to apply the animation to.")
        return

    for file_path in anim_file_paths:
        try:
            animation = anim.read_file(file_path)

            skill = bcf.Skill(
                animation.name,
                animation.name,
                animation.duration,
                animation.distance,
                animation.moves,
                len(animation.translations),
                len(animation.rotations),
                [anim_motion_to_bcf_motion(x) for x in animation.motions],
            )
            animation_data = import_animation.AnimData(
                animation.translations,
                animation.rotations,
            )

            import_animation.import_animation(context, logger, active_object, skill, animation_data)

        except FileReadError as _:  # noqa: PERF203
            logger.info("Could not import %s.", file_path)


def import_files(
    context: bpy.types.Context,
    logger: logging.Logger,
    file_paths: list[pathlib.Path],
    *,
    cleanup_meshes: bool,
) -> None:
    """Import all the selected files."""
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    for file_path in [x for x in file_paths if x.suffix.lower() == ".skel"]:
        try:
            skeleton = skel.read_file(file_path)
            context.view_layer.objects.active = import_skeleton.import_skeleton(context, skeleton)

        except FileReadError as _:  # noqa: PERF203
            logger.info(f"Could not import {file_path}")  # noqa: G004

    active_object = context.view_layer.objects.active

    mesh_file_paths = [x for x in file_paths if x.suffix.lower() == ".mesh"]
    if mesh_file_paths and (active_object is None or active_object.type != 'ARMATURE'):
        logger.info("Please select an armature to apply the mesh to.")
        return

    mesh_objects = []
    for file_path in mesh_file_paths:
        try:
            sims_mesh = mesh.read_file(file_path)
            mesh_object = import_mesh.import_mesh(logger, file_path.stem, active_object, sims_mesh)
            if mesh_object is None:
                continue
            context.collection.objects.link(mesh_object)
            mesh_objects.append(mesh_object)

        except FileReadError as _:
            logger.info("Could not import %s.", file_path)

    mesh_objects = [obj for obj in mesh_objects if obj is not None]

    if mesh_objects:
        previous_active_object = context.view_layer.objects.active

        import_mesh.parent_and_clean_up_meshes(context, active_object, mesh_objects, cleanup_meshes=cleanup_meshes)

        bpy.ops.object.select_all(action='DESELECT')

        context.view_layer.objects.active = previous_active_object

    import_animations(file_paths, context, logger)
