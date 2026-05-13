"""The Sims 1 Blender IO."""

bl_info = {
    "name": "The Sims 1 3D Formats",
    "description": "Import and export The Sims 1 meshes and animations",
    "author": "mix",
    "version": (1, 4, 2),
    "blender": (4, 1, 0),
    "location": "File > Import-Export",
    "warning": "",
    "doc_url": "https://github.com/mixiate/ts1-blender-io/wiki",
    "tracker_url": "https://github.com/mixiate/ts1-blender-io/issues",
    "support": "COMMUNITY",
    "category": "Import-Export",
}


if "bpy" in locals():
    import importlib
    import sys

    for name in tuple(sys.modules):
        if name.startswith(__name__ + "."):
            importlib.reload(sys.modules[name])


import typing  # noqa: E402

import bpy  # noqa: E402
import bpy_extras  # noqa: E402


class TS1IOImport(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Import The Sims 1 files."""

    bl_idname: str = "import.bcf"
    bl_label: str = "Import The Sims 1 meshes and animations"
    bl_description: str = "Import a cmx or bcf file from The Sims 1"
    bl_options: typing.ClassVar[set[str]] = {'UNDO'}

    filename_ext = ".cmx.bcf"

    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.cmx;*.cmx.bcf",
        options={'HIDDEN'},
    )
    files: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )
    directory: bpy.props.StringProperty(  # type: ignore[valid-type]
        subtype='DIR_PATH',
    )

    import_skeletons: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Import Skeletons",
        default=True,
    )

    import_meshes: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Import Meshes",
        default=True,
    )

    import_animations: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Import Animations",
        default=True,
    )

    find_skeleton: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Find Skeleton Automatically",
        description="Find and load the correct skeleton, otherwise attempt to import mesh on selected armature",
        default=True,
    )

    cleanup_meshes: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Cleanup Meshes (Lossy)",
        description="Merge the vertices of the mesh, add sharp edges, remove original normals and shade smooth",
        default=True,
    )

    fix_textures: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Fix Official Texture Mistakes",
        description="Fix texture file mistakes made in the game, expansions and official downloads",
        default=True,
    )

    skin_color: bpy.props.EnumProperty(  # type: ignore[valid-type]
        name="Skin Color",
        description="Which skin color texture will be set to the active material",
        items=[
            ('drk', "Dark", ""),
            ('med', "Medium", ""),
            ('lgt', "Light", ""),
        ],
        default='med',
    )

    def execute(self, context: bpy.context) -> set[str]:
        """Execute the importing function."""
        import io  # noqa: PLC0415
        import logging  # noqa: PLC0415
        import pathlib  # noqa: PLC0415

        from . import import_ts1  # noqa: PLC0415

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        log_stream = io.StringIO()
        logger.addHandler(logging.StreamHandler(stream=log_stream))

        directory = pathlib.Path(self.directory)
        paths = [directory / file.name for file in self.files]

        import_ts1.import_files(
            context,
            logger,
            paths,
            self.skin_color,
            import_skeletons=self.import_skeletons,
            import_meshes=self.import_meshes,
            import_animations=self.import_animations,
            find_skeleton=self.find_skeleton,
            cleanup_meshes=self.cleanup_meshes,
            fix_textures=self.fix_textures,
        )

        log_output = log_stream.getvalue()
        if log_output != "":
            self.report({"ERROR"}, log_output)

        return {'FINISHED'}

    def draw(self, _: bpy.context) -> None:
        """Draw the import options ui."""
        col = self.layout.column()
        col.prop(self, "import_skeletons")
        col.prop(self, "import_meshes")
        col.prop(self, "import_animations")
        col.prop(self, "find_skeleton")
        col.prop(self, "cleanup_meshes")
        col.prop(self, "fix_textures")
        col.label(text="Skin Color:")
        col.prop(self, "skin_color", text="")


class TS1IOExport(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    """Export to The Sims 1 files."""

    bl_idname = "export.bcf"
    bl_label = "Export The Sims 1 meshes and animations"
    bl_description = "Export a cmx or bcf file for The Sims 1"

    check_extension = None
    filename_ext = ".cmx.bcf"

    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.cmx;*.cmx.bcf",
        options={'HIDDEN'},
    )

    export_meshes: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Meshes",
        default=True,
    )

    export_animations: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Animations",
        default=True,
    )

    mesh_format: bpy.props.EnumProperty(  # type: ignore[valid-type]
        name="Mesh Format",
        description="Which format to use when exporting meshes",
        items=[
            ('bmf', "BMF", ""),
            ('skn', "SKN", ""),
        ],
        default='bmf',
    )

    apply_modifiers: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Apply Modifiers",
        description="Apply modifiers to meshes before exporting",
        default=True,
    )

    compress_cfp: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Compress CFP file (Lossy)",
        description="Compress the values in the CFP file",
        default=True,
    )

    def execute(self, context: bpy.context) -> set[str]:
        """Execute the exporting function."""
        import pathlib  # noqa: PLC0415

        from . import export_ts1  # noqa: PLC0415

        try:
            export_ts1.export_files(
                context,
                pathlib.Path(self.properties.filepath),
                self.mesh_format,
                export_meshes=self.export_meshes,
                export_animations=self.export_animations,
                compress_cfp=self.compress_cfp,
                apply_modifiers=self.apply_modifiers,
            )
        except export_ts1.ExportError as exception:
            self.report({"ERROR"}, exception.args[0])

        return {'FINISHED'}

    def draw(self, _: bpy.context) -> None:
        """Draw the export options ui."""
        col = self.layout.column()
        col.prop(self, "export_meshes")
        col.prop(self, "export_animations")
        col.label(text="Mesh Format:")
        col.prop(self, "mesh_format", text="")
        col.prop(self, "apply_modifiers")
        col.prop(self, "compress_cfp")


def ts1_menu_import(self: bpy.types.TOPBAR_MT_file_import, _: bpy.context) -> None:
    """Add an entry to the import menu."""
    self.layout.operator(TS1IOImport.bl_idname, text="The Sims 1 (.cmx/.bcf)")


def ts1_menu_export(self: bpy.types.TOPBAR_MT_file_export, _: bpy.context) -> None:
    """Add an entry to the export menu."""
    self.layout.operator(TS1IOExport.bl_idname, text="The Sims 1 (.cmx/.bcf)")


class TS1IOAddonPreferences(bpy.types.AddonPreferences):
    """Preferences for the addon."""

    bl_idname = __name__

    file_search_directory: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="File Search Directory",
        description="Directory that will be recursively searched to find referenced files",
        subtype='DIR_PATH',
        default="",
    )

    def draw(self, _: bpy.context) -> None:
        """Draw the addon preferences ui."""
        self.layout.prop(self, "file_search_directory")


class TSOIOImport(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Import The Sims Online files."""

    bl_idname: str = "tsoblenderio.import"
    bl_label: str = "The Sims Online (.skel/.mesh)"
    bl_description: str = "Import a skel or mesh file from The Sims Online"
    bl_options: typing.ClassVar[set[str]] = {'UNDO'}

    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.skel;*.mesh",
        options={'HIDDEN'},
    )
    files: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )
    directory: bpy.props.StringProperty(  # type: ignore[valid-type]
        subtype='DIR_PATH',
    )

    cleanup_meshes: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Cleanup Meshes (Lossy)",
        description="Merge the vertices of the mesh, add sharp edges, remove original normals and shade smooth",
        default=True,
    )

    def execute(self, context: bpy.context) -> set[str]:
        """Execute the importing function."""
        import io  # noqa: PLC0415
        import logging  # noqa: PLC0415
        import pathlib  # noqa: PLC0415

        from . import import_tso  # noqa: PLC0415

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        log_stream = io.StringIO()
        logger.addHandler(logging.StreamHandler(stream=log_stream))

        directory = pathlib.Path(self.directory)
        paths = [directory / file.name for file in self.files]

        import_tso.import_files(
            context,
            logger,
            paths,
            cleanup_meshes=self.cleanup_meshes,
        )

        log_output = log_stream.getvalue()
        if log_output != "":
            self.report({"ERROR"}, log_output)

        return {'FINISHED'}


