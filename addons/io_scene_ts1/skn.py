from . import bmf
from . import utils


def read_bones(file):
    count = int(file.readline())
    bones = list()
    for i in range(count):
        bones.append(file.readline().strip())
    return bones


def read_faces(file):
    count = int(file.readline())
    faces = list()
    for i in range(count):
        values = file.readline().split(" ")
        faces.append((int(values[0]), int(values[1]), int(values[2])))
    return faces


def read_bone_bindings(file):
    count = int(file.readline())
    bone_bindings = list()
    for i in range(count):
        values = file.readline().split(" ")
        bone_bindings.append(
            bmf.BoneBinding(
                int(values[0]),
                int(values[1]),
                int(values[2]),
                int(values[3]),
                int(values[4]),
            )
        )
    return bone_bindings


def read_uvs(file):
    count = int(file.readline())
    uvs = list()
    for i in range(count):
        values = file.readline().split(" ")
        uvs.append((float(values[0]), float(values[1])))
    return uvs


def read_blends(file):
    count = int(file.readline())
    blends = list()
    for i in range(count):
        values = file.readline().split(" ")
        blends.append(
            bmf.Blend(
                int(values[1]),
                int(values[0]),
            )
        )
    return blends


def read_vertices(file):
    count = int(file.readline())
    vertices = list()
    for i in range(count):
        values = file.readline().split(" ")
        vertices.append(
            bmf.Vertex(
                (float(values[0]), float(values[1]), float(values[2])),
                (float(values[3]), float(values[4]), float(values[5])),
            )
        )
    return vertices


def read_skn(file):
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


def read_file(file_path):
    with open(file_path) as file:
        skn = read_skn(file)

        if file.readline() != "":
            raise Exception("data left unread at end of " + file_path)

        return skn
