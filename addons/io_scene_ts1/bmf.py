import struct


def read_string(file):
    length = struct.unpack('<B', file.read(1))[0]
    return struct.unpack("%ds" % length, file.read(length))[0].decode("windows-1252")


def read_bones(file, count):
    bones = list()
    for i in range(count):
        bones.append(read_string(file))
    return bones


def read_faces(file, count):
    faces = list()
    for i in range(count):
        faces.append(struct.unpack('<3I', file.read(4 * 3)))
    return faces


class BoneBinding(object):
    pass


def read_bone_bindings(file, count):
    bone_bindings = list()
    for i in range(count):
        bone_binding = BoneBinding()
        bone_binding.bone_index = struct.unpack('<I', file.read(4))[0]
        bone_binding.vertex_index = struct.unpack('<I', file.read(4))[0]
        bone_binding.vertex_count = struct.unpack('<I', file.read(4))[0]
        bone_binding.blended_vertex_index = struct.unpack('<I', file.read(4))[0]
        bone_binding.blended_vertex_count = struct.unpack('<I', file.read(4))[0]
        bone_bindings.append(bone_binding)
    return bone_bindings


def read_uvs(file, count):
    uvs = list()
    for i in range(count):
        uvs.append(struct.unpack('<2f', file.read(4 * 2)))
    return uvs


class Blend(object):
    pass


def read_blends(file, count):
    blends = list()
    for i in range(count):
        blend = Blend()
        blend.weight = struct.unpack('<I', file.read(4))[0]
        blend.vertex_index = struct.unpack('<I', file.read(4))[0]
        blends.append(blend)
    return blends


class Vertex(object):
    pass


def read_vertices(file, count):
    vertices = list()
    for i in range(count):
        vertex = Vertex()
        vertex.position = struct.unpack('<3f', file.read(4 * 3))
        vertex.normal = struct.unpack('<3f', file.read(4 * 3))
        vertices.append(vertex)
    return vertices


class Bmf(object):
    pass


def read_bmf(file):
    bmf = Bmf()

    bmf.skin_name = read_string(file)
    bmf.default_texture_name = read_string(file)
    bmf.bone_count = struct.unpack('<I', file.read(4))[0]
    bmf.bones = read_bones(file, bmf.bone_count)
    bmf.face_count = struct.unpack('<I', file.read(4))[0]
    bmf.faces = read_faces(file, bmf.face_count)
    bmf.bone_binding_count = struct.unpack('<I', file.read(4))[0]
    bmf.bone_bindings = read_bone_bindings(file, bmf.bone_binding_count)
    bmf.uv_count = struct.unpack('<I', file.read(4))[0]
    bmf.uvs = read_uvs(file, bmf.uv_count)
    bmf.blend_count = struct.unpack('<I', file.read(4))[0]
    bmf.blends = read_blends(file, bmf.blend_count)
    bmf.vertex_count = struct.unpack('<I', file.read(4))[0]
    bmf.vertices = read_vertices(file, bmf.vertex_count)

    return bmf


def read_file(file_path):
    file = open(file_path, mode='rb')

    bmf = read_bmf(file)

    try:
        file.read(1)
        raise Exception("data left unread at end of " + file_path)
    except:
        pass

    return bmf
