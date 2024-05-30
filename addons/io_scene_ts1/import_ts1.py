import bmesh
import bpy
import copy
import math
import mathutils
import pathlib
import re


from . import bcf
from . import bmf
from . import cfp
from . import cmx
from . import skn
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
            parent_matrix = armature.edit_bones[bone.parent].matrix @ utils.BONE_ROTATION_OFFSET_INVERTED

        armature_bone.head = mathutils.Vector((0.0, 0.0, 0.0))
        armature_bone.tail = mathutils.Vector((0.1, 0.0, 0.0))

        rotation = (
            mathutils.Quaternion((bone.rotation_w, bone.rotation_x, bone.rotation_z, bone.rotation_y))
            .to_matrix()
            .to_4x4()
        )

        translation = mathutils.Matrix.Translation(
            mathutils.Vector((bone.position_x, bone.position_z, bone.position_y)) / utils.BONE_SCALE
        )

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
        if bone.parent:
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


def get_skin_type_skeleton_names(skin_name: str) -> list[str]:
    """Get a list of skeletons that a skin can be applied to"""
    # adult head
    if re.match("^xskin-c\\d{3}(f|m|u)a.*-head", skin_name.lower()):
        return ["adult"]

    # adult body
    if re.match("^xskin-b\\d{3}(f|m|u)a(skn|fit|fat|chd).*-body.*", skin_name.lower()):
        return ["adult"]

    # child head
    if re.match("^xskin-c\\d{3}(f|m|u)c.*-head", skin_name.lower()):
        return ["child"]

    # child body
    if re.match("^xskin-b\\d{3}(f|m|u)c(skn|fit|fat|chd|).*-body.*", skin_name.lower()):
        return ["child"]

    # child npc head
    if re.match("^xskin-.*chd_.*-head-.*", skin_name.lower()):
        return ["child"]

    # child npc body
    if re.match("^xskin-.*chd_.*-pelvis-.*", skin_name.lower()):
        return ["child"]

    # child costume
    if re.match("^xskin-ct-.*(f|m)c-.*", skin_name.lower()):
        return ["child"]

    # cat
    if re.match("^xskin-b\\d{3}(c|k)at.*", skin_name.lower()):
        return ["kat"]

    # dog
    if re.match("^xskin-b\\d{3}dog_.*", skin_name.lower()):
        return ["dog"]

    # skunk and raccoon
    if re.match("^xskin-.*-dogbody", skin_name.lower()):
        return ["dog"]

    # dragon
    if re.match("^xskin-b\\d{3}dragon_.*", skin_name.lower()):
        return ["kat"]

    # effects
    if re.match("^xskin-effects1-.*", skin_name.lower()):
        return ["effects1"]

    # gnome
    if re.match("^xskin-.*-gnomebody", skin_name.lower()):
        return ["kat"]

    # cat accessories
    if re.match("^xskin-cat.*-cat-", skin_name.lower()):
        return ["kat"]

    # dog accessories
    if re.match("^xskin-dog.*-dog-", skin_name.lower()):
        return ["dog"]

    return ["adult", "child"]


class UnknownSkillTypeError(Exception):
    """Unknown skill type error."""


def get_skill_type_skeleton_name(skill_name: str) -> list[str]:
    """Return the name of the skeleton that the skill type uses"""
    if skill_name.startswith("a2"):
        return ["adult"]
    if skill_name.startswith("c2"):
        return ["child"]
    if skill_name.startswith("k2"):
        return ["kat"]
    if skill_name.startswith("d2"):
        return ["dog"]
    if skill_name.startswith("f2"):
        return ["kat"]
    if skill_name.startswith("effects-"):
        return ["effects1"]

    raise UnknownSkillTypeError


def find_or_import_skeleton(context, file_list, skeleton_names):
    if context.active_object is not None:
        for skeleton_name in skeleton_names:
            if context.active_object.name.startswith(skeleton_name):
                return bpy.data.armatures[context.active_object.name]

    if skeleton_names[0] == "adult":
        skeleton_file_name = "adult-skeleton.cmx.bcf"
    elif skeleton_names[0] == "child":
        skeleton_file_name = "child-skeleton.cmx.bcf"
    elif skeleton_names[0] == "kat":
        skeleton_file_name = "kat_skeleton.cmx.bcf"
    elif skeleton_names[0] == "dog":
        skeleton_file_name = "dog_skeleton.cmx.bcf"
    elif skeleton_names[0] == "effects1":
        skeleton_file_name = "effects1-skeleton.cmx.bcf"

    armature = bpy.data.armatures.get(skeleton_names[0])
    if armature is None:
        for file_path in file_list:
            if file_path.name == skeleton_file_name:
                bcf_file = bcf.read_file(file_path)
                return import_skeleton(context, bcf_file.skeletons[0])

    return armature


