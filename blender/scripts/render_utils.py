"""Shared render helpers for the Galahad Blender build."""
import math
import os

import bpy
from mathutils import Vector


def pick_engine():
    """Blender 5.2 renamed the EEVEE enum; probe instead of hard-coding."""
    available = bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys()
    for candidate in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH"):
        if candidate in available:
            return candidate
    return "BLENDER_WORKBENCH"


def ensure_world(strength=0.35, color=(0.85, 0.87, 0.9)):
    world = bpy.data.worlds.get("GalahadWorld") or bpy.data.worlds.new("GalahadWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (*color, 1.0)
    bg.inputs[1].default_value = strength
    bpy.context.scene.world = world
    return world


def ensure_lights():
    for name, loc, energy, size in (
        ("KeyLight", (600, -700, 900), 900.0, 0.35),
        ("FillLight", (-700, -450, 500), 320.0, 0.6),
        ("RimLight", (200, 800, 700), 500.0, 0.4),
    ):
        light = bpy.data.objects.get(name)
        if light is None:
            data = bpy.data.lights.new(name, type="AREA")
            light = bpy.data.objects.new(name, data)
            bpy.context.scene.collection.objects.link(light)
        light.data.energy = energy
        light.data.size = abs(loc[0] or 400) * size
        light.location = loc
        direction = Vector((0, 0, 120)) - Vector(loc)
        light.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return True


def make_camera(name="GalahadCam"):
    cam = bpy.data.objects.get(name)
    if cam is None:
        data = bpy.data.cameras.new(name)
        cam = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    bpy.context.scene.camera = cam
    return cam


def aim_camera(cam, target, direction, distance=900.0, ortho_scale=320.0):
    d = Vector(direction).normalized()
    cam.location = Vector(target) + d * distance
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = ortho_scale


def render_view(path, target=(0, 0, 120), direction=(0, -1, 0.12), ortho_scale=300.0,
                res=(900, 1100), engine=None, samples=16, transparent=False):
    scene = bpy.context.scene
    engine = engine or pick_engine()
    scene.render.engine = engine
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = "PNG"
    if engine.startswith("BLENDER_EEVEE") and hasattr(scene, "eevee"):
        try:
            scene.eevee.taa_render_samples = samples
        except Exception:
            pass
    ensure_world()

    cam = make_camera()
    aim_camera(cam, target, direction, ortho_scale=ortho_scale)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def hex_rgba(value, alpha=1.0):
    value = value.lstrip("#")
    r, g, b = (int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (r, g, b, alpha)


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
