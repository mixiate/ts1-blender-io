"""Read The Sims 1 XBM files."""

import dataclasses
import pathlib
import struct
import typing

from . import utils


@dataclasses.dataclass
class Vertex:
    """Xbox Mesh Vertex."""

    position: tuple[float, float, float]
    unknown: int


def read_vertices(file: typing.BinaryIO, count: int) -> list[Vertex]:
    """Read vertices."""
    return [
        Vertex(
            struct.unpack('<3f', file.read(4 * 3)),
            struct.unpack('<I', file.read(4))[0],
        )
        for _ in range(count)
    ]


@dataclasses.dataclass
class Mesh:
    """Xbox Mesh."""

    positions: list[Vertex]
    uvs: list[tuple[float, float]]
    normals: list[tuple[float, float, float]]
    faces: list[int]
    strips: list[tuple[int, int]]
    texture_id: int


def read_mesh(file: typing.BinaryIO) -> Mesh:  # noqa: C901 PLR0912 PLR0915
    """Read mesh."""
    flags = struct.unpack('<I', file.read(4))[0]

    texture_id = struct.unpack('<I', file.read(4))[0]

    strip_count = struct.unpack('<I', file.read(4))[0]
    file.read(strip_count)

    positions = []
    uvs = []
    normals = []
    faces = []
    strips = []

    previous_strip_end = 0

    for _ in range(strip_count):
        mesh_type = struct.unpack('<B', file.read(1))[0]

        if mesh_type == 4:  # noqa: PLR2004
            for _ in range(strip_count):
                file.read(1)

                vertex_count = struct.unpack('<I', file.read(4))[0]

                positions += read_vertices(file, vertex_count)
                uvs += [struct.unpack('<2f', file.read(8)) for _ in range(vertex_count)]

                if flags & 0b00000100:
                    file.read(vertex_count * 4)

                if flags & 0b00001000:
                    original_normals = [struct.unpack('<3b', file.read(3)) for _ in range(vertex_count)]
                    for normal in original_normals:
                        x = float(normal[0] / 127.0)
                        y = float(normal[1] / 127.0)
                        z = float(normal[2] / 127.0)
                        normals.append((x, y, z))

                file.read(vertex_count * 4)

                strips.append((previous_strip_end, previous_strip_end + vertex_count))
                previous_strip_end = previous_strip_end + vertex_count

            break

        if mesh_type == 2:  # noqa: PLR2004
            file.read(1)

        read_blends = False

        if mesh_type in (1, 2):
            while True:
                unknowns = struct.unpack('<4B', file.read(4))
                if unknowns[3] == 0:
                    break

                read_blends = True

        vertex_count = struct.unpack('<I', file.read(4))[0]

        positions += read_vertices(file, vertex_count)

        if flags & 0b00000010:
            uvs += [struct.unpack('<2f', file.read(8)) for _ in range(vertex_count)]

        if flags & 0b00000100:
            file.read(vertex_count * 4)

        if flags & 0b00001000:
            original_normals = [struct.unpack('<3b', file.read(3)) for _ in range(vertex_count)]
            for normal in original_normals:
                x = float(normal[0] / 127.0)
                y = float(normal[1] / 127.0)
                z = float(normal[2] / 127.0)
                normals.append((x, y, z))

        if flags & 0b00100000:
            index_count = struct.unpack('<I', file.read(4))[0]
            file.read(1)
            faces = [struct.unpack('<H', file.read(2))[0] for _ in range(index_count)]
        else:
            strips.append((previous_strip_end, previous_strip_end + vertex_count))

        previous_strip_end = previous_strip_end + vertex_count

        if read_blends:
            file.read(vertex_count * 4)

    return Mesh(
        positions,
        uvs,
        normals,
        faces,
        strips,
        texture_id,
    )


@dataclasses.dataclass
class XboxObject:
    """Xbox Object."""

    meshes: list[Mesh]


def read_object(file: typing.BinaryIO) -> XboxObject:
    """Read Xbox Object."""
    file.read(4)

    mesh_count = struct.unpack('<I', file.read(4))[0]

    meshes = []
    for _ in range(mesh_count):
        meshes.append(read_mesh(file))

        marker = struct.unpack('<B', file.read(1))[0]
        if marker != 6:  # noqa: PLR2004
            file.read(1)

    return XboxObject(meshes)


@dataclasses.dataclass
class XboxModel:
    """Xbox Model."""

    name: str
    objects: list[XboxObject]


def read_xbox_model(file: typing.BinaryIO) -> XboxModel:
    """Read Xbox Model."""
    file.read(6)

    name = ''.join(iter(lambda: file.read(1).decode('ascii'), '\x00'))

    file.read(1)

    file.read(4)

    object_count = struct.unpack('<I', file.read(4))[0]

    objects = [read_object(file) for _ in range(object_count)]

    file.read(64)
    file.read(8)

    return XboxModel(
        name,
        objects,
    )


def read_file(file_path: pathlib.Path) -> XboxModel:
    """Read a file as an Xbox Model."""
    try:
        with file_path.open(mode='rb') as file:
            bmf = read_xbox_model(file)

            if len(file.read(1)) != 0:
                raise utils.FileReadError

            return bmf

    except (OSError, struct.error) as exception:
        raise utils.FileReadError from exception
