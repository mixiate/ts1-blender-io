import bpy
import copy
import math
import mathutils
import os
import pathlib
import re

from . import bcf
from . import bmf
from . import cfp
from . import cmx
from . import texture_loader
from . import utils


def import_skeleton(context, skeleton):
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
            if bone.parent.matrix.to_4x4().to_quaternion().dot(previous_parent_quat) < 0.999999:
                bone.parent.tail = previous_parent_tail
            else:
                bone.use_connect = True

        if len(bone.children) == 0:
            bone.length = bone.parent.length

    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    armature_obj.select_set(True)
    return armature


def get_skin_type_skeleton_name(skin_name):
    # adult head
    if re.match("^xskin-c\\d{3}(f|m|u)a.*-head", skin_name.lower()):
        return "adult"

    # adult body
    if re.match("^xskin-b\\d{3}(f|m|u)a(skn|fit|fat|chd).*-body.*", skin_name.lower()):
        return "adult"

    # child head
    if re.match("^xskin-c\\d{3}(f|m|u)c.*-head", skin_name.lower()):
        return "child"

    # child body
    if re.match("^xskin-b\\d{3}(f|m|u)c(skn|fit|fat|chd|).*-body.*", skin_name.lower()):
        return "child"

    # child npc head
    if re.match("^xskin-.*chd_.*-head-.*", skin_name.lower()):
        return "child"

    # child npc body
    if re.match("^xskin-.*chd_.*-pelvis-.*", skin_name.lower()):
        return "child"

    # child costume
    if re.match("^xskin-ct-.*(f|m)c-.*", skin_name.lower()):
        return "child"

    # cat
    if re.match("^xskin-b\\d{3}(c|k)at.*", skin_name.lower()):
        return "kat"

    # dog
    if re.match("^xskin-b\\d{3}dog_.*", skin_name.lower()):
        return "dog"

    # skunk and raccoon
    if re.match("^xskin-.*-dogbody", skin_name.lower()):
        return "dog"

    # dragon
    if re.match("^xskin-b\\d{3}dragon_.*", skin_name.lower()):
        return "kat"

    # effects
    if re.match("^xskin-effects1-.*", skin_name.lower()):
        return "effects1"

    # gnome
    if re.match("^xskin-.*-gnomebody", skin_name.lower()):
        return "kat"

    return "adult"


def get_skill_type_skeleton_name(skill_name):
    if skill_name.startswith("a2"):
        return "adult"
    elif skill_name.startswith("c2"):
        return "child"
    elif skill_name.startswith("k2"):
        return "kat"
    elif skill_name.startswith("d2"):
        return "dog"

    raise Exception("Invalid skill name")


def find_or_import_skeleton(context, file_list, skeleton_name):
    if context.active_object is not None and context.active_object.name.startswith(skeleton_name):
        return bpy.data.armatures[context.active_object.name]

    if skeleton_name == "adult":
        skeleton_file_name = "adult-skeleton.cmx.bcf"
    elif skeleton_name == "child":
        skeleton_file_name = "child-skeleton.cmx.bcf"
    elif skeleton_name == "kat":
        skeleton_file_name = "kat_skeleton.cmx.bcf"
    elif skeleton_name == "dog":
        skeleton_file_name = "dog_skeleton.cmx.bcf"
    elif skeleton_name == "effects1":
        skeleton_file_name = "effects1-skeleton.cmx.bcf"

    armature = bpy.data.armatures.get(skeleton_name)
    if armature is None:
        for file_path in file_list:
            if os.path.basename(file_path) == skeleton_file_name:
                bcf_file = bcf.read_file(file_path)
                armature = import_skeleton(context, bcf_file.skeletons[0])

    return armature


def import_suit(
    context,
    logger,
    bcf_directory,
    file_list,
    texture_file_list,
    suit,
    cleanup_meshes,
    preferred_skin_color,
    armature_object_map,
):
    for skin in suit.skins:
        skeleton_name = get_skin_type_skeleton_name(skin.skin_name)
        armature = find_or_import_skeleton(context, file_list, skeleton_name)
        if armature is None:
            logger.info("Could not find or import {} skeleton used by {} .".format(skeleton_name, suit.name))
            continue

        bmf_file_path = os.path.join(bcf_directory, skin.skin_name + ".bmf")
        try:
            bmf_file = bmf.read_file(bmf_file_path)
        except:
            logger.info(
                "Could not load mesh {} used by {}.".format(
                    bmf_file_path,
                    suit.name,
                )
            )
            continue

        if not all(bone in armature.bones for bone in bmf_file.bones):
            logger.info(
                "Could not apply mesh {} to armature {}. The bones do not match.".format(
                    bmf_file.skin_name,
                    armature.name
                )
            )
            continue

        mesh = bpy.data.meshes.new(bmf_file.skin_name)
        obj = bpy.data.objects.new(bmf_file.skin_name, mesh)

        mesh_collection = bpy.data.collections.get(suit.name)
        if mesh_collection is None:
            mesh_collection = bpy.data.collections.new(suit.name)
        mesh_collection.objects.link(obj)
        if mesh_collection.name not in context.collection.children:
            context.collection.children.link(mesh_collection)

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

                bone_matrix_normal = bone_matrix.to_quaternion().to_matrix().to_4x4()
                normal = bone_matrix_normal @ mathutils.Vector(vertex.normal).xzy
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

        invalid_face_count = 0
        for face in bmf_file.faces:
            try:
                b_mesh.faces.new((b_mesh.verts[face[2]], b_mesh.verts[face[1]], b_mesh.verts[face[0]]))
            except:
                invalid_face_count += 1
        if invalid_face_count > 0:
            logger.info("Skipped {} invalid faces in mesh {}".format(invalid_face_count, bmf_file.skin_name))

        uv_layer = b_mesh.loops.layers.uv.verify()
        for face in b_mesh.faces:
            for loop in face.loops:
                uv = bmf_file.uvs[loop.vert.index]
                loop[uv_layer].uv = (uv[0], -uv[1])

        b_mesh.to_mesh(mesh)
        b_mesh.free()

        mesh.normals_split_custom_set_from_vertices(normals)

        texture_loader.load_textures(
            obj,
            texture_file_list,
            skin.skin_name,
            bmf_file.default_texture_name,
            preferred_skin_color
        )

        if not obj.data.materials:
            logger.info("Could not find a texture for mesh {}".format(bmf_file.skin_name))

        if armature_object_map.get(armature.name) is None:
            armature_object_map[armature.name] = list()

        armature_object_map[armature.name] += [obj.name]

        armature_obj = bpy.data.objects[armature.name]
        obj.location = armature_obj.location
        obj.rotation_euler = armature_obj.rotation_euler
        obj.scale = armature_obj.scale


