"""Rebuild galahad.blend from the reference mesh, headless.

    blender -b -P blender/scripts/build_from_scratch.py

Requires reference/humanoid robot 3d model.3mf next to the repo root.
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import build_galahad  # noqa: E402

build_galahad.build_scene(root=ROOT)

out = os.path.join(ROOT, "blender", "galahad.blend")
bpy.ops.wm.save_as_mainfile(filepath=out)
print("WROTE", out, os.path.getsize(out))
