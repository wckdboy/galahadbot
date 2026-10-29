"""Render a turnaround from a saved .blend headlessly.

Usage:
  blender -b model.blend -P render_views.py -- <out_dir> <prefix> [--res 720x900] [--target z]
"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_utils import aim_camera, ensure_lights, ensure_world, make_camera, pick_engine  # noqa: E402

VIEWS = {
    "front": (0, -1, 0.04),
    "right": (1, 0, 0.04),
    "back": (0, 1, 0.04),
    "left": (-1, 0, 0.04),
    "top": (0, -0.001, 1),
    "iso": (0.85, -1.0, 0.45),
    "hero": (0.55, -1.0, 0.22),
}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out_dir = argv[0] if argv else "renders"
    prefix = argv[1] if len(argv) > 1 else "view"
    res = (720, 900)
    target_z = 122.0
    scale = 300.0
    only = None
    i = 2
    while i < len(argv):
        if argv[i] == "--res":
            w, h = argv[i + 1].lower().split("x")
            res = (int(w), int(h))
            i += 2
        elif argv[i] == "--target":
            target_z = float(argv[i + 1])
            i += 2
        elif argv[i] == "--scale":
            scale = float(argv[i + 1])
            i += 2
        elif argv[i] == "--only":
            only = argv[i + 1].split(",")
            i += 2
        else:
            i += 1

    ensure_world()
    ensure_lights()
    cam = make_camera()
    scene = bpy.context.scene
    scene.render.engine = pick_engine()
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    try:
        scene.eevee.taa_render_samples = 32
    except Exception:
        pass

    os.makedirs(out_dir, exist_ok=True)
    written = []
    for name, direction in VIEWS.items():
        if only and name not in only:
            continue
        aim_camera(cam, (0, 0, target_z), direction, ortho_scale=scale)
        scene.render.filepath = os.path.join(out_dir, f"{prefix}_{name}.png")
        bpy.ops.render.render(write_still=True)
        written.append(scene.render.filepath)
    for p in written:
        print("WROTE", p)


main()
