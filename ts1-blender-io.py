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
import math
import mathutils

def load_cmx_bcf(context, file_bytes):
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

    cmx_bcf_file = construct.Struct(
        "skeleton_count" / construct.Int32ul,
        "skeletons" / construct.Array(construct.this.skeleton_count, skeleton),
        "suit_count" / construct.Int32ul,
        "suits" / construct.Array(construct.this.suit_count, suit),
        "skill_count" / construct.Int32ul,
        "skills" / construct.Array(construct.this.skill_count, skill),
    )

    animation_file = cmx_bcf_file.parse(file_bytes)

    for skeleton in animation_file.skeletons:
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
                parent_matrix = armature.edit_bones[bone.parent].matrix

            armature_bone.head = mathutils.Vector((0.0, 0.0, 0.0))
            armature_bone.tail = mathutils.Vector((1.0, 0.0, 0.0))

            BONE_SCALE = 3.0

            rotation = mathutils.Quaternion(
                (bone.rotation_w, bone.rotation_x, bone.rotation_z, bone.rotation_y)
            ).to_matrix().to_4x4()

            translation = mathutils.Matrix.Translation(mathutils.Vector(
                (bone.position_x, bone.position_z, bone.position_y)
            ) / BONE_SCALE)

            armature_bone.matrix = parent_matrix @ (translation @ rotation)

            armature_bone["ts1_translate"] = bone.translate
            armature_bone["ts1_rotate"] = bone.rotate
            armature_bone["ts1_blend"] = bone.blend_suits
            armature_bone["ts1_wiggle_value"] = bone.wiggle_value
            armature_bone["ts1_wiggle_power"] = bone.wiggle_power

            for property_list in bone.properties:
                for prop in property_list.properties:
                    armature_bone["ts1_" + prop.name] = prop.value

        parent_bones = set()
        quat_final_rotation = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'Z')
        for bone in skeleton.bones:
            armature_bone = armature.edit_bones[bone.name]
            # this is probably wrong ultimately
            armature_bone.matrix @= quat_final_rotation
            if bone.parent != "NULL":
                parent_bones.add(bone.parent)
                armature.edit_bones[bone.parent].tail = armature_bone.head

        for bone in skeleton.bones:
            if bone.name not in parent_bones:
                armature.edit_bones[bone.name].length = armature.edit_bones[bone.parent].length
            if bone.name == "SPINE":
                armature.edit_bones[bone.parent].tail = armature.edit_bones[bone.name].head

        for bone in skeleton.bones:
            if bone.parent != "NULL" and armature.edit_bones[bone.parent].tail == armature.edit_bones[bone.name].head:
                armature.edit_bones[bone.name].use_connect = True

        bpy.ops.object.mode_set(mode='OBJECT')


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

        for path in paths:
            with open(path, mode='rb') as file:
                file_bytes = file.read()
                load_cmx_bcf(context, file_bytes)

        return {'FINISHED'}

    def draw(self, context):
        pass


def menu_import(self, context):
    self.layout.operator(ImportTS1.bl_idname, text="The Sims 1 (.cmx.bcf)")


classes = (
    ImportTS1,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_import)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(menu_import)


if __name__ == "__main__":
    register()