def import_suit(
    context,
    logger,
    bcf_directory,
    file_list,
    texture_file_list,
    suit,
    fix_textures,
    preferred_skin_color,
    armature_object_map,
):
    for skin in suit.skins:
        skeleton_names = get_skin_type_skeleton_names(skin.skin_name)
        armature = find_or_import_skeleton(context, file_list, skeleton_names)
        if armature is None:
            logger.info(f"Could not find or import {skeleton_names[0]} skeleton used by {suit.name} .")
            continue

        try:
            bmf_file_path = bcf_directory / (skin.skin_name + ".bmf")
            if bmf_file_path.is_file():
                bmf_file = bmf.read_file(bmf_file_path)
            else:
                skn_file_path = bcf_directory / (skin.skin_name + ".skn")
                bmf_file = skn.read_file(skn_file_path)
        except utils.FileReadError as _:
            logger.info(f"Could not load mesh {skin.skin_name} used by {suit.name}.")
            continue

        if not all(bone in armature.bones for bone in bmf_file.bones):
            logger.info(f"Could not apply mesh {skin.skin_name} to armature {armature.name}. The bones do not match.")
            continue

        mesh = bpy.data.meshes.new(skin.skin_name)
        obj = bpy.data.objects.new(skin.skin_name, mesh)

        mesh_collection = bpy.data.collections.get(suit.name)
        if mesh_collection is None:
            mesh_collection = bpy.data.collections.new(suit.name)
            mesh_collection["Suit Type"] = suit.suit_type
        mesh_collection.objects.link(obj)
        if mesh_collection.name not in context.collection.children:
            context.collection.children.link(mesh_collection)

        obj["Bone Name"] = skin.bone_name
        obj["Censor Flags"] = skin.censor_flags

        b_mesh = bmesh.new()

        normals = []
        deform_layer = b_mesh.verts.layers.deform.verify()

        for bone_binding in bmf_file.bone_bindings:
            bone_name = bmf_file.bones[bone_binding.bone_index]

            armature_bone = armature.bones[bone_name]
            bone_matrix = armature_bone.matrix_local @ utils.BONE_ROTATION_OFFSET_INVERTED

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
            except ValueError as _:
                invalid_face_count += 1

        if invalid_face_count > 0:
            logger.info(f"Skipped {invalid_face_count} invalid faces in mesh {skin.skin_name}")

        uv_layer = b_mesh.loops.layers.uv.verify()
        for face in b_mesh.faces:
            for loop in face.loops:
                uv = bmf_file.uvs[loop.vert.index]
                loop[uv_layer].uv = (uv[0], 1 - uv[1])

        b_mesh.to_mesh(mesh)
        b_mesh.free()

        mesh.normals_split_custom_set_from_vertices(normals)

        texture_loader.load_textures(
            obj,
            texture_file_list,
            skin.skin_name,
            bmf_file.default_texture_name,
            fix_textures,
            preferred_skin_color,
        )

        if not obj.data.materials:
            logger.info(f"Could not find a texture for mesh {skin.skin_name}")

        if armature_object_map.get(armature.name) is None:
            armature_object_map[armature.name] = []

        armature_object_map[armature.name] += [obj.name]

        armature_obj = bpy.data.objects[armature.name]
        obj.location = armature_obj.location
        obj.rotation_euler = armature_obj.rotation_euler
        obj.scale = armature_obj.scale


def create_fcurve_data(action, data_path, index, count, data):
    f_curve = action.fcurves.new(data_path, index=index)
    f_curve.keyframe_points.add(count=count)
    f_curve.keyframe_points.foreach_set("co", data)
    f_curve.update()


