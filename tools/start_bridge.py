import importlib.util
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON = os.path.join(ROOT, "tools", "blender_bridge_addon.py")
BLEND = os.path.join(ROOT, "blender", "galahad.blend")

if os.path.exists(BLEND) and bpy.data.filepath != BLEND:
    bpy.ops.wm.open_mainfile(filepath=BLEND)

spec = importlib.util.spec_from_file_location("galahad_bridge_addon", ADDON)
mod = importlib.util.module_from_spec(spec)
sys.modules["galahad_bridge_addon"] = mod
spec.loader.exec_module(mod)
mod.register()
print("Galahad bridge up on 127.0.0.1:9876 —", bpy.data.filepath)