def import_files(
    context,
    logger,
    file_paths,
    import_skeletons,
    import_meshes,
    import_animations,
    cleanup_meshes,
    preferred_skin_color
):
    bcf_files = []
    for file_path in file_paths:
        match os.path.splitext(file_path)[1]:
            case ".cmx":
                bcf_files.append((file_path, cmx.read_file(file_path)))
            case ".bcf":
                bcf_files.append((file_path, bcf.read_file(file_path)))

    file_search_directory = context.preferences.addons["io_scene_ts1"].preferences.file_search_directory
    if file_search_directory == "":
        file_search_directory = os.path.dirname(file_paths[0])
    file_list = list(map(lambda x: str(x), pathlib.Path(file_search_directory).rglob("*")))

    texture_file_list = [
        file_name for file_name in file_list
        if os.path.splitext(file_name)[1].lower() == ".bmp" \
        or os.path.splitext(file_name)[1].lower() == ".tga"
    ]

    if import_skeletons:
        for bcf_file_path, bcf_file in bcf_files:
            for skeleton in bcf_file.skeletons:
                import_skeleton(context, skeleton)

    if import_meshes:
        armature_object_map = {}
        for bcf_file_path, bcf_file in bcf_files:
            for suit in bcf_file.suits:
                import_suit(
                    context,
                    logger,
                    os.path.dirname(bcf_file_path),
                    file_list,
                    texture_file_list,
                    suit,
                    cleanup_meshes,
                    preferred_skin_color,
                    armature_object_map,
                )

        previous_active_object = context.view_layer.objects.active

        for armature_name in armature_object_map:
            bpy.ops.object.select_all(action='DESELECT')

            for object_name in armature_object_map[armature_name]:
                obj = bpy.data.objects[object_name]
                obj.select_set(True)

            if cleanup_meshes:
                context.view_layer.objects.active = bpy.data.objects[armature_object_map[armature_name][0]]
                bpy.ops.object.mode_set(mode='EDIT')

                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
                bpy.ops.mesh.select_all(action='SELECT')

                bpy.ops.mesh.merge_normals()
                bpy.ops.mesh.remove_doubles(use_sharp_edge_from_normals=True)
                bpy.ops.mesh.customdata_custom_splitnormals_clear()
                bpy.ops.mesh.faces_shade_smooth()

                bpy.ops.mesh.select_all(action='DESELECT')

                bpy.ops.object.mode_set(mode='OBJECT')

            armature_object = bpy.data.objects[armature_name]
            armature_object.select_set(True)
            context.view_layer.objects.active = armature_object
            bpy.ops.object.parent_set(type='ARMATURE')

        bpy.ops.object.select_all(action='DESELECT')

        context.view_layer.objects.active = previous_active_object

    for bcf_file_path, bcf_file in bcf_files:
        if not import_animations:
            break

        for skill in bcf_file.skills:
            skeleton_name = get_skill_type_skeleton_name(skill.skill_name)
            armature = find_or_import_skeleton(context, file_list, skeleton_name)
            if armature is None:
                logger.info("Could not find or import {} skeleton used by {} .".format(skeleton_name, bcf_file_path))
                continue

            armature_object = bpy.data.objects[armature.name]

            if skill.skill_name in bpy.data.actions:
                continue

            armature_object.animation_data_create()

            original_action = armature_object.animation_data.action if armature_object.animation_data.action is not None else None

            armature_object.animation_data.action = bpy.data.actions.new(name=skill.skill_name)
            action = armature_object.animation_data.action

            action.frame_range = (1.0, skill.motions[0].frame_count)

            action["distance"] = skill.distance

            cfp_file_path = os.path.join(os.path.dirname(bcf_file_path), skill.animation_name + ".cfp")
            cfp_file = cfp.read_file(cfp_file_path, skill.position_count, skill.rotation_count)

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

                for time_property_list in motion.time_property_lists:
                    for time_property in time_property_list.time_properties:
                        for event in time_property.events:
                            marker = action.pose_markers.new(name=motion.bone_name + " " + event.name + " " + event.value)
                            marker.frame = int(round(time_property.time / 33.3333333)) + 1

            track = armature_object.animation_data.nla_tracks.new(prev=None)
            track.name = skill.animation_name
            strip = track.strips.new(skill.skill_name, 1, action)
            armature_object.animation_data.action = original_action
