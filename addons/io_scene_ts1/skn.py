"""Read and write The Sims 1 SKN files."""

import pathlib
import typing


from . import bmf
from . import utils


def read_bones(file: typing.TextIO) -> list[str]:
    """Read SKN bones."""
    count = int(file.readline())
    return [file.readline().strip() for _ in range(count)]


def write_bones(file: typing.TextIO, bones: list[str]) -> None:
    """Write SKN bones."""
    file.write(str(len(bones)) + "\n")
    for bone in bones:
        file.write(bone + "\n")


def read_faces(file: typing.TextIO) -> list[tuple[int, int, int]]:
    """Read SKN faces."""
    count = int(file.readline())
    faces = []
    for _ in range(count):
        values = file.readline().split(" ")
        faces.append((int(values[0]), int(values[1]), int(values[2])))
    return faces


def write_faces(file: typing.TextIO, faces: list[tuple[int, int, int]]) -> None:
    """Write SKN faces."""
    file.write(str(len(faces)) + "\n")
    for face in faces:
        file.write("{} {} {}\n".format(*face))


def read_bone_bindings(file: typing.TextIO) -> list[bmf.BoneBinding]:
    """Read SKN bone bindings."""
    count = int(file.readline())
    bone_bindings = []
    for _ in range(count):
        values = file.readline().split(" ")
        bone_bindings.append(
            bmf.BoneBinding(
                int(values[0]),
                int(values[1]),
                int(values[2]),
                int(values[3]),
                int(values[4]),
            ),
        )
    return bone_bindings


def write_bone_bindings(file: typing.TextIO, bone_bindings: list[bmf.BoneBinding]) -> None:
    """Write SKN bone bindings."""
    file.write(str(len(bone_bindings)) + "\n")
    for bone_binding in bone_bindings:
        file.write(
            "{} {} {} {} {}\n".format(  # noqa: UP032
                bone_binding.bone_index,
                bone_binding.vertex_index,
                bone_binding.vertex_count,
                bone_binding.blended_vertex_index,
                bone_binding.blended_vertex_count,
            ),
        )


def read_uvs(file: typing.TextIO) -> list[tuple[float, float]]:
    """Read SKN uvs."""
    count = int(file.readline())
    uvs = []
    for _ in range(count):
        values = file.readline().split(" ")
        uvs.append((float(values[0]), float(values[1])))
    return uvs


def write_uvs(file: typing.TextIO, uvs: list[tuple[float, float]]) -> None:
    """Write SKN uvs."""
    file.write(str(len(uvs)) + "\n")
    for uv in uvs:
        file.write("{:.7f} {:.7f}\n".format(*uv))


def read_blends(file: typing.TextIO) -> list[bmf.Blend]:
    """Read SKN blends."""
    count = int(file.readline())
    blends = []
    for _ in range(count):
        values = file.readline().split(" ")
        blends.append(
            bmf.Blend(
                int(values[1]),
                int(values[0]),
            ),
        )
    return blends


def write_blends(file: typing.TextIO, blends: list[bmf.Blend]) -> None:
    """Write SKN blends."""
    file.write(str(len(blends)) + "\n")
    for blend in blends:
        file.write(f"{blend.vertex_index} {blend.weight}\n")


def read_vertices(file: typing.TextIO) -> list[bmf.Vertex]:
    """Read SKN vertices."""
    count = int(file.readline())
    vertices = []
    for _ in range(count):
        values = file.readline().split(" ")
        vertices.append(
            bmf.Vertex(
                (float(values[0]), float(values[1]), float(values[2])),
                (float(values[3]), float(values[4]), float(values[5])),
            ),
        )
    return vertices


def write_vertices(file: typing.TextIO, vertices: list[bmf.Vertex]) -> None:
    """Write SKN vertices."""
    file.write(str(len(vertices)) + "\n")
    for vertex in vertices:
        file.write("{:.7f} {:.7f} {:.7f} {:.7f} {:.7f} {:.7f}\n".format(*vertex.position, *vertex.normal))


def read_skn(file: typing.TextIO) -> bmf.Bmf:
    """Read SKN."""
    return bmf.Bmf(
        file.readline().strip(),
        file.readline().strip(),
        read_bones(file),
        read_faces(file),
        read_bone_bindings(file),
        read_uvs(file),
        read_blends(file),
        read_vertices(file),
    )


def write_skn(file: typing.TextIO, bmf: bmf.Bmf) -> None:
    """Write SKN."""
    file.write(bmf.skin_name + "\n")
    file.write(bmf.default_texture_name + "\n")
    write_bones(file, bmf.bones)
    write_faces(file, bmf.faces)
    write_bone_bindings(file, bmf.bone_bindings)
    write_uvs(file, bmf.uvs)
    write_blends(file, bmf.blends)
    write_vertices(file, bmf.vertices)


def read_file(file_path: pathlib.Path) -> bmf.Bmf:
    """Read a file as a SKN."""
    try:
        with file_path.open() as file:
            bmf = read_skn(file)

            if file.readline() != "":
                raise utils.FileReadError

            return bmf

    except OSError as exception:
        raise utils.FileReadError from exception


def write_file(file_path: pathlib.Path, bmf: bmf.Bmf) -> None:
    """Write a SKN to a file."""
    with file_path.open('w') as file:
        write_skn(file, bmf)
