"""Export The Sims Online files."""

import pathlib

import bpy

from . import export_mesh
from .ts1_formats import mesh


def export_files(
    context: bpy.types.Context,
    output_directory: pathlib.Path,
    *,
    export_meshes: bool,
    apply_modifiers: bool,
) -> None:
    """Export all the meshes in the scene."""
    if export_meshes:
        for mesh_object in [obj for obj in context.scene.objects if obj.type == 'MESH']:
            sims_mesh = export_mesh.export_mesh(mesh_object, apply_modifiers=apply_modifiers)
            mesh.write_file(output_directory / (mesh_object.name + ".mesh"), sims_mesh)