class TSOIOExport(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    """Export The Sims Online files."""

    bl_idname = "ts1blenderio.exporttso"
    bl_label = "The Sims Online (.mesh)"
    bl_description = "Export mesh files for The Sims Online"

    directory: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Output Directory Path",
        description="Output Directory Path",
        subtype='DIR_PATH',
    )

    filter_folder: bpy.props.BoolProperty(  # type: ignore[valid-type]
        default=True, options={"HIDDEN"}
    )

    export_meshes: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Meshes",
        default=True,
    )

    apply_modifiers: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Apply Modifiers",
        description="Apply modifiers to meshes before exporting",
        default=True,
    )

    def execute(self, context: bpy.context) -> set[str]:
        """Execute the exporting function."""
        import pathlib  # noqa: PLC0415

        from . import export_tso, utils  # noqa: PLC0415

        try:
            export_tso.export_files(
                context,
                pathlib.Path(self.properties.filepath),
                export_meshes=self.export_meshes,
                apply_modifiers=self.apply_modifiers,
            )
        except utils.ExportError as exception:
            self.report({"ERROR"}, exception.args[0])

        return {'FINISHED'}

    def invoke(self, context: bpy.context, _: bpy.types.Event) -> set[str]:
        """Invoke the file selection window."""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def tso_menu_import(self: bpy.types.TOPBAR_MT_file_import, _: bpy.context) -> None:
    """Add an entry to the import menu."""
    self.layout.operator(TSOIOImport.bl_idname)


def tso_menu_export(self: bpy.types.TOPBAR_MT_file_export, _: bpy.context) -> None:
    """Add an entry to the export menu."""
    self.layout.operator(TSOIOExport.bl_idname)


classes = (
    TS1IOImport,
    TS1IOExport,
    TS1IOAddonPreferences,
    TSOIOImport,
    TSOIOExport,
)


def register() -> None:
    """Register with Blender."""
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(ts1_menu_import)
    bpy.types.TOPBAR_MT_file_export.append(ts1_menu_export)

    bpy.types.TOPBAR_MT_file_import.append(tso_menu_import)
    bpy.types.TOPBAR_MT_file_export.append(tso_menu_export)


def unregister() -> None:
    """Unregister with Blender."""
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(ts1_menu_import)
    bpy.types.TOPBAR_MT_file_export.remove(ts1_menu_export)

    bpy.types.TOPBAR_MT_file_import.remove(tso_menu_import)
    bpy.types.TOPBAR_MT_file_export.remove(tso_menu_export)


if __name__ == "__main__":
    register()
