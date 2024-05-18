bl_info = {
    "name": "The Sims 1 3D Formats",
    "description": "Imports and exports The Sims 1 meshes and animations.",
    "author": "mix",
    "version": (0, 0, 0),
    "blender": (4, 1, 0),
    "location": "File > Import-Export",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Import-Export",
}

import bpy
import bpy_extras
import copy
import math
import mathutils
import os
import struct


BONE_SCALE = 3.0
BONE_ROTATION_OFFSET = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'Z')


def cmx_bcf_struct():
    import construct

    prop = construct.Struct(
        "name" / construct.PascalString(construct.Int8ul, "ascii"),
        "value" / construct.PascalString(construct.Int8ul, "ascii"),
    )

    properties = construct.Struct(
        "count" / construct.Int32ul,
        "properties" / construct.Array(construct.this.count, prop),
    )

    time_property_event = construct.Struct(
        "name" / construct.PascalString(construct.Int8ul, "ascii"),
        "value" / construct.PascalString(construct.Int8ul, "ascii"),
    )

    time_property = construct.Struct(
        "time" / construct.Int32ul,
        "event_count" / construct.Int32ul,
        "events" / construct.Array(construct.this.event_count, time_property_event),
    )

    time_properties = construct.Struct(
        "count" / construct.Int32ul,
        "properties" / construct.Array(construct.this.count, time_property),
    )

    motion = construct.Struct(
        "bone_name" / construct.PascalString(construct.Int8ul, "ascii"),
        "frame_count" / construct.Int32ul,
        "duration" / construct.Float32l,
        "positions_used_flag" / construct.Int32ul,
        "rotations_used_flag" / construct.Int32ul,
        "position_offset" / construct.Int32ul,
        "rotation_offset" / construct.Int32ul,
        "property_count" / construct.Int32ul,
        "properties" / construct.Array(construct.this.property_count, properties),
        "time_property_count" / construct.Int32ul,
        "time_properties" / construct.Array(construct.this.time_property_count, time_properties),
    )

    skill = construct.Struct(
        "skill_name" / construct.PascalString(construct.Int8ul, "ascii"),
        "animation_name" / construct.PascalString(construct.Int8ul, "ascii"),
        "duration" / construct.Float32l,
        "distance" / construct.Int32ul,
        "moving_flag" / construct.Int32ul,
        "position_count" / construct.Int32ul,
        "rotation_count" / construct.Int32ul,
        "motion_count" / construct.Int32ul,
        "motions" / construct.Array(construct.this.motion_count, motion),
    )

    skin = construct.Struct(
        "bone_name" / construct.PascalString(construct.Int8ul, "ascii"),
        "skin_name" / construct.PascalString(construct.Int8ul, "ascii"),
        "censor_flags" / construct.Int32ul,
        "unknown" / construct.Int32ul,
    )

    suit = construct.Struct(
        "name" / construct.PascalString(construct.Int8ul, "ascii"),
        "type" / construct.Int32ul,
        "unknown" / construct.Int32ul,
        "skin_count" / construct.Int32ul,
        "skins" / construct.Array(construct.this.skin_count, skin),
    )

    bone = construct.Struct(
        "name" / construct.PascalString(construct.Int8ul, "ascii"),
        "parent" / construct.PascalString(construct.Int8ul, "ascii"),
        "property_count" / construct.Int32ul,
        "properties" / construct.Array(construct.this.property_count, properties),
        "position_x" / construct.Float32l,
        "position_y" / construct.Float32l,
        "position_z" / construct.Float32l,
        "rotation_x" / construct.Float32l,
        "rotation_y" / construct.Float32l,
        "rotation_z" / construct.Float32l,
        "rotation_w" / construct.Float32l,
        "translate" / construct.Int32ul,
        "rotate" / construct.Int32ul,
        "blend_suits" / construct.Int32ul,
        "wiggle_value" / construct.Float32l,
        "wiggle_power" / construct.Float32l,
    )

    skeleton = construct.Struct(
        "name" / construct.PascalString(construct.Int8ul, "ascii"),
        "bone_count" / construct.Int32ul,
        "bones" / construct.Array(construct.this.bone_count, bone),
    )

    cmx_bcf_struct = construct.Struct(
        "skeleton_count" / construct.Int32ul,
        "skeletons" / construct.Array(construct.this.skeleton_count, skeleton),
        "suit_count" / construct.Int32ul,
        "suits" / construct.Array(construct.this.suit_count, suit),
        "skill_count" / construct.Int32ul,
        "skills" / construct.Array(construct.this.skill_count, skill),
    )

    return cmx_bcf_struct


def decode_cfp_values(file, count):
    values = list()

    previous_value = 0.0

    while len(values) < count:
        compression_type = struct.unpack('<B', file.read(1))[0]

        if compression_type == 0xFF: # full 4 byte float
            values.append(struct.unpack('<f', file.read(4))[0])
        elif compression_type == 0xFE: # repeat previous
            repeat_count = struct.unpack('<H', file.read(2))[0]
            for i in range(repeat_count + 1):
                values.append(previous_value)
        else: # delta
            values.append(previous_value + 3.9676e-10 * math.pow(float(compression_type) - 126.0, 3) * abs(float(compression_type) - 126.0))

        previous_value = values[-1]

    return values


