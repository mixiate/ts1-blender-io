"""Import The Sims mesh in to Blender."""

import logging
import math

import bmesh
import bpy
import mathutils

from . import utils
from .ts1_formats.bmf import Mesh


def import_mesh(
    logger: logging.Logger, mesh_name: str, armature_object: bpy.types.Object, sims_mesh: Mesh
) -> bpy.types.Object | None:
    """Create a mesh object for the mesh."""
    armature = armature_object.data

    if not all(bone in armature.bones for bone in sims_mesh.bones):
        logger.info(
            f"Could not apply mesh {mesh_name} to armature {armature_object.name}. The bones do not match.",  # noqa: G004
        )
        return None

    mesh = bpy.data.meshes.new(mesh_name)
    obj = bpy.data.objects.new(mesh_name, mesh)

    b_mesh = bmesh.new()

    normals = []
    deform_layer = b_mesh.verts.layers.deform.verify()

    for bone_binding in sims_mesh.bone_bindings:
        if bone_binding.bone_index >= len(sims_mesh.bones):
            logger.info("Invalid bone index in %s.", mesh_name)
            return None
        bone_name = sims_mesh.bones[bone_binding.bone_index]

        armature_bone = armature.bones[bone_name]
        bone_matrix = armature_bone.matrix_local @ utils.BONE_ROTATION_OFFSET_INVERTED

        vertex_group = obj.vertex_groups.new(name=bone_name)

        vertex_index_start = bone_binding.vertex_index
        vertex_index_end = vertex_index_start + bone_binding.vertex_count
        for vertex in sims_mesh.vertices[vertex_index_start:vertex_index_end]:
            position = mathutils.Vector(vertex.position).xzy / utils.BONE_SCALE
            b_mesh_vertex = b_mesh.verts.new(bone_matrix @ position)

            bone_matrix_normal = bone_matrix.to_quaternion().to_matrix().to_4x4()
            normal = bone_matrix_normal @ mathutils.Vector(vertex.normal).xzy
            normals.append(normal)

            b_mesh_vertex[deform_layer][vertex_group.index] = 1.0

    b_mesh.verts.ensure_lookup_table()
    b_mesh.verts.index_update()

    for bone_binding in sims_mesh.bone_bindings:
        bone_name = sims_mesh.bones[bone_binding.bone_index]
        vertex_group = obj.vertex_groups[bone_name]

        armature_bone = armature.bones[bone_name]
        bone_matrix = armature_bone.matrix_local @ utils.BONE_ROTATION_OFFSET_INVERTED

        blend_index_start = bone_binding.blended_vertex_index
        blend_index_end = blend_index_start + bone_binding.blended_vertex_count
        for blend_index, blend in enumerate(sims_mesh.blends[blend_index_start:blend_index_end]):
            weight = float(blend.weight) * math.pow(2, -15)

            vertex_position = b_mesh.verts[blend.vertex_index].co
            blend_position = sims_mesh.blend_vertices[blend_index_start + blend_index].position
            blend_position = mathutils.Vector(blend_position).xzy / utils.BONE_SCALE
            blend_position = bone_matrix @ blend_position
            vertex_position *= 1 - weight
            blend_position *= weight
            b_mesh.verts[blend.vertex_index].co = vertex_position + blend_position

            for inner_bone_binding in sims_mesh.bone_bindings:
                vertex_index_start = inner_bone_binding.vertex_index
                vertex_index_end = vertex_index_start + inner_bone_binding.vertex_count
                if blend.vertex_index >= vertex_index_start and blend.vertex_index < vertex_index_end:
                    original_bone_name = sims_mesh.bones[inner_bone_binding.bone_index]

            original_vertex_group = obj.vertex_groups[original_bone_name]
            b_mesh.verts[blend.vertex_index][deform_layer][original_vertex_group.index] = 1 - weight
            b_mesh.verts[blend.vertex_index][deform_layer][vertex_group.index] = weight

    invalid_face_count = 0
    for face in sims_mesh.faces:
        try:
            b_mesh.faces.new((b_mesh.verts[face[2]], b_mesh.verts[face[1]], b_mesh.verts[face[0]]))
        except ValueError as _:  # noqa: PERF203
            invalid_face_count += 1

    if invalid_face_count > 0:
        logger.info(f"Skipped {invalid_face_count} invalid faces in mesh {mesh_name}")  # noqa: G004

    uv_layer = b_mesh.loops.layers.uv.verify()
    for face in b_mesh.faces:
        for loop in face.loops:
            uv = sims_mesh.uvs[loop.vert.index]
            loop[uv_layer].uv = (uv[0], 1 - uv[1])

    b_mesh.to_mesh(mesh)
    b_mesh.free()

    mesh.normals_split_custom_set_from_vertices(normals)

    obj.location = armature_object.location
    obj.rotation_euler = armature_object.rotation_euler
    obj.scale = armature_object.scale

    return obj


def parent_and_clean_up_meshes(
    context: bpy.types.Context, armature: bpy.types.Object, objects: list[bpy.types.Object], *, cleanup_meshes: bool
) -> None:
    """Parents all objects in the list to an armature at once and optionally cleans up the meshes.

    It's a lot faster to do this in bulk when importing many meshes at the same time.
    """
    bpy.ops.object.select_all(action='DESELECT')

    for obj in objects:
        obj.select_set(state=True)

    if cleanup_meshes:
        context.view_layer.objects.active = objects[0]
        bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.mesh.select_all(action='SELECT')

        bpy.ops.mesh.merge_normals()
        bpy.ops.mesh.remove_doubles(use_sharp_edge_from_normals=True)
        bpy.ops.mesh.faces_shade_smooth()
        bpy.ops.mesh.normals_make_consistent()

        bpy.ops.mesh.select_all(action='DESELECT')

        bpy.ops.object.mode_set(mode='OBJECT')

        for obj in objects:
            context.view_layer.objects.active = obj
            bpy.ops.mesh.customdata_custom_splitnormals_clear()

    armature.select_set(state=True)
    context.view_layer.objects.active = armature
    bpy.ops.object.parent_set(type='ARMATURE')
