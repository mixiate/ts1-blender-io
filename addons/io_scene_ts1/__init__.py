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

    def execute(self, context):
        import os
        from . import import_ts1

        paths = [os.path.join(self.directory, name.name) for name in self.files]

        if not paths:
            paths.append(self.filepath)

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action='DESELECT')

        try:
            import_ts1.import_files(context, paths)
        except Exception as exception:
             self.report({"ERROR"}, exception.args[0])

        return {'FINISHED'}

    def draw(self, context):
        pass


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
        name="Compress CFP file",
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


classes = (
    ImportTS1,
    ExportTS1,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_export)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(menu_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_export)


if __name__ == "__main__":
    register()
