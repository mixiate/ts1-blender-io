"""Export Blender mesh to The Sims mesh."""

import math

import bpy

from . import utils
from .ts1_formats import bmf
from .utils import ExportError

MAX_VERTEX_GROUP_COUNT = 2


def export_mesh(obj: bpy.types.Object, *, apply_modifiers: bool) -> bmf.Mesh:
    """Export a mesh object to a sims mesh."""
    if apply_modifiers:
        armature_modifiers = {}
        for i, modifier in enumerate(obj.modifiers):
            if modifier.type == 'ARMATURE':
                armature_modifiers[i] = modifier.show_viewport
                modifier.show_viewport = False

        depsgraph = bpy.context.evaluated_depsgraph_get()
        mesh_owner = obj.evaluated_get(depsgraph)
        mesh = mesh_owner.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    else:
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

    bones: list[str] = []
    bone_bindings: list[bmf.BoneBinding] = []
    blends: list[bmf.Blend] = []
    vertices: list[bmf.Vertex] = []
    uvs: list[tuple[float, float]] = []

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
            ),
        )
        bones.append(vertex_group.name)

        vertices += vertex_group_vertices
        uvs += vertex_group_uvs

    # create blended vertices
    blended_vertices: list[bmf.Vertex] = []
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

    faces = [
        (
            vertex_index_map.index(face[2]),
            vertex_index_map.index(face[1]),
            vertex_index_map.index(face[0]),
        )
        for face in new_faces
    ]

    if apply_modifiers:
        for i, show_viewport in armature_modifiers.items():
            obj.modifiers[i].show_viewport = show_viewport

        mesh_owner.to_mesh_clear()

    return bmf.Mesh(
        bones,
        faces,
        bone_bindings,
        uvs,
        blends,
        vertices,
        blended_vertices,
    )
