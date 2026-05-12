"""Import The Sims 1 3D formats in to Blender."""

import logging
import pathlib
import re

import bpy
import bpy_extras.anim_utils
import mathutils

from . import import_mesh, import_skeleton, texture_loader, utils
from .ts1_formats import bcf, bmf, cfp, cmx, skn
from .ts1_formats.error import FileReadError as TS1FileReadError


def get_skin_type_skeleton_names(skin_name: str) -> list[str]:  # noqa: PLR0911
    """Get a list of skeletons that a skin can be applied to."""
    # gnome
    if re.match("^xskin-SpellboundMAFat_Gnome-.*-GNOMEBODY.*", skin_name):
        return ["kat"]

    # adult head
    if re.match("^xskin-c\\d{3}(f|m|u)a.*-head", skin_name.lower()):
        return ["adult"]

    # adult body
    if re.match("^xskin-(b|f|h|l|s|w)\\d{3}(f|m|u)a(skn|fit|fat|chd).*-body.*", skin_name.lower()):
        return ["adult"]

    # child head
    if re.match("^xskin-c\\d{3}(f|m|u)c.*-head", skin_name.lower()):
        return ["child"]

    # child body
    if re.match("^xskin-(b|f|h|l|s|w)\\d{3}(f|m|u)c(skn|fit|fat|chd|).*-body.*", skin_name.lower()):
        return ["child"]

    # adult npc head
    if re.match("^xskin-c((?!\\d{3}).).*(f|m|u)a(skn|fit|fat|)_.*-head-.*", skin_name.lower()):
        return ["adult"]

    # child npc head
    if re.match("^xskin-c((?!\\d{3}).).*(f|m|u)cchd_.*-head-.*", skin_name.lower()):
        return ["child"]

    # adult npc body
    if re.match("^xskin-((?!\\d{3}).).*(f|m|u)a(skn|fit|fat)_.*-pelvis-.*", skin_name.lower()):
        return ["adult"]

    # child npc body
    if re.match("^xskin-.*chd_.*-pelvis-.*", skin_name.lower()):
        return ["child"]

    # adult costume
    if re.match("^xskin-ct-.*(f|m)a-.*", skin_name.lower()):
        return ["adult"]

    # child costume
    if re.match("^xskin-ct-.*(f|m)c-.*", skin_name.lower()):
        return ["child"]

    # unleashed npc
    if texture_loader.is_unleashed_npc_body_skin_type(skin_name):
        return ["adult"]

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
    """Return the name of the skeleton that the skill type uses."""
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


def find_or_import_skeleton(
    context: bpy.types.Context,
    file_list: list[pathlib.Path],
    skeleton_names: list[str],
) -> bpy.types.Object | None:
    """Find a skeleton from the list of names, or import it if it doesn't exist."""
    if context.active_object is not None:
        for skeleton_name in skeleton_names:
            if context.active_object.type == 'ARMATURE' and context.active_object.name.startswith(skeleton_name):
                return context.active_object

    skeleton_file_name_map = {
        "adult": "adult-skeleton.cmx.bcf",
        "child": "child-skeleton.cmx.bcf",
        "kat": "kat_skeleton.cmx.bcf",
        "dog": "dog_skeleton.cmx.bcf",
        "effects1": "effects1-skeleton.cmx.bcf",
    }
    skeleton_file_name = skeleton_file_name_map.get(skeleton_names[0])

    armature_object = context.scene.objects.get(skeleton_names[0])
    if armature_object is None or armature_object.type != 'ARMATURE':
        for file_path in file_list:
            if file_path.name == skeleton_file_name:
                bcf_file = bcf.read_file(file_path)
                return import_skeleton.import_skeleton(context, bcf_file.skeletons[0])

    return armature_object


