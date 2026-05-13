"""Utility functions and classes."""

import math

import mathutils

BONE_SCALE = 3.0
BONE_ROTATION_OFFSET = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'Z')
BONE_ROTATION_OFFSET_INVERTED = BONE_ROTATION_OFFSET.inverted()


class ExportError(Exception):
    """General purpose export error."""
