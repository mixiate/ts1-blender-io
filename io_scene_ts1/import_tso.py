"""Import The Sims Online files."""

import logging
import pathlib

import bpy

from . import import_skeleton
from .ts1_formats import skel
from .ts1_formats.error import FileReadError


def import_files(
    context: bpy.types.Context,
    logger: logging.Logger,
    file_paths: list[pathlib.Path],
) -> None:
    """Import all the selected files."""
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    for file_path in file_paths:
        try:
            skeleton = skel.read_file(file_path)
            import_skeleton.import_skeleton(context, skeleton)

        except FileReadError as _:  # noqa: PERF203
            logger.info(f"Could not import {file_path}")  # noqa: G004
