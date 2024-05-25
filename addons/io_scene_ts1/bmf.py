import dataclasses
import struct


def read_string(file):
    length = struct.unpack('<B', file.read(1))[0]
    return struct.unpack("%ds" % length, file.read(length))[0].decode("windows-1252")


def read_bones(file):
    count = struct.unpack('<I', file.read(4))[0]
    bones = list()
    for i in range(count):
        bones.append(read_string(file))
    return bones


def read_faces(file):
    count = struct.unpack('<I', file.read(4))[0]
    faces = list()
    for i in range(count):
        faces.append(struct.unpack('<3I', file.read(4 * 3)))
    return faces


@dataclasses.dataclass
class BoneBinding:
    bone_index: int
    vertex_index: int
    vertex_count: int
    blended_vertex_index: int
    blended_vertex_count: int


def read_bone_bindings(file):
    count = struct.unpack('<I', file.read(4))[0]
    bone_bindings = list()
    for i in range(count):
        bone_bindings.append(
            BoneBinding(
                struct.unpack('<I', file.read(4))[0],
                struct.unpack('<I', file.read(4))[0],
                struct.unpack('<I', file.read(4))[0],
                struct.unpack('<I', file.read(4))[0],
                struct.unpack('<I', file.read(4))[0],
            )
        )
    return bone_bindings


def read_uvs(file):
    count = struct.unpack('<I', file.read(4))[0]
    uvs = list()
    for i in range(count):
        uvs.append(struct.unpack('<2f', file.read(4 * 2)))
    return uvs


@dataclasses.dataclass
class Blend:
    weight: int
    vertex_index: int


def read_blends(file):
    count = struct.unpack('<I', file.read(4))[0]
    blends = list()
    for i in range(count):
        blends.append(
            Blend(
                struct.unpack('<I', file.read(4))[0],
                struct.unpack('<I', file.read(4))[0],
            )
        )
    return blends


@dataclasses.dataclass
class Vertex:
    position: (float, float, float)
    normal: (float, float, float)


def read_vertices(file):
    count = struct.unpack('<I', file.read(4))[0]
    vertices = list()
    for i in range(count):
        vertices.append(
            Vertex(
                struct.unpack('<3f', file.read(4 * 3)),
                struct.unpack('<3f', file.read(4 * 3)),
            )
        )
    return vertices


@dataclasses.dataclass
class Bmf:
    skin_name: str
    default_texture_name: str
    bones: list[str]
    faces: list[(int, int, int)]
    bone_bindings: list[BoneBinding]
    uvs: list[(float, float)]
    blends: list[Blend]
    vertices: list[Vertex]


def read_bmf(file):
    skin_name = read_string(file)
    default_texture_name = read_string(file)
    bones = read_bones(file)
    faces = read_faces(file)
    bone_bindings = read_bone_bindings(file)
    uvs = read_uvs(file)
    blends = read_blends(file)
    vertices = read_vertices(file)

    return Bmf(
        skin_name,
        default_texture_name,
        bones,
        faces,
        bone_bindings,
        uvs,
        blends,
        vertices,
    )


def read_file(file_path):
    file = open(file_path, mode='rb')

    bmf = read_bmf(file)

    try:
        file.read(1)
        raise Exception("data left unread at end of " + file_path)
    except:
        pass

    file.close()

    return bmf
