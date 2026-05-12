"""Import The Sims skeleton in to Blender."""

import copy
import math

import bpy
import mathutils

from . import utils
from .ts1_formats.skeleton import Skeleton


def import_skeleton(context: bpy.types.Context, skeleton: Skeleton) -> bpy.types.Object:
    """Create an armature object for the skeleton."""
    armature = bpy.data.armatures.new(name=skeleton.name)
    armature_object = bpy.data.objects.new(name=skeleton.name, object_data=armature)
    context.scene.collection.objects.link(armature_object)

    context.view_layer.objects.active = armature_object
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
            mathutils.Quaternion((bone.rotation[3], bone.rotation[0], bone.rotation[2], bone.rotation[1]))
            .to_matrix()
            .to_4x4()
        )

        translation = mathutils.Matrix.Translation(
            mathutils.Vector((bone.position[0], bone.position[2], bone.position[1])) / utils.BONE_SCALE,
        )

        armature_bone.matrix = (parent_matrix @ (translation @ rotation)) @ utils.BONE_ROTATION_OFFSET

        armature_bone["translate"] = bone.translate
        armature_bone["rotate"] = bone.rotate
        armature_bone["blend"] = bone.blend
        armature_bone["wiggle value"] = bone.wiggle_value
        armature_bone["wiggle power"] = bone.wiggle_power

        for property_list in bone.property_lists:
            for prop in property_list.properties:
                armature_bone[prop.name] = prop.value

    for bone in armature.edit_bones:
        if bone.parent:
            previous_parent_tail = copy.copy(bone.parent.tail)
            previous_parent_quat = bone.parent.matrix.to_4x4().to_quaternion()
            bone.parent.tail = bone.head
            quaternion_difference = bone.parent.matrix.to_4x4().to_quaternion().dot(previous_parent_quat)
            if not math.isclose(quaternion_difference, 1.0, rel_tol=1e-06):
                bone.parent.tail = previous_parent_tail
            else:
                bone.use_connect = True

        if len(bone.children) == 0:
            bone.length = bone.parent.length

    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    armature_object.select_set(state=True)

    return armature_object
