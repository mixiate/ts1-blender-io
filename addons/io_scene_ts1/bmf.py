import dataclasses
import struct

from . import utils


def read_bones(file):
    count = struct.unpack('<I', file.read(4))[0]
    bones = []
    for i in range(count):
        bones.append(utils.read_string(file))
    return bones


def write_bones(file, bones):
    file.write(struct.pack('<I', len(bones)))
    for bone in bones:
        utils.write_string(file, bone)


def read_faces(file):
    count = struct.unpack('<I', file.read(4))[0]
    faces = []
    for i in range(count):
        faces.append(struct.unpack('<3I', file.read(4 * 3)))
    return faces


def write_faces(file, faces):
    file.write(struct.pack('<I', len(faces)))
    for face in faces:
        file.write(struct.pack('<3I', *face))


@dataclasses.dataclass
class BoneBinding:
    bone_index: int
    vertex_index: int
    vertex_count: int
    blended_vertex_index: int
    blended_vertex_count: int


def read_bone_bindings(file):
    count = struct.unpack('<I', file.read(4))[0]
    bone_bindings = []
    for i in range(count):
        bone_bindings.append(
            BoneBinding(
                struct.unpack('<I', file.read(4))[0],
                struct.unpack('<I', file.read(4))[0],
                struct.unpack('<I', file.read(4))[0],
                struct.unpack('<i', file.read(4))[0],
                struct.unpack('<I', file.read(4))[0],
            )
        )
    return bone_bindings


def write_bone_bindings(file, bone_bindings):
    file.write(struct.pack('<I', len(bone_bindings)))
    for bone_binding in bone_bindings:
        file.write(struct.pack('<I', bone_binding.bone_index))
        file.write(struct.pack('<I', bone_binding.vertex_index))
        file.write(struct.pack('<I', bone_binding.vertex_count))
        file.write(struct.pack('<i', bone_binding.blended_vertex_index))
        file.write(struct.pack('<I', bone_binding.blended_vertex_count))


def read_uvs(file):
    count = struct.unpack('<I', file.read(4))[0]
    uvs = []
    for i in range(count):
        uvs.append(struct.unpack('<2f', file.read(4 * 2)))
    return uvs


def write_uvs(file, uvs):
    file.write(struct.pack('<I', len(uvs)))
    for uv in uvs:
        file.write(struct.pack('<2f', *uv))


@dataclasses.dataclass
class Blend:
    weight: int
    vertex_index: int


def read_blends(file):
    count = struct.unpack('<I', file.read(4))[0]
    blends = []
    for i in range(count):
        blends.append(
            Blend(
                struct.unpack('<I', file.read(4))[0],
                struct.unpack('<I', file.read(4))[0],
            )
        )
    return blends


def write_blends(file, blends):
    file.write(struct.pack('<I', len(blends)))
    for blend in blends:
        file.write(struct.pack('<I', blend.weight))
        file.write(struct.pack('<I', blend.vertex_index))


@dataclasses.dataclass
class Vertex:
    position: (float, float, float)
    normal: (float, float, float)


def read_vertices(file):
    count = struct.unpack('<I', file.read(4))[0]
    vertices = []
    for i in range(count):
        vertices.append(
            Vertex(
                struct.unpack('<3f', file.read(4 * 3)),
                struct.unpack('<3f', file.read(4 * 3)),
            )
        )
    return vertices


def write_vertices(file, vertices):
    file.write(struct.pack('<I', len(vertices)))
    for vertex in vertices:
        file.write(struct.pack('<3f', *vertex.position))
        file.write(struct.pack('<3f', *vertex.normal))


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
    return Bmf(
        utils.read_string(file),
        utils.read_string(file),
        read_bones(file),
        read_faces(file),
        read_bone_bindings(file),
        read_uvs(file),
        read_blends(file),
        read_vertices(file),
    )


def write_bmf(file, bmf):
    utils.write_string(file, bmf.skin_name)
    utils.write_string(file, bmf.default_texture_name)
    write_bones(file, bmf.bones)
    write_faces(file, bmf.faces)
    write_bone_bindings(file, bmf.bone_bindings)
    write_uvs(file, bmf.uvs)
    write_blends(file, bmf.blends)
    write_vertices(file, bmf.vertices)


def read_file(file_path):
    with file_path.open(mode='rb') as file:
        bmf = read_bmf(file)

        try:
            file.read(1)
            raise Exception("data left unread at end of " + file_path)
        except Exception as _:
            pass

        return bmf


def write_file(file_path, bmf):
    with file_path.open('wb') as file:
        write_bmf(file, bmf)
