import math
import mathutils
import struct

BONE_SCALE = 3.0
BONE_ROTATION_OFFSET = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'Z')


def read_string(file):
    length = struct.unpack('<B', file.read(1))[0]
    return struct.unpack("%ds" % length, file.read(length))[0].decode("windows-1252")


def write_string(file, string):
    file.write(struct.pack('<B', len(string)))
    file.write(string.encode("windows-1252"))
