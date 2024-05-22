bl_info = {
    "name": "The Sims 1 3D Formats",
    "description": "Imports and exports The Sims 1 meshes and animations.",
    "author": "mix",
    "version": (0, 0, 0),
    "blender": (4, 1, 0),
    "location": "File > Import-Export",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Import-Export",
}


if "bpy" in locals():
    import sys
    import importlib
    for name in tuple(sys.modules):
        if name.startswith(__name__ + "."):
            importlib.reload(sys.modules[name])


import bpy
import bpy_extras


class ImportTS1(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "import.bcf"
    bl_label = "Import The Sims 1 meshes and animations"
    bl_description = ""
    bl_options = {'UNDO'}

    filename_ext = ".cmx.bcf"

    filter_glob: bpy.props.StringProperty(
        default="*.cmx.bcf",
        options={'HIDDEN'},
    )
    files: bpy.props.CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )
    directory: bpy.props.StringProperty(
        subtype='DIR_PATH',
    )

    cleanup_meshes: bpy.props.BoolProperty(
        name="Cleanup Meshes (Lossy)",
        description="Merge the vertices of the mesh, add sharp edges, remove original normals and shade smooth",
        default=True,
    )

    def execute(self, context):
        import io
        import logging
        import os
        from . import import_ts1

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        log_stream = io.StringIO()
        logger.addHandler(logging.StreamHandler(stream=log_stream))

        paths = [os.path.join(self.directory, name.name) for name in self.files]

        if not paths:
            paths.append(self.filepath)

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action='DESELECT')

        import_ts1.import_files(context, logger, paths, self.cleanup_meshes, context.scene.ts1_import_skin_color)

        log_output = log_stream.getvalue()
        if log_output != "":
            self.report({"ERROR"}, log_output)

        return {'FINISHED'}

    def draw(self, context):
        col = self.layout.column()
        col.prop(self, "cleanup_meshes")
        col.label(text="Skin Color:")
        col.prop(context.scene, "ts1_import_skin_color", text="")


class ExportTS1(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "export.cmx"
    bl_label = "Export The Sims 1 meshes and animations"
    bl_description = ""

    filename_ext = ".cmx"

    filter_glob: bpy.props.StringProperty(
        default="*.cmx.bcf",
        options={'HIDDEN'},
    )

    compress_cfp: bpy.props.BoolProperty(
        name="Compress CFP file (Lossy)",
        description="Compress the values in the CFP file",
        default=True,
    )

    def execute(self, context):
        from . import export_ts1

        try:
            export_ts1.export_files(context, self.properties.filepath, self.compress_cfp)
        except Exception as exception:
             self.report({"ERROR"}, exception.args[0])

        return {'FINISHED'}

    def draw(self, context):
        col = self.layout.column()
        col.prop(self, "compress_cfp")


def menu_import(self, context):
    self.layout.operator(ImportTS1.bl_idname, text="The Sims 1 (.cmx.bcf)")


def menu_export(self, context):
    self.layout.operator(ExportTS1.bl_idname, text="The Sims 1 (.cmx.bcf)")


class TS1_IO_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    file_search_directory: bpy.props.StringProperty(
        name="File Search Directory",
        description="Directory that will be recursively searched to find referenced files",
        subtype='FILE_PATH',
        default="",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "file_search_directory")


classes = (
    ImportTS1,
    ExportTS1,
    TS1_IO_AddonPreferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_export)

    bpy.types.Scene.ts1_import_skin_color = bpy.props.EnumProperty(
        name="Skin Color",
        description="Which skin color texture will be set to the active material",
        items=[
            ('drk', "Dark", ""),
            ('med', "Medium", ""),
            ('lgt', "Light", ""),
        ],
        default='med',
    )


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(menu_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_export)

    del bpy.types.Scene.ts1_import_skin_color


if __name__ == "__main__":
    register()