def load_cfp(file_path, position_count, rotation_count):
    values = {}

    file = open(file_path, mode='rb')

    values["positions_x"] = decode_cfp_values(file, position_count)
    values["positions_y"] = decode_cfp_values(file, position_count)
    values["positions_z"] = decode_cfp_values(file, position_count)

    values["rotations_x"] = decode_cfp_values(file, rotation_count)
    values["rotations_y"] = decode_cfp_values(file, rotation_count)
    values["rotations_z"] = decode_cfp_values(file, rotation_count)
    values["rotations_w"] = decode_cfp_values(file, rotation_count)

    try:
        file.read(1)
        raise Exception("data left unread at end of cfp file")
    except:
        pass

    return values


def import_files(context, file_paths):
    bcf_files = []
    for file_path in file_paths:
        file = open(file_path, mode='rb')
        bcf_files.append(cmx_bcf_struct().parse(file.read()))

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
                    parent_matrix = armature.edit_bones[bone.parent].matrix @ BONE_ROTATION_OFFSET.inverted()

                armature_bone.head = mathutils.Vector((0.0, 0.0, 0.0))
                armature_bone.tail = mathutils.Vector((0.1, 0.0, 0.0))

                rotation = mathutils.Quaternion(
                    (bone.rotation_w, bone.rotation_x, bone.rotation_z, bone.rotation_y)
                ).to_matrix().to_4x4()

                translation = mathutils.Matrix.Translation(mathutils.Vector(
                    (bone.position_x, bone.position_z, bone.position_y)
                ) / BONE_SCALE)

                armature_bone.matrix = (parent_matrix @ (translation @ rotation)) @ BONE_ROTATION_OFFSET

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

    for bcf_file in bcf_files:
        for skill in bcf_file.skills:
            cfp_file_path = os.path.join(os.path.dirname(file_path), skill.animation_name + ".cfp")
            cfp_file = load_cfp(cfp_file_path, skill.position_count, skill.rotation_count)

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
                            cfp_file["positions_x"][motion.position_offset + frame] / BONE_SCALE,
                            cfp_file["positions_z"][motion.position_offset + frame] / BONE_SCALE,
                            cfp_file["positions_y"][motion.position_offset + frame] / BONE_SCALE,
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
                        parent_matrix = bone.parent.matrix @ BONE_ROTATION_OFFSET.inverted()

                    bone.matrix = (parent_matrix @ (translation @ rotation)) @ BONE_ROTATION_OFFSET

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


class ImportTS1(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "import.bcf"
    bl_label = "Import The Sims 1 meshes and animations"
    bl_description = ""
    bl_options = {'UNDO'}

    filename_ext = ".cmx.bcf"

    filter_glob: bpy.props.StringProperty(
        default="*.cmx.bcf",
        options={'HIDDEN'},
    )
    files: bpy.props.CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )
    directory: bpy.props.StringProperty(
        subtype='DIR_PATH',
    )

    def execute(self, context):
        import os

        paths = [os.path.join(self.directory, name.name) for name in self.files]

        if not paths:
            paths.append(self.filepath)

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action='DESELECT')

        try:
            import_files(context, paths)
        except Exception as exception:
             self.report({"ERROR"}, exception.args[0])

        return {'FINISHED'}

    def draw(self, context):
        pass


def write_cfp_entries(file, entries):
    for entry in entries:
        file.write(bytes([0xFF]))
        file.write(struct.pack('<f', entry))


def write_cfp_file(file_path, positions_x, positions_y, positions_z, rotations_x, rotations_y, rotations_z, rotations_w):
    file = open(file_path, "wb")
    write_cfp_entries(file, positions_x)
    write_cfp_entries(file, positions_y)
    write_cfp_entries(file, positions_z)
    write_cfp_entries(file, rotations_x)
    write_cfp_entries(file, rotations_y)
    write_cfp_entries(file, rotations_z)
    write_cfp_entries(file, rotations_w)


