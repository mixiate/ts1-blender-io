from . import bmf


def read_bones(file):
    count = int(file.readline())
    bones = []
    for i in range(count):
        bones.append(file.readline().strip())
    return bones


def write_bones(file, bones):
    file.write(str(len(bones)) + "\n")
    for bone in bones:
        file.write(bone + "\n")


def read_faces(file):
    count = int(file.readline())
    faces = []
    for i in range(count):
        values = file.readline().split(" ")
        faces.append((int(values[0]), int(values[1]), int(values[2])))
    return faces


def write_faces(file, faces):
    file.write(str(len(faces)) + "\n")
    for face in faces:
        file.write("{} {} {}\n".format(*face))


def read_bone_bindings(file):
    count = int(file.readline())
    bone_bindings = []
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


def write_bone_bindings(file, bone_bindings):
    file.write(str(len(bone_bindings)) + "\n")
    for bone_binding in bone_bindings:
        file.write(f"{bone_binding.bone_index}\n")
        file.write(f"{bone_binding.vertex_index}\n")
        file.write(f"{bone_binding.vertex_count}\n")
        file.write(f"{bone_binding.blended_vertex_index}\n")
        file.write(f"{bone_binding.blended_vertex_count}\n")


def read_uvs(file):
    count = int(file.readline())
    uvs = []
    for i in range(count):
        values = file.readline().split(" ")
        uvs.append((float(values[0]), float(values[1])))
    return uvs


def write_uvs(file, uvs):
    file.write(str(len(uvs)) + "\n")
    for uv in uvs:
        file.write("{:.7f} {:.7f}\n".format(*uv))


def read_blends(file):
    count = int(file.readline())
    blends = []
    for i in range(count):
        values = file.readline().split(" ")
        blends.append(
            bmf.Blend(
                int(values[1]),
                int(values[0]),
            )
        )
    return blends


def write_blends(file, blends):
    file.write(str(len(blends)) + "\n")
    for blend in blends:
        file.write(f"{blend.vertex_index} {blend.weight}\n")


def read_vertices(file):
    count = int(file.readline())
    vertices = []
    for i in range(count):
        values = file.readline().split(" ")
        vertices.append(
            bmf.Vertex(
                (float(values[0]), float(values[1]), float(values[2])),
                (float(values[3]), float(values[4]), float(values[5])),
            )
        )
    return vertices


def write_vertices(file, vertices):
    file.write(str(len(vertices)) + "\n")
    for vertex in vertices:
        file.write("{:.7f} {:.7f} {:.7f} {:.7f} {:.7f} {:.7f}\n".format(*vertex.position, *vertex.normal))


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


def write_skn(file, bmf):
    file.write(bmf.skin_name + "\n")
    file.write(bmf.default_texture_name + "\n")
    write_bones(file, bmf.bones)
    write_faces(file, bmf.faces)
    write_bone_bindings(file, bmf.bone_bindings)
    write_uvs(file, bmf.uvs)
    write_blends(file, bmf.blends)
    write_vertices(file, bmf.vertices)


def read_file(file_path):
    with open(file_path) as file:
        skn = read_skn(file)

        if file.readline() != "":
            raise Exception("data left unread at end of " + file_path)

        return skn


def write_file(file_path, bmf):
    with open(file_path, 'w') as file:
        write_skn(file, bmf)
