"""Import The Sims Online files."""

import logging
import pathlib

import bpy

from . import import_mesh, import_skeleton
from .ts1_formats import mesh, skel
from .ts1_formats.error import FileReadError


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
            context.collection.objects.link(mesh_object)
            mesh_objects.append(mesh_object)

        except FileReadError as _:  # noqa: PERF203
            logger.info("Could not import %s.", file_path)

    mesh_objects = [obj for obj in mesh_objects if obj is not None]

    if mesh_objects:
        previous_active_object = context.view_layer.objects.active

        import_mesh.parent_and_clean_up_meshes(context, active_object, mesh_objects, cleanup_meshes=cleanup_meshes)

        bpy.ops.object.select_all(action='DESELECT')

        context.view_layer.objects.active = previous_active_object