def export_files(context, file_path):
    animation_file = {}

    animation_file["skeletons"] = list()
    animation_file["suits"] = list()
    animation_file["skills"] = list()

    for armature in bpy.data.armatures:
        armature_object = bpy.data.objects[armature.name]

        for track in armature_object.animation_data.nla_tracks:
            for strip in track.strips:
                armature_object.animation_data.action = strip.action

                positions_x = list()
                positions_y = list()
                positions_z = list()

                rotations_x = list()
                rotations_y = list()
                rotations_z = list()
                rotations_w = list()

                skill = {}
                skill["skill_name"] = strip.action.name
                skill["animation_name"] = track.name
                skill["duration"] = math.floor((strip.action.frame_end - 1) * 33.3333333)
                skill["distance"] = strip.action["distance"]
                skill["moving_flag"] = 1 if strip.action["distance"] != 0.0 else 0
                skill["motions"] = list()

                for bone in armature_object.pose.bones:
                    motion = {}
                    motion["bone_name"] = bone.name
                    motion["frame_count"] = int(strip.action.frame_end - strip.action.frame_start) + 1
                    motion["duration"] = skill["duration"]
                    motion["positions_used_flag"] = 0
                    motion["rotations_used_flag"] = 0
                    motion["property_count"] = 0
                    motion["properties"] = list()
                    motion["time_properties"] = list()

                    for frame in range(int(strip.action.frame_start), int(strip.action.frame_end) + 1):
                        for fcu in strip.action.fcurves:
                            if fcu.data_path == bone.path_from_id("location"):
                                if frame in (p.co.x for p in fcu.keyframe_points):
                                    motion["positions_used_flag"] = 1
                            if fcu.data_path == bone.path_from_id("rotation_quaternion"):
                                if frame in (p.co.x for p in fcu.keyframe_points):
                                    motion["rotations_used_flag"] = 1

                    if not motion["positions_used_flag"] and not motion["rotations_used_flag"]:
                        continue

                    original_current_frame = bpy.context.scene.frame_current

                    for frame in range(int(strip.action.frame_start), int(strip.action.frame_end) + 1):
                        bpy.context.scene.frame_set(frame)

                        if motion["positions_used_flag"]:
                            position = copy.copy(bone.head)
                            if bone.parent is not None:
                                position = bone.parent.matrix.inverted() @ bone.head
                                position = BONE_ROTATION_OFFSET @ position
                            position *= BONE_SCALE
                            positions_x.append(position.x)
                            positions_y.append(position.z) # swap y and z
                            positions_z.append(position.y)
                        if motion["rotations_used_flag"]:
                            rotation = bone.matrix @ BONE_ROTATION_OFFSET.inverted()
                            if bone.parent is not None:
                                rotation = (bone.parent.matrix @ BONE_ROTATION_OFFSET.inverted()).inverted() @ rotation
                            rotation = rotation.to_quaternion()
                            rotations_x.append(rotation.x)
                            rotations_y.append(rotation.z) # swap y and z
                            rotations_z.append(rotation.y)
                            rotations_w.append(rotation.w)

                    bpy.context.scene.frame_set(original_current_frame)

                    time_properties = {}
                    time_properties["properties"] = list()

                    for marker in strip.action.pose_markers:
                        marker_components = marker.name.split()
                        if marker_components[0] == bone.name:
                            event = {}
                            event["name"] = marker_components[1]
                            event["value"] = marker_components[2]

                            time_property = {}
                            time_property["time"] = int(round((marker.frame - int(strip.action.frame_start)) * 33.33333))
                            time_property["event_count"] = 1
                            time_property["events"] = [event]

                            time_properties["properties"].append(time_property)

                    if len(time_properties["properties"]) > 0:
                        time_properties["count"] = len(time_properties["properties"])
                        motion["time_properties"].append(time_properties)

                    motion["time_property_count"] = len(motion["time_properties"])

                    motion["position_offset"] = 4294967295
                    motion["rotation_offset"] = 4294967295

                    skill["motions"].append(motion)

                position_offset = 0
                rotation_offset = 0
                for motion in skill["motions"]:
                    if motion["positions_used_flag"]:
                        motion["position_offset"] = position_offset
                        position_offset += motion["frame_count"]
                    if motion["rotations_used_flag"]:
                        motion["rotation_offset"] = rotation_offset
                        rotation_offset += motion["frame_count"]

                skill["position_count"] = len(positions_x)
                skill["rotation_count"] = len(rotations_x)

                skill["motion_count"] = len(skill["motions"])
                animation_file["skills"].append(skill)

                cfp_file_path = os.path.join(os.path.dirname(file_path), track.name + ".cfp")
                write_cfp_file(
                    cfp_file_path,
                    positions_x,
                    positions_y,
                    positions_z,
                    rotations_x,
                    rotations_y,
                    rotations_z,
                    rotations_w
                )

    animation_file["skeleton_count"] = len(animation_file["skeletons"])
    animation_file["suit_count"] = len(animation_file["suits"])
    animation_file["skill_count"] = len(animation_file["skills"])

    file = open(file_path + ".bcf", "wb")
    file.write(cmx_bcf_struct().build(animation_file))


class ExportTS1(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "export.cmx"
    bl_label = "Export The Sims 1 meshes and animations"
    bl_description = ""

    filename_ext = ".cmx"

    filter_glob: bpy.props.StringProperty(
        default="*.cmx.bcf",
        options={'HIDDEN'},
    )

    def execute(self, context):
        try:
            export_files(context, self.properties.filepath)
        except Exception as exception:
             self.report({"ERROR"}, exception.args[0])

        return {'FINISHED'}

    def draw(self, context):
        pass


def menu_import(self, context):
    self.layout.operator(ImportTS1.bl_idname, text="The Sims 1 (.cmx.bcf)")


def menu_export(self, context):
    self.layout.operator(ExportTS1.bl_idname, text="The Sims 1 (.cmx.bcf)")


classes = (
    ImportTS1,
    ExportTS1,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_export)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(menu_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_export)


if __name__ == "__main__":
    register()