def import_suit(
    context: bpy.types.Context,
    logger: logging.Logger,
    bcf_directory: pathlib.Path,
    file_list: list[pathlib.Path],
    texture_file_list: list[pathlib.Path],
    suit: bcf.Suit,
    preferred_skin_color: str,
    armature_object_map: dict[str, list[str]],
    *,
    find_skeleton: bool,
    fix_textures: bool,
) -> None:
    """Create the meshes for the described suit."""
    for skin in suit.skins:
        armature_object = None
        if find_skeleton:
            skeleton_names = get_skin_type_skeleton_names(skin.skin_name)
            armature_object = find_or_import_skeleton(context, file_list, skeleton_names)

            if armature_object is None:
                logger.info(f"Could not find or import {skeleton_names[0]} skeleton used by {suit.name}.")  # noqa: G004
                continue

        elif context.active_object:
            armature_object = context.active_object

        if armature_object is None or armature_object.type != 'ARMATURE':
            logger.info("Please select an armature to apply the imported mesh to.")
            break

        try:
            bmf_file_path = bcf_directory / (skin.skin_name + ".bmf")
            if bmf_file_path.is_file():
                bmf_file = bmf.read_file(bmf_file_path)
            else:
                skn_file_path = bcf_directory / (skin.skin_name + ".skn")
                bmf_file = skn.read_file(skn_file_path)
        except TS1FileReadError as _:
            logger.info(f"Could not load mesh {skin.skin_name} used by {suit.name}.")  # noqa: G004
            continue

        obj = import_mesh.import_mesh(logger, skin.skin_name, armature_object, bmf_file.mesh)
        if obj is None:
            continue

        mesh_collection = bpy.data.collections.get(suit.name)
        if mesh_collection is None:
            mesh_collection = bpy.data.collections.new(suit.name)
            mesh_collection["Suit Type"] = suit.suit_type
        mesh_collection.objects.link(obj)
        if mesh_collection.name not in context.scene.collection.children:
            context.scene.collection.children.link(mesh_collection)

        obj["Bone Name"] = skin.bone_name
        obj["Censor Flags"] = skin.censor_flags

        texture_loader.load_textures(
            obj,
            texture_file_list,
            skin.skin_name,
            bmf_file.default_texture_name,
            preferred_skin_color,
            fix_textures=fix_textures,
        )

        if not obj.data.materials:
            logger.info(f"Could not find a texture for mesh {skin.skin_name}")  # noqa: G004

        if armature_object_map.get(armature_object) is None:
            armature_object_map[armature_object] = []

        armature_object_map[armature_object] += [obj]


def create_fcurve_data(
    action: bpy.types.Action,
    channelbag,  #  noqa: ANN001
    data_path: str,
    index: int,
    count: int,
    data: list[float],
) -> None:
    """Create the fcurve data for all frames at once."""
    if bpy.app.version[0] >= 5:
        f_curve = channelbag.fcurves.new(data_path, index=index)
    else:
        f_curve = action.fcurves.new(data_path, index=index)
    f_curve.keyframe_points.add(count=count)
    f_curve.keyframe_points.foreach_set("co", data)
    f_curve.update()


MAX_TIMELINE_MARKER_NAME_LENGTH = 63  # 64 - null


