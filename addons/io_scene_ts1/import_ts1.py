import bpy
import copy
import math
import mathutils
import os

from . import bcf
from . import bmf
from . import cfp
from . import utils

def import_files(context, file_paths, cleanup_meshes):
    bcf_files = []
    for file_path in file_paths:
        file = open(file_path, mode='rb')
        bcf_files.append(bcf.bcf_struct().parse(file.read()))

    for bcf_file in bcf_files:
        for skeleton in bcf_file.skeletons:
            if skeleton.name in bpy.data.armatures:
                continue
            armature = bpy.data.armatures.new(name=skeleton.name)
            armature_obj = bpy.data.objects.new(name=skeleton.name, object_data=armature)
            context.collection.objects.link(armature_obj)

            context.view_layer.objects.active = armature_obj
            bpy.ops.object.mode_set(mode='EDIT')

            for bone in skeleton.bones:
                armature_bone = armature.edit_bones.new(name=bone.name)

                parent_matrix = mathutils.Matrix()
                if bone.parent != "NULL":
                    armature_bone.parent = armature.edit_bones[bone.parent]
                    parent_matrix = armature.edit_bones[bone.parent].matrix @ utils.BONE_ROTATION_OFFSET.inverted()

                armature_bone.head = mathutils.Vector((0.0, 0.0, 0.0))
                armature_bone.tail = mathutils.Vector((0.1, 0.0, 0.0))

                rotation = mathutils.Quaternion(
                    (bone.rotation_w, bone.rotation_x, bone.rotation_z, bone.rotation_y)
                ).to_matrix().to_4x4()

                translation = mathutils.Matrix.Translation(mathutils.Vector(
                    (bone.position_x, bone.position_z, bone.position_y)
                ) / utils.BONE_SCALE)

                armature_bone.matrix = (parent_matrix @ (translation @ rotation)) @ utils.BONE_ROTATION_OFFSET

                armature_bone["ts1_translate"] = bone.translate
                armature_bone["ts1_rotate"] = bone.rotate
                armature_bone["ts1_blend"] = bone.blend_suits
                armature_bone["ts1_wiggle_value"] = bone.wiggle_value
                armature_bone["ts1_wiggle_power"] = bone.wiggle_power

                for property_list in bone.properties:
                    for prop in property_list.properties:
                        armature_bone["ts1_" + prop.name] = prop.value

            for bone in armature.edit_bones:
                if bone.parent != None:
                    previous_parent_tail = copy.copy(bone.parent.tail)
                    previous_parent_quat = bone.parent.matrix.to_4x4().to_quaternion()
                    bone.parent.tail = bone.head
                    if bone.parent.matrix.to_4x4().to_quaternion().dot(previous_parent_quat) < 0.9999999:
                        bone.parent.tail = previous_parent_tail
                    else:
                        bone.use_connect = True

                if len(bone.children) == 0:
                    bone.length = bone.parent.length

            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.object.select_all(action='DESELECT')
            armature_obj.select_set(True)

    for bcf_file in bcf_files:
        for suit in bcf_file.suits:
            for skin in suit.skins:
                if context.active_object.name not in bpy.data.armatures:
                    raise Exception("please select the armature you want to add the meshes to")
                armature = bpy.data.armatures[context.active_object.name]

                bmf_file_path = os.path.join(os.path.dirname(file_path), skin.skin_name + ".bmf")
                bmf_file = bmf.read_file(bmf_file_path)

                for bone in bmf_file.bones:
                    if bone not in armature.bones:
                        raise Exception("could not apply mesh to this armature, bones do not match")

                mesh = bpy.data.meshes.new(bmf_file.skin_name)
                obj = bpy.data.objects.new(bmf_file.skin_name, mesh)
                context.collection.objects.link(obj)

                import bmesh
                b_mesh = bmesh.new()

                normals = list()
                deform_layer = b_mesh.verts.layers.deform.verify()

                for bone_binding in bmf_file.bone_bindings:
                    bone_name = bmf_file.bones[bone_binding.bone_index]

                    armature_bone = armature.bones[bone_name]
                    bone_matrix = armature_bone.matrix_local @ utils.BONE_ROTATION_OFFSET.inverted()

                    vertex_group = obj.vertex_groups.new(name=bone_name)

                    vertex_index_start = bone_binding.vertex_index
                    vertex_index_end = vertex_index_start + bone_binding.vertex_count
                    for vertex in bmf_file.vertices[vertex_index_start:vertex_index_end]:
                        position = mathutils.Vector(vertex.position).xzy / utils.BONE_SCALE
                        b_mesh_vertex = b_mesh.verts.new(bone_matrix @ position)

                        normal = bone_matrix.to_quaternion().to_matrix().to_4x4() @ mathutils.Vector(vertex.normal).xzy
                        normals.append(normal)

                        b_mesh_vertex[deform_layer][vertex_group.index] = 1.0

                b_mesh.verts.ensure_lookup_table()
                b_mesh.verts.index_update()

                for bone_binding in bmf_file.bone_bindings:
                    bone_name = bmf_file.bones[bone_binding.bone_index]
                    vertex_group = obj.vertex_groups[bone_name]

                    blend_index_start = bone_binding.blended_vertex_index
                    blend_index_end = blend_index_start + bone_binding.blended_vertex_count
                    for blend in bmf_file.blends[blend_index_start:blend_index_end]:
                        for bone_binding in bmf_file.bone_bindings:
                            vertex_index_start = bone_binding.vertex_index
                            vertex_index_end = vertex_index_start + bone_binding.vertex_count
                            if blend.vertex_index >= vertex_index_start and blend.vertex_index < vertex_index_end:
                                original_bone_name = bmf_file.bones[bone_binding.bone_index]

                        original_vertex_group = obj.vertex_groups[original_bone_name]
                        weight = float(blend.weight) * math.pow(2, -15)
                        b_mesh.verts[blend.vertex_index][deform_layer][original_vertex_group.index] = 1 - weight
                        b_mesh.verts[blend.vertex_index][deform_layer][vertex_group.index] = weight

                for face in bmf_file.faces:
                    try:
                        b_mesh.faces.new((b_mesh.verts[face[2]], b_mesh.verts[face[1]], b_mesh.verts[face[0]]))
                    except:
                        continue

                uv_layer = b_mesh.loops.layers.uv.verify()
                for face in b_mesh.faces:
                    for loop in face.loops:
                        uv = bmf_file.uvs[loop.vert.index]
                        loop[uv_layer].uv = (uv[0], -uv[1])

                b_mesh.to_mesh(mesh)
                b_mesh.free()

                mesh.normals_split_custom_set_from_vertices(normals)

                if cleanup_meshes:
                    original_active_object = context.view_layer.objects.active

                    context.view_layer.objects.active = obj
                    bpy.ops.object.mode_set(mode = 'EDIT')

                    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
                    bpy.ops.mesh.select_all(action='SELECT')

                    bpy.ops.mesh.merge_normals()
                    bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=False, use_sharp_edge_from_normals=True)
                    bpy.ops.mesh.customdata_custom_splitnormals_clear()
                    bpy.ops.mesh.faces_shade_smooth()

                    bpy.ops.mesh.select_all(action='DESELECT')

                    bpy.ops.object.mode_set(mode = 'OBJECT')

                    context.view_layer.objects.active = original_active_object

                texture_file_path = os.path.join(os.path.dirname(file_path), bmf_file.default_texture_name + ".bmp")

                if os.path.exists(texture_file_path):
                    material = bpy.data.materials.get(bmf_file.default_texture_name)
                    if material is None:
                        material = bpy.data.materials.new(name=bmf_file.default_texture_name)

                    image = bpy.data.images.load(texture_file_path)
                    material.use_nodes = True

                    image_node = material.node_tree.nodes.new('ShaderNodeTexImage')
                    image_node.image = image

                    principled_BSDF = material.node_tree.nodes.get('Principled BSDF')
                    material.node_tree.links.new(image_node.outputs[0], principled_BSDF.inputs[0])
                    principled_BSDF.inputs[2].default_value = 1.0
                    principled_BSDF.inputs[12].default_value = 0.0

                    obj.data.materials.append(material)

        for skill in bcf_file.skills:
            cfp_file_path = os.path.join(os.path.dirname(file_path), skill.animation_name + ".cfp")
            cfp_file = cfp.read_file(cfp_file_path, skill.position_count, skill.rotation_count)

            armature = None
            try:
                armature = next(x for x in bpy.data.armatures if x.name[0] == skill.skill_name[0])
            except:
                raise Exception("no skeleton found. please import the " + skill.skill_name[0] + " skeleton")
            armature_object = bpy.data.objects[armature.name]

            if skill.skill_name in bpy.data.actions:
                continue

            armature_object.animation_data_create()

            original_action = armature_object.animation_data.action if armature_object.animation_data.action is not None else None

            armature_object.animation_data.action = bpy.data.actions.new(name=skill.skill_name)
            action = armature_object.animation_data.action

            action.frame_range = (1.0, skill.motions[0].frame_count)

            action["distance"] = skill.distance

            for motion in skill.motions:
                for frame in range(motion.frame_count):
                    bone = next(x for x in armature_object.pose.bones if x.name == motion.bone_name)

                    translation = mathutils.Matrix()
                    if motion.positions_used_flag:
                        translation = mathutils.Matrix.Translation(mathutils.Vector((
                            cfp_file["positions_x"][motion.position_offset + frame] / utils.BONE_SCALE,
                            cfp_file["positions_z"][motion.position_offset + frame] / utils.BONE_SCALE,
                            cfp_file["positions_y"][motion.position_offset + frame] / utils.BONE_SCALE,
                        )))

                    rotation = mathutils.Matrix()
                    if motion.rotations_used_flag:
                        rotation = (mathutils.Quaternion((
                            cfp_file["rotations_w"][motion.rotation_offset + frame],
                            cfp_file["rotations_x"][motion.rotation_offset + frame],
                            cfp_file["rotations_z"][motion.rotation_offset + frame],
                            cfp_file["rotations_y"][motion.rotation_offset + frame],
                        ))).normalized().to_matrix().to_4x4()

                    parent_matrix = mathutils.Matrix()
                    if bone.parent != None:
                        parent_matrix = bone.parent.matrix @ utils.BONE_ROTATION_OFFSET.inverted()

                    bone.matrix = (parent_matrix @ (translation @ rotation)) @ utils.BONE_ROTATION_OFFSET

                    if motion.positions_used_flag:
                        bone.keyframe_insert("location", frame=frame + 1)
                    else:
                        bone.location = (0.0, 0.0, 0.0)
                    if motion.rotations_used_flag:
                        bone.keyframe_insert("rotation_quaternion", frame=frame + 1)

                for time_props in motion.time_properties:
                    for time_prop in time_props.properties:
                        for event in time_prop.events:
                            marker = action.pose_markers.new(name=motion.bone_name + " " + event.name + " " + event.value)
                            marker.frame = int(round(time_prop.time / 33.3333333)) + 1

            track = armature_object.animation_data.nla_tracks.new(prev=None)
            track.name = skill.animation_name
            strip = track.strips.new(skill.skill_name, 1, action)
            armature_object.animation_data.action = original_action
