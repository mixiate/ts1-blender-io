"""Read and write The Sims 1 BMF files."""

import dataclasses
import pathlib
import struct
import typing

from . import utils


def read_bones(file: typing.BinaryIO) -> list[str]:
    """Read BMF bones."""
    count = struct.unpack('<I', file.read(4))[0]
    return [utils.read_string(file) for _ in range(count)]


def write_bones(file: typing.BinaryIO, bones: list[str]) -> None:
    """Write BMF bones."""
    file.write(struct.pack('<I', len(bones)))
    for bone in bones:
        utils.write_string(file, bone)


def read_faces(file: typing.BinaryIO) -> list[tuple[int, int, int]]:
    """Read BMF faces."""
    count = struct.unpack('<I', file.read(4))[0]
    return [struct.unpack('<3I', file.read(4 * 3)) for _ in range(count)]


def write_faces(file: typing.BinaryIO, faces: list[tuple[int, int, int]]) -> None:
    """Write BMF faces."""
    file.write(struct.pack('<I', len(faces)))
    for face in faces:
        file.write(struct.pack('<3I', *face))


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
    for uv in uvs:
        file.write(struct.pack('<2f', *uv))


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


def read_vertices(file: typing.BinaryIO) -> list[Vertex]:
    """Read BMF vertices."""
    count = struct.unpack('<I', file.read(4))[0]
    return [
        Vertex(
            struct.unpack('<3f', file.read(4 * 3)),
            struct.unpack('<3f', file.read(4 * 3)),
        )
        for _ in range(count)
    ]


def write_vertices(file: typing.BinaryIO, vertices: list[Vertex]) -> None:
    """Write BMF vertices."""
    file.write(struct.pack('<I', len(vertices)))
    for vertex in vertices:
        file.write(struct.pack('<3f', *vertex.position))
        file.write(struct.pack('<3f', *vertex.normal))


@dataclasses.dataclass
class Bmf:
    """BMF File."""

    skin_name: str
    default_texture_name: str
    bones: list[str]
    faces: list[tuple[int, int, int]]
    bone_bindings: list[BoneBinding]
    uvs: list[tuple[float, float]]
    blends: list[Blend]
    vertices: list[Vertex]


def read_bmf(file: typing.BinaryIO) -> Bmf:
    """Read BMF."""
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


def write_bmf(file: typing.BinaryIO, bmf: Bmf) -> None:
    """Write BMF."""
    utils.write_string(file, bmf.skin_name)
    utils.write_string(file, bmf.default_texture_name)
    write_bones(file, bmf.bones)
    write_faces(file, bmf.faces)
    write_bone_bindings(file, bmf.bone_bindings)
    write_uvs(file, bmf.uvs)
    write_blends(file, bmf.blends)
    write_vertices(file, bmf.vertices)


def read_file(file_path: pathlib.Path) -> Bmf:
    """Read a file as a BMF."""
    with file_path.open(mode='rb') as file:
        bmf = read_bmf(file)

        try:
            file.read(1)
            raise Exception("data left unread at end of " + file_path.as_posix())
        except Exception as _:
            pass

        return bmf


def write_file(file_path: pathlib.Path, bmf: Bmf) -> None:
    """Write a BMF to a file."""
    with file_path.open('wb') as file:
        write_bmf(file, bmf)