def import_skill(context, logger, file_directory, file_list, skill):
    cfp_file_path = file_directory / (skill.animation_name + ".cfp")
    try:
        cfp_file = cfp.read_file(cfp_file_path, skill.position_count, skill.rotation_count)
    except utils.FileReadError as _:
        logger.info(f"Could not load cfp file {cfp_file_path}")
        return

    skeleton_name = get_skill_type_skeleton_name(skill.skill_name)
    armature = find_or_import_skeleton(context, file_list, skeleton_name)
    if armature is None:
        logger.info(f"Could not find or import {skeleton_name} skeleton used by {skill.skill_name}")
        return

    armature_object = bpy.data.objects[armature.name]

    if skill.skill_name in bpy.data.actions:
        return

    if not all(x in armature.bones for x in (x.bone_name for x in skill.motions)):
        logger.info(
            f"Could not apply animation {skill.skill_name} to armature {armature.name}. The bones do not match."
        )
        return

    armature_object.animation_data_create()

    original_action = armature_object.animation_data.action

    armature_object.animation_data.action = bpy.data.actions.new(name=skill.skill_name)
    action = armature_object.animation_data.action

    action.frame_range = (1.0, skill.motions[0].frame_count)

    action["Distance"] = skill.distance

    for motion in skill.motions:
        bone = armature_object.pose.bones[motion.bone_name]

        parent_bone_matrix = mathutils.Matrix()
        if bone.parent:
            parent_bone_matrix = bone.parent.bone.matrix_local @ utils.BONE_ROTATION_OFFSET_INVERTED

        positions_x = []
        positions_y = []
        positions_z = []
        rotations_w = []
        rotations_x = []
        rotations_y = []
        rotations_z = []

        for frame in range(motion.frame_count):
            translation = mathutils.Matrix()
            if motion.positions_used_flag:
                translation = mathutils.Matrix.Translation(
                    mathutils.Vector(
                        (
                            cfp_file.positions_x[motion.position_offset + frame] / utils.BONE_SCALE,
                            cfp_file.positions_z[motion.position_offset + frame] / utils.BONE_SCALE,  # swap y and z
                            cfp_file.positions_y[motion.position_offset + frame] / utils.BONE_SCALE,
                        )
                    )
                )

            rotation = mathutils.Matrix()
            if motion.rotations_used_flag:
                rotation = (
                    mathutils.Quaternion(
                        (
                            cfp_file.rotations_w[motion.rotation_offset + frame],
                            cfp_file.rotations_x[motion.rotation_offset + frame],
                            cfp_file.rotations_z[motion.rotation_offset + frame],  # swap y and z
                            cfp_file.rotations_y[motion.rotation_offset + frame],
                        )
                    )
                    .to_matrix()
                    .to_4x4()
                )

            bone_matrix = parent_bone_matrix @ (translation @ rotation)
            bone_matrix = bone.bone.convert_local_to_pose(
                bone_matrix,
                bone.bone.matrix_local,
                invert=True,
            )
            bone_matrix @= utils.BONE_ROTATION_OFFSET

            if motion.positions_used_flag:
                translation = bone_matrix.to_translation()
                positions_x += (float(frame + 1), translation.x)
                positions_y += (float(frame + 1), translation.y)
                positions_z += (float(frame + 1), translation.z)

            if motion.rotations_used_flag:
                rotation = bone_matrix.to_quaternion()
                rotations_w += (float(frame + 1), rotation.w)
                rotations_x += (float(frame + 1), rotation.x)
                rotations_y += (float(frame + 1), rotation.y)
                rotations_z += (float(frame + 1), rotation.z)

        if motion.positions_used_flag:
            data_path = bone.path_from_id("location")
            create_fcurve_data(action, data_path, 0, motion.frame_count, positions_x)
            create_fcurve_data(action, data_path, 1, motion.frame_count, positions_y)
            create_fcurve_data(action, data_path, 2, motion.frame_count, positions_z)

        if motion.rotations_used_flag:
            data_path = bone.path_from_id("rotation_quaternion")
            create_fcurve_data(action, data_path, 0, motion.frame_count, rotations_w)
            create_fcurve_data(action, data_path, 1, motion.frame_count, rotations_x)
            create_fcurve_data(action, data_path, 2, motion.frame_count, rotations_y)
            create_fcurve_data(action, data_path, 3, motion.frame_count, rotations_z)

    for motion in skill.motions:
        for time_property_list in motion.time_property_lists:
            for time_property in time_property_list.time_properties:
                for event in time_property.events:
                    event_string = f"{motion.bone_name} {event.name} {event.value}"
                    frame = int(round(time_property.time / 33.3333333)) + 1

                    markers = [x for x in action.pose_markers if x.frame == frame]

                    if len(markers) == 0:
                        marker = action.pose_markers.new(name=event_string)
                        marker.frame = frame
                    else:
                        last_marker = action.pose_markers[-1]
                        if len(last_marker.name) + 1 + len(event_string) <= 63:  # room for null
                            last_marker.name = f"{last_marker.name};{event_string}"
                        else:
                            marker = action.pose_markers.new(name=event_string)
                            marker.frame = frame

    track = armature_object.animation_data.nla_tracks.new(prev=None)
    track.name = skill.animation_name
    track.strips.new(skill.skill_name, 1, action)
    armature_object.animation_data.action = original_action


def import_files(
    context,
    logger,
    file_paths,
    import_skeletons,
    import_meshes,
    import_animations,
    cleanup_meshes,
    fix_textures,
    preferred_skin_color,
):
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    bcf_files = []
    for file_path in file_paths:
        match file_path.suffix:
            case ".cmx":
                bcf_files.append((file_path, cmx.read_file(file_path)))
            case ".bcf":
                bcf_files.append((file_path, bcf.read_file(file_path)))

    file_search_directory = context.preferences.addons["io_scene_ts1"].preferences.file_search_directory
    if file_search_directory == "":
        file_search_directory = file_paths[0].parent
    file_list = list(pathlib.Path(file_search_directory).rglob("*"))

    texture_file_list = [
        file_name for file_name in file_list if file_name.suffix.lower() == ".bmp" or file_name.suffix.lower() == ".tga"
    ]

    if import_skeletons:
        for _, bcf_file in bcf_files:
            for skeleton in bcf_file.skeletons:
                import_skeleton(context, skeleton)

    if import_meshes:
        armature_object_map = {}
        for bcf_file_path, bcf_file in bcf_files:
            for suit in bcf_file.suits:
                import_suit(
                    context,
                    logger,
                    bcf_file_path.parent,
                    file_list,
                    texture_file_list,
                    suit,
                    fix_textures,
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

    if import_animations:
        for bcf_file_path, bcf_file in bcf_files:
            for skill in bcf_file.skills:
                import_skill(context, logger, bcf_file_path.parent, file_list, skill)
