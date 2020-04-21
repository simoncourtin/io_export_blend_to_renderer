bl_info = {
    "name": "Export Blend to render format",
    "category": "Import-Export",
    "blender": (2, 79, 2),
}

import sys
import os

from io_export_blend_to_render import exporter
from io_export_blend_to_render import pbrt
from io_export_blend_to_render import nodes

def register():
    exporter.register()
    pbrt.register()
    nodes.register()

def unregister():
    exporter.unregister()
    pbrt.unregister()
    nodes.unregister()

if __name__ == "__main__":
    register()