def import_skill(
    context: bpy.types.Context,
    logger: logging.Logger,
    file_directory: pathlib.Path,
    file_list: list[pathlib.Path],
    skill: bcf.Skill,
) -> None:
    """Create the actions and nla track for the described skill."""
    cfp_file_path = file_directory / (skill.animation_name + ".cfp")
    if not cfp_file_path.is_file():
        matches = [file_path for file_path in file_list if file_path.stem.lower() == cfp_file_path.stem.lower()]
        if len(matches) > 0:
            cfp_file_path = matches[0]
    try:
        cfp_file = cfp.read_file(cfp_file_path, skill.position_count, skill.rotation_count)
    except TS1FileReadError as _:
        logger.info(f"Could not load cfp file {cfp_file_path}")  # noqa: G004
        return

    skeleton_name = get_skill_type_skeleton_name(skill.skill_name)
    armature = find_or_import_skeleton(context, file_list, skeleton_name)
    if armature is None:
        logger.info(f"Could not find or import {skeleton_name} skeleton used by {skill.skill_name}")  # noqa: G004
        return

    armature_object = bpy.data.objects[armature.name]

    if skill.skill_name in bpy.data.actions:
        return

    anim_data = armature_object.animation_data_create()

    action = bpy.data.actions.new(name=skill.skill_name)
    anim_data.action = action
    channelbag = None
    if bpy.app.version[0] >= 5:
        anim_data.action_slot = action.slots.new(id_type='OBJECT', name="slot")
        channelbag = bpy_extras.anim_utils.action_ensure_channelbag_for_slot(anim_data.action, anim_data.action_slot)

    action.frame_range = (1.0, skill.motions[0].frame_count)

    action["Distance"] = skill.distance

    ignored_bone_count = 0

    for motion in skill.motions:
        bone = armature_object.pose.bones.get(motion.bone_name)
        if bone is None:
            ignored_bone_count += 1
            continue

        parent_bone_matrix = mathutils.Matrix()
        if bone.parent:
            parent_bone_matrix = bone.parent.bone.matrix_local @ utils.BONE_ROTATION_OFFSET_INVERTED

        positions_x: list[float] = []
        positions_y: list[float] = []
        positions_z: list[float] = []
        rotations_w: list[float] = []
        rotations_x: list[float] = []
        rotations_y: list[float] = []
        rotations_z: list[float] = []

        for frame in range(motion.frame_count):
            translation = mathutils.Matrix()
            if motion.positions_used_flag:
                translation = mathutils.Matrix.Translation(
                    mathutils.Vector(
                        (
                            cfp_file.positions_x[motion.position_offset + frame] / utils.BONE_SCALE,
                            cfp_file.positions_z[motion.position_offset + frame] / utils.BONE_SCALE,  # swap y and z
                            cfp_file.positions_y[motion.position_offset + frame] / utils.BONE_SCALE,
                        ),
                    ),
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
                        ),
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
            create_fcurve_data(action, channelbag, data_path, 0, motion.frame_count, positions_x)
            create_fcurve_data(action, channelbag, data_path, 1, motion.frame_count, positions_y)
            create_fcurve_data(action, channelbag, data_path, 2, motion.frame_count, positions_z)

        if motion.rotations_used_flag:
            data_path = bone.path_from_id("rotation_quaternion")
            create_fcurve_data(action, channelbag, data_path, 0, motion.frame_count, rotations_w)
            create_fcurve_data(action, channelbag, data_path, 1, motion.frame_count, rotations_x)
            create_fcurve_data(action, channelbag, data_path, 2, motion.frame_count, rotations_y)
            create_fcurve_data(action, channelbag, data_path, 3, motion.frame_count, rotations_z)

    # create a single default keyframe for any locations or rotations not used by the animation
    for bone in armature_object.pose.bones:
        location_data_path = bone.path_from_id("location")
        rotation_data_path = bone.path_from_id("rotation_quaternion")

        if bpy.app.version[0] >= 5:
            location_fcurve = channelbag.fcurves.find(location_data_path)
            rotation_fcurve = channelbag.fcurves.find(rotation_data_path)
        else:
            location_fcurve = action.fcurves.find(location_data_path)
            rotation_fcurve = action.fcurves.find(rotation_data_path)

        if not location_fcurve:
            create_fcurve_data(action, channelbag, location_data_path, 0, 1, (1.0, 0.0))
            create_fcurve_data(action, channelbag, location_data_path, 1, 1, (1.0, 0.0))
            create_fcurve_data(action, channelbag, location_data_path, 2, 1, (1.0, 0.0))
        if not rotation_fcurve:
            create_fcurve_data(action, channelbag, rotation_data_path, 0, 1, (1.0, 1.0))
            create_fcurve_data(action, channelbag, rotation_data_path, 1, 1, (1.0, 0.0))
            create_fcurve_data(action, channelbag, rotation_data_path, 2, 1, (1.0, 0.0))
            create_fcurve_data(action, channelbag, rotation_data_path, 3, 1, (1.0, 0.0))

    if ignored_bone_count > 0:
        logger.info(f"Skipped {ignored_bone_count} unknown bones in {skill.skill_name}.")  # noqa: G004

    for motion in skill.motions:
        for time_property_list in motion.time_property_lists:
            for time_property in time_property_list.time_properties:
                for event in time_property.events:
                    event_string = f"{motion.bone_name} {event.name} {event.value}"
                    frame = round(time_property.time / 33.3333333) + 1

                    markers = [x for x in action.pose_markers if x.frame == frame]

                    if len(markers) == 0:
                        marker = action.pose_markers.new(name=event_string)
                        marker.frame = frame
                    else:
                        last_marker = action.pose_markers[-1]
                        if len(last_marker.name) + 1 + len(event_string) <= MAX_TIMELINE_MARKER_NAME_LENGTH:
                            last_marker.name = f"{last_marker.name};{event_string}"
                        else:
                            marker = action.pose_markers.new(name=event_string)
                            marker.frame = frame

    track = anim_data.nla_tracks.new(prev=None)
    track.name = skill.animation_name
    track.strips.new(skill.skill_name, 1, action)
    track.mute = True

    context.scene.render.fps = 33
    context.scene.frame_end = max(context.scene.frame_end, skill.motions[0].frame_count)


