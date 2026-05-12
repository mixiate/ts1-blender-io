"""Read and write The Sims 1 BMF files."""

import dataclasses
import pathlib
import struct
import typing

from . import error, pascal_string


def read_bones(file: typing.BinaryIO) -> list[str]:
    """Read BMF bones."""
    count = struct.unpack('<I', file.read(4))[0]
    return [pascal_string.read_string(file) for _ in range(count)]


def write_bones(file: typing.BinaryIO, bones: list[str]) -> None:
    """Write BMF bones."""
    file.write(struct.pack('<I', len(bones)))
    for bone in bones:
        pascal_string.write_string(file, bone)


def read_faces(file: typing.BinaryIO) -> list[tuple[int, int, int]]:
    """Read BMF faces."""
    count = struct.unpack('<I', file.read(4))[0]
    return [struct.unpack('<3I', file.read(4 * 3)) for _ in range(count)]


def write_faces(file: typing.BinaryIO, faces: list[tuple[int, int, int]]) -> None:
    """Write BMF faces."""
    file.write(struct.pack('<I', len(faces)))
    file.writelines(struct.pack('<3I', *face) for face in faces)


@dataclasses.dataclass
class BoneBinding:
    """BMF File Bone Binding."""

    bone_index: int
    vertex_index: int
    vertex_count: int
    blended_vertex_index: int
    blended_vertex_count: int


def read_bone_bindings(file: typing.BinaryIO) -> list[BoneBinding]:
    """Read BMF bone bindings."""
    count = struct.unpack('<I', file.read(4))[0]
    return [
        BoneBinding(
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<i', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
        )
        for _ in range(count)
    ]


def write_bone_bindings(file: typing.BinaryIO, bone_bindings: list[BoneBinding]) -> None:
    """Write BMF bone bindings."""
    file.write(struct.pack('<I', len(bone_bindings)))
    for bone_binding in bone_bindings:
        file.write(struct.pack('<I', bone_binding.bone_index))
        file.write(struct.pack('<I', bone_binding.vertex_index))
        file.write(struct.pack('<I', bone_binding.vertex_count))
        file.write(struct.pack('<i', bone_binding.blended_vertex_index))
        file.write(struct.pack('<I', bone_binding.blended_vertex_count))


def read_uvs(file: typing.BinaryIO) -> list[tuple[float, float]]:
    """Read BMF uvs."""
    count = struct.unpack('<I', file.read(4))[0]
    return [struct.unpack('<2f', file.read(4 * 2)) for _ in range(count)]


def write_uvs(file: typing.BinaryIO, uvs: list[tuple[float, float]]) -> None:
    """Write BMF uvs."""
    file.write(struct.pack('<I', len(uvs)))
    file.writelines(struct.pack('<2f', *uv) for uv in uvs)


@dataclasses.dataclass
class Blend:
    """BMF File Blend."""

    weight: int
    vertex_index: int


def read_blends(file: typing.BinaryIO) -> list[Blend]:
    """Read BMF blends."""
    count = struct.unpack('<I', file.read(4))[0]
    return [
        Blend(
            struct.unpack('<I', file.read(4))[0],
            struct.unpack('<I', file.read(4))[0],
        )
        for _ in range(count)
    ]


def write_blends(file: typing.BinaryIO, blends: list[Blend]) -> None:
    """Write BMF blends."""
    file.write(struct.pack('<I', len(blends)))
    for blend in blends:
        file.write(struct.pack('<I', blend.weight))
        file.write(struct.pack('<I', blend.vertex_index))


@dataclasses.dataclass
class Vertex:
    """BMF File Vertex."""

    position: tuple[float, float, float]
    normal: tuple[float, float, float]


def read_vertex(stream: typing.BinaryIO) -> Vertex:
    """Read a vertex from a stream."""
    return Vertex(
        struct.unpack('<3f', stream.read(4 * 3)),
        struct.unpack('<3f', stream.read(4 * 3)),
    )


def write_vertices(file: typing.BinaryIO, vertices: list[Vertex]) -> None:
    """Write BMF vertices."""
    file.write(struct.pack('<I', len(vertices)))
    for vertex in vertices:
        file.write(struct.pack('<3f', *vertex.position))
        file.write(struct.pack('<3f', *vertex.normal))


@dataclasses.dataclass
class Mesh:
    """Mesh description."""

    bones: list[str]
    faces: list[tuple[int, int, int]]
    bone_bindings: list[BoneBinding]
    uvs: list[tuple[float, float]]
    blends: list[Blend]
    vertices: list[Vertex]
    blend_vertices: list[Vertex]


def read_mesh(stream: typing.BinaryIO) -> Mesh:
    """Read mesh from a stream."""
    bones = read_bones(stream)
    faces = read_faces(stream)
    bone_bindings = read_bone_bindings(stream)
    uvs = read_uvs(stream)
    blends = read_blends(stream)
    struct.unpack('<I', stream.read(4))  # total vertex count
    vertices = [read_vertex(stream) for _ in range(len(uvs))]
    blend_vertices = [read_vertex(stream) for _ in range(len(blends))]

    return Mesh(
        bones,
        faces,
        bone_bindings,
        uvs,
        blends,
        vertices,
        blend_vertices,
    )


def write_mesh(stream: typing.BinaryIO, mesh: Mesh) -> None:
    """Write a mesh to a stream."""
    write_bones(stream, mesh.bones)
    write_faces(stream, mesh.faces)
    write_bone_bindings(stream, mesh.bone_bindings)
    write_uvs(stream, mesh.uvs)
    write_blends(stream, mesh.blends)
    write_vertices(stream, mesh.vertices + mesh.blend_vertices)


@dataclasses.dataclass
class Bmf:
    """BMF File."""

    skin_name: str
    default_texture_name: str
    mesh: Mesh


def read_bmf(file: typing.BinaryIO) -> Bmf:
    """Read BMF."""
    return Bmf(
        pascal_string.read_string(file),
        pascal_string.read_string(file),
        read_mesh(file),
    )


def write_bmf(file: typing.BinaryIO, bmf: Bmf) -> None:
    """Write BMF."""
    pascal_string.write_string(file, bmf.skin_name)
    pascal_string.write_string(file, bmf.default_texture_name)
    write_mesh(file, bmf.mesh)


def read_file(file_path: pathlib.Path) -> Bmf:
    """Read a file as a BMF."""
    try:
        with file_path.open(mode='rb') as file:
            bmf = read_bmf(file)

            if len(file.read(1)) != 0:
                raise error.FileReadError

            return bmf

    except (OSError, struct.error) as exception:
        raise error.FileReadError from exception


def write_file(file_path: pathlib.Path, bmf: Bmf) -> None:
    """Write a BMF to a file."""
    with file_path.open('wb') as file:
        write_bmf(file, bmf)
