"""Final deliverable renders + glTF export, run headless:

  blender -b blender/galahad.blend -P blender/scripts/final_renders.py

Writes docs/images/*.png, blender/galahad.glb and blender/galahad.fbx.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from render_utils import aim_camera, ensure_world, make_camera, pick_engine  # noqa: E402

IMAGES = os.path.join(ROOT, "docs", "images")
BLENDER = os.path.join(ROOT, "blender")

VIEWS = [
    ("front", (0, -1, 0.02)),
    ("right", (1, 0, 0.02)),
    ("back", (0, 1, 0.02)),
    ("left", (-1, 0, 0.02)),
    ("top", (0, -0.001, 1)),
    ("iso", (0.85, -1.0, 0.42)),
]


def setup(res=(1000, 1250), samples=64):
    scene = bpy.context.scene
    scene.render.engine = pick_engine()
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    try:
        scene.eevee.taa_render_samples = samples
    except Exception:
        pass
    ensure_world()
    return scene


def render_turnaround(scene):
    cam = make_camera()
    os.makedirs(IMAGES, exist_ok=True)
    written = []
    for name, direction in VIEWS:
        aim_camera(cam, (0, 0, 122), direction, ortho_scale=290.0)
        scene.render.filepath = os.path.join(IMAGES, f"galahad_{name}.png")
        bpy.ops.render.render(write_still=True)
        written.append(scene.render.filepath)
    return written


def render_hero(scene):
    cam = make_camera("HeroCam")
    cam.data.type = "PERSP"
    cam.data.lens = 68.0
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 5.6
    cam.location = Vector((360, -430, 250))
    target = Vector((0, 0, 132))
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.dof.focus_distance = (target - cam.location).length
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = 1600, 1100
    try:
        scene.eevee.taa_render_samples = 96
    except Exception:
        pass
    scene.render.filepath = os.path.join(IMAGES, "galahad_hero.png")
    bpy.ops.render.render(write_still=True)
    return scene.render.filepath


def text_to_mesh():
    for obj in list(bpy.data.objects):
        if obj.type == "FONT":
            bpy.context.view_layer.objects.active = obj
            for o in bpy.context.view_layer.objects:
                o.select_set(False)
            obj.select_set(True)
            bpy.ops.object.convert(target="MESH")
            obj.select_set(False)


def export_models():
    written = []
    glb = os.path.join(BLENDER, "galahad.glb")
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.export_scene.gltf(
        filepath=glb,
        export_format="GLB",
        use_selection=False,
        export_apply=True,
        export_yup=True,
        export_animations=False,
    )
    written.append(glb)

    objs = [o for o in bpy.data.objects if o.type == "MESH" and o.name != "StudioFloor"]
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(BLENDER, "galahad.fbx"),
        use_selection=True,
        apply_scale_options="FBX_SCALE_ALL",
        mesh_smooth_type="FACE",
        path_mode="AUTO",
    )
    written.append(os.path.join(BLENDER, "galahad.fbx"))
    return written


def main():
    scene = setup()
    shots = render_turnaround(scene)
    shots.append(render_hero(scene))
    text_to_mesh()
    models = export_models()
    bpy.ops.wm.save_mainfile()
    for p in shots + models:
        print("WROTE", p, os.path.getsize(p) if os.path.exists(p) else "MISSING")


main()