def import_files(
    context: bpy.types.Context,
    logger: logging.Logger,
    file_paths: list[pathlib.Path],
    preferred_skin_color: str,
    *,
    import_skeletons: bool,
    import_meshes: bool,
    import_animations: bool,
    find_skeleton: bool,
    cleanup_meshes: bool,
    fix_textures: bool,
) -> None:
    """Import all the skeletons, meshes and animations in the selected files."""
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

    file_search_directory = pathlib.Path(context.preferences.addons["io_scene_ts1"].preferences.file_search_directory)
    if file_search_directory == "":
        file_search_directory = file_paths[0].parent
    file_list = list(file_search_directory.rglob("*"))

    if not file_paths[0].parent.is_relative_to(file_search_directory):
        file_list.extend(file_paths[0].parent.glob("*"))

    bcf_file_list = [path for path in file_list if path.suffix.lower() == ".bcf" or path.suffix.lower() == ".cmx"]

    if import_skeletons:
        for _, bcf_file in bcf_files:
            for skeleton in bcf_file.skeletons:
                import_skeleton.import_skeleton(context, skeleton)

    if import_meshes:
        mesh_file_list = bcf_file_list + [
            path for path in file_list if path.suffix.lower() == ".bmf" or path.suffix.lower() == ".skn"
        ]
        texture_file_list = [
            path for path in file_list if path.suffix.lower() == ".bmp" or path.suffix.lower() == ".tga"
        ]

        armature_object_map: dict[str, list[str]] = {}
        for bcf_file_path, bcf_file in bcf_files:
            for suit in bcf_file.suits:
                import_suit(
                    context,
                    logger,
                    bcf_file_path.parent,
                    mesh_file_list,
                    texture_file_list,
                    suit,
                    preferred_skin_color,
                    armature_object_map,
                    find_skeleton=find_skeleton,
                    fix_textures=fix_textures,
                )

        previous_active_object = context.view_layer.objects.active

        for armature_object, objects in armature_object_map.items():
            import_mesh.parent_and_clean_up_meshes(context, armature_object, objects, cleanup_meshes=cleanup_meshes)

        bpy.ops.object.select_all(action='DESELECT')

        context.view_layer.objects.active = previous_active_object

    if import_animations:
        animation_file_list = bcf_file_list + [path for path in file_list if path.suffix.lower() == ".cfp"]

        for bcf_file_path, bcf_file in bcf_files:
            for skill in bcf_file.skills:
                import_skill(context, logger, bcf_file_path.parent, animation_file_list, skill)
