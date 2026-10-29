"""Build the Galahad Blender scene from the imported reference geometry.

Runs inside Blender (bridge or headless). Idempotent: re-running re-applies
materials/naming/hierarchy on top of the existing mesh objects.

  build_scene()          materials, naming, collections, rig, studio bits
  PART_MAP               ref mesh id -> (collection, name, material key)
"""
import math
import sys

import bpy
from mathutils import Matrix, Vector
import numpy as np

sys.path.insert(0, __file__.rsplit("\\", 1)[0])
import galahad_materials  # noqa: E402

# --------------------------------------------------------------------------
# Part map: 87 imported meshes -> subsystem, descriptive name, material.
# Coordinates in the source model are millimetres, +X right, -Y front, +Z up.
# --------------------------------------------------------------------------
BASE = "01_BASE"
WAIST = "02_WAIST"
TORSO = "03_TORSO"
HEAD = "04_HEAD"
ARM_L = "05_ARM_L"
ARM_R = "06_ARM_R"

PART_MAP = {
    # ---- tracks, drive and chassis -------------------------------------
    "ref_003": (BASE, "tread_L", "rubber"),
    "ref_002": (BASE, "tread_R", "rubber"),
    "ref_032": (BASE, "base_frame", "ivory"),
    "ref_012": (BASE, "base_deck", "navy"),
    "ref_016": (BASE, "base_front_cap", "ivory"),
    "ref_054": (BASE, "base_skirt_front", "navy"),
    "ref_065": (BASE, "base_front_trim", "navy"),
    "ref_040": (BASE, "bumper_front", "navy"),
    "ref_043": (BASE, "base_rear_lower", "navy"),
    "ref_057": (BASE, "base_rear_panel", "navy"),
    "ref_045": (BASE, "base_rear_corner_L", "ivory"),
    "ref_050": (BASE, "base_rear_corner_R", "ivory"),
    "ref_059": (BASE, "base_deck_rear_R", "ivory"),
    "ref_017": (BASE, "base_side_L", "ivory"),
    "ref_034": (BASE, "base_side_R", "ivory"),
    "ref_018": (BASE, "wheel_rear_R", "graphite"),
    "ref_030": (BASE, "wheel_rear_L", "graphite"),
    "ref_022": (BASE, "base_bracket_L", "ivory"),
    "ref_061": (BASE, "base_bracket_R", "navy"),
    "ref_079": (BASE, "base_mount_front_R", "ivory"),
    "ref_083": (BASE, "base_mount_rear_R", "ivory"),
    "ref_014": (BASE, "drive_motor_L", "graphite"),
    "ref_019": (BASE, "drive_motor_R", "graphite"),
    "ref_066": (BASE, "skid_L", "graphite"),
    "ref_068": (BASE, "skid_R", "graphite"),
    "ref_073": (BASE, "tof_front_L", "graphite"),
    "ref_074": (BASE, "tof_front_R", "graphite"),
    "ref_088": (BASE, "tof_front_trim", "graphite"),
    "ref_038": (BASE, "battery_A", "navy"),
    "ref_042": (BASE, "battery_B", "navy"),
    "ref_053": (BASE, "battery_A_latch", "navy"),
    "ref_067": (BASE, "battery_B_latch", "navy"),
    "ref_076": (BASE, "battery_A_handle", "navy"),
    "ref_078": (BASE, "battery_B_handle", "navy"),
    "ref_081": (BASE, "battery_tab_1", "orange"),
    "ref_084": (BASE, "battery_tab_2", "orange"),
    "ref_085": (BASE, "battery_tab_3", "orange"),
    "ref_086": (BASE, "battery_stop", "navy"),
    "ref_075": (BASE, "base_rear_trim_L", "navy"),

    # ---- waist ----------------------------------------------------------
    "ref_015": (WAIST, "waist_turntable", "brass"),
    "ref_024": (WAIST, "waist_block_L", "graphite"),
    "ref_056": (WAIST, "waist_block_R", "graphite"),
    "ref_060": (WAIST, "waist_service_L", "brass"),
    "ref_063": (WAIST, "waist_service_R", "brass"),

    # ---- torso ----------------------------------------------------------
    "ref_006": (TORSO, "torso_shell", "ivory"),
    "ref_035": (TORSO, "torso_front_plate", "ivory"),
    "ref_013": (TORSO, "torso_back_panel", "navy"),
    "ref_029": (TORSO, "chest_speaker", "navy"),
    "ref_070": (TORSO, "chest_screen_bezel", "graphite"),
    "ref_026": (TORSO, "torso_side_L", "ivory"),
    "ref_048": (TORSO, "torso_side_R", "ivory"),
    "ref_055": (TORSO, "torso_side_low_R", "ivory"),
    "ref_062": (TORSO, "torso_side_low_L", "ivory"),
    "ref_041": (TORSO, "torso_compute_bay", "graphite"),
    "ref_023": (TORSO, "torso_side_panel_R", "ivory"),
    "ref_069": (TORSO, "torso_pcb_edge", "navy_dark"),
    "ref_009": (TORSO, "neck_base", "graphite"),
    "ref_080": (TORSO, "neck_ring", "brass"),

    # ---- head -----------------------------------------------------------
    "ref_004": (HEAD, "head_shell", "ivory"),
    "ref_046": (HEAD, "head_sensor_bar", "graphite"),
    "ref_049": (HEAD, "head_side_R", "ivory"),
    "ref_028": (HEAD, "head_side_plate_R", "ivory"),
    "ref_027": (HEAD, "head_side_plate_L", "ivory"),
    "ref_072": (HEAD, "head_back_trim", "navy"),
    "ref_071": (HEAD, "head_lens_ring", "graphite"),
    "ref_077": (HEAD, "head_lens", "glass"),
    "ref_087": (HEAD, "head_ir_window", "glass"),

    # ---- left arm -------------------------------------------------------
    "ref_037": (ARM_L, "shoulder_L", "ivory"),
    "ref_025": (ARM_L, "shoulder_joint_L", "graphite"),
    "ref_082": (ARM_L, "shoulder_disc_L", "brass"),
    "ref_036": (ARM_L, "upperarm_L", "ivory"),
    "ref_033": (ARM_L, "upperarm_inner_L", "ivory"),
    "ref_047": (ARM_L, "elbow_housing_L", "graphite"),
    "ref_021": (ARM_L, "elbow_disc_L", "brass"),
    "ref_051": (ARM_L, "forearm_L", "ivory"),
    "ref_052": (ARM_L, "forearm_inner_L", "ivory"),
    "ref_058": (ARM_L, "wrist_joint_L", "graphite"),
    "ref_064": (ARM_L, "wrist_disc_L", "brass"),
    "ref_020": (ARM_L, "wrist_cuff_L", "ivory"),
    "ref_007": (ARM_L, "gripper_L", "graphite"),

    # ---- right arm ------------------------------------------------------
    "ref_005": (ARM_R, "shoulder_R", "ivory"),
    "ref_044": (ARM_R, "shoulder_joint_R", "graphite"),
    "ref_011": (ARM_R, "upperarm_R", "ivory"),
    "ref_010": (ARM_R, "upperarm_inner_R", "ivory"),
    "ref_008": (ARM_R, "elbow_housing_R", "graphite"),
    "ref_039": (ARM_R, "forearm_R", "ivory"),
    "ref_031": (ARM_R, "gripper_R", "graphite"),
}

MATERIAL_BY_COLLECTION = {
    BASE: "ivory",
    WAIST: "graphite",
    TORSO: "ivory",
    HEAD: "ivory",
    ARM_L: "ivory",
    ARM_R: "ivory",
}


# --------------------------------------------------------------------------
def _collection(name, parent=None):
    coll = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    parent = parent or bpy.context.scene.collection
    if coll.name not in {c.name for c in parent.children}:
        parent.children.link(coll)
    return coll


def _assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for poly in obj.data.polygons[:1]:
        poly.material_index = 0
    obj.color = mat.diffuse_color


def apply_parts(mats):
    root = _collection("GALAHAD")
    colls = {name: _collection(name, root) for name in
             (BASE, WAIST, TORSO, HEAD, ARM_L, ARM_R)}
    unmapped = []
    for obj in list(bpy.data.objects):
        if obj.type != "MESH":
            continue
        if any(c.name == "99_STUDIO" for c in obj.users_collection):
            continue
        entry = PART_MAP.get(obj.name)
        if entry is None:
            unmapped.append(obj.name)
            entry = (BASE, obj.name, MATERIAL_BY_COLLECTION[BASE])
        coll_name, new_name, mat_key = entry
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        colls[coll_name].objects.link(obj)
        obj.name = new_name
        obj.data.name = new_name + "_mesh"
        _assign(obj, mats[mat_key])
        obj.data.polygons.foreach_set("use_smooth", [True] * len(obj.data.polygons))
        obj.data.update()
    return colls, unmapped


# --------------------------------------------------------------------------
# Rig: 14 articulation joints + 2 tread drives, matching the master prompt.
# All coordinates are the parked-pose joint pivots in millimetres.
# --------------------------------------------------------------------------
BONES = [
    # name, head, tail, parent
    ("base_link", (0, 0, 22), (0, 0, 46), None),
    ("waist_yaw", (0, 0, 80), (0, 0, 92), "base_link"),
    ("waist_pitch", (0, -4, 92), (0, -4, 112), "waist_yaw"),
    ("torso", (0, -4, 112), (0, -4, 176), "waist_pitch"),
    ("head_pan", (0, -2, 186), (0, -2, 200), "torso"),
    ("head_tilt", (0, -2, 200), (0, -2, 214), "head_pan"),
    ("shoulder_yaw_L", (-26, -4, 168), (-42, -4, 168), "torso"),
    ("shoulder_pitch_L", (-52, -4, 168), (-63, -4, 148), "shoulder_yaw_L"),
    ("elbow_L", (-70, -6, 122), (-76, -6, 104), "shoulder_pitch_L"),
    ("wrist_L", (-80, -8, 96), (-82, -10, 84), "elbow_L"),
    ("gripper_L", (-83, -12, 76), (-83, -12, 52), "wrist_L"),
    ("shoulder_yaw_R", (26, -4, 168), (42, -4, 168), "torso"),
    ("shoulder_pitch_R", (52, -4, 168), (63, -4, 148), "shoulder_yaw_R"),
    ("elbow_R", (70, -6, 122), (76, -6, 104), "shoulder_pitch_R"),
    ("wrist_R", (80, -8, 96), (82, -10, 84), "elbow_R"),
    ("gripper_R", (83, -12, 76), (83, -12, 52), "wrist_R"),
    ("tread_L", (0, -12, 25), (0, 12, 25), "base_link"),
    ("tread_R", (0, -12, 25), (0, 12, 25), "base_link"),
]

# Which bone each subsystem rides on (parked pose).
BONE_FOR_COLLECTION = {
    BASE: "base_link",
    WAIST: "waist_yaw",
    TORSO: "torso",
    HEAD: "head_tilt",
    ARM_L: "shoulder_pitch_L",
    ARM_R: "shoulder_pitch_R",
}

# Finer per-part bones for the arm chains so the elbow/wrist can pose.
PART_BONE = {
    "shoulder_L": "shoulder_pitch_L", "shoulder_joint_L": "shoulder_pitch_L",
    "shoulder_disc_L": "shoulder_pitch_L", "upperarm_L": "shoulder_pitch_L",
    "upperarm_inner_L": "shoulder_pitch_L",
    "elbow_housing_L": "elbow_L", "elbow_disc_L": "elbow_L",
    "forearm_L": "elbow_L", "forearm_inner_L": "elbow_L",
    "wrist_joint_L": "wrist_L", "wrist_disc_L": "wrist_L", "wrist_cuff_L": "wrist_L",
    "gripper_L": "gripper_L",
    "shoulder_R": "shoulder_pitch_R", "upperarm_R": "shoulder_pitch_R",
    "upperarm_inner_R": "shoulder_pitch_R", "forearm_R": "shoulder_pitch_R",
    "elbow_housing_R": "elbow_R",
    "shoulder_joint_R": "wrist_R",
    "gripper_R": "gripper_R",
}


def build_rig():
    arm_data = bpy.data.armatures.get("GalahadRig") or bpy.data.armatures.new("GalahadRig")
    rig = bpy.data.objects.get("GalahadRig")
    if rig is None:
        rig = bpy.data.objects.new("GalahadRig", arm_data)
    rig_col = _collection("00_RIG")
    if rig.name not in rig_col.objects:
        for c in list(rig.users_collection):
            c.objects.unlink(rig)
        rig_col.objects.link(rig)

    if bpy.context.view_layer.objects.active is not rig:
        bpy.context.view_layer.objects.active = rig
    for b in list(arm_data.bones):
        arm_data.bones.remove(b)

    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    created = {}
    for name, head, tail, parent in BONES:
        eb = arm_data.edit_bones.new(name)
        eb.head = Vector(head)
        eb.tail = Vector(tail)
        eb.use_connect = False
        created[name] = eb
    for name, head, tail, parent in BONES:
        if parent:
            created[name].parent = created[parent]
    bpy.ops.object.mode_set(mode="OBJECT")

    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"
    rig.show_in_front = True
    arm_data.display_type = "OCTAHEDRAL"
    return rig


def bind_to_rig(rig, colls):
    """Rigid skinning: one vertex group at weight 1 + an Armature modifier.

    The rest pose equals the built pose, so binding cannot move geometry, and
    animating a bone moves exactly the parts assigned to it.
    """
    rig.matrix_world = Matrix.Identity(4)
    bound = 0
    for coll_name, default_bone in BONE_FOR_COLLECTION.items():
        for obj in colls[coll_name].objects:
            bone_name = PART_BONE.get(obj.name, default_bone)
            if bone_name not in rig.data.bones:
                bone_name = default_bone
            for vg in list(obj.vertex_groups):
                obj.vertex_groups.remove(vg)
            vg = obj.vertex_groups.new(name=bone_name)
            vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
            mod = next((m for m in obj.modifiers if m.type == "ARMATURE"), None)
            if mod is None:
                mod = obj.modifiers.new("Armature", "ARMATURE")
            mod.object = rig
            mod.use_vertex_groups = True
            mod.use_bone_envelopes = False
            if obj.parent != rig:
                obj.parent = rig
                obj.matrix_parent_inverse = Matrix.Identity(4)
            bound += 1
    return bound



# --------------------------------------------------------------------------
def make_scene_units():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.render.fps = 30


def add_ground(mats):
    if bpy.data.objects.get("StudioFloor"):
        return bpy.data.objects["StudioFloor"]
    me = bpy.data.meshes.new("StudioFloor")
    s = 900.0
    me.from_pydata([(-s, -s, -0.6), (s, -s, -0.6), (s, s, -0.6), (-s, s, -0.6)], [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new("StudioFloor", me)
    ob.data.materials.append(mats["floor"])
    _collection("99_STUDIO").objects.link(ob)
    return ob


def add_chest_ui(mats):
    """Screen text sitting just proud of the chest bezel (front is -Y)."""
    for name in ("UI_LAN", "UI_BATT", "UI_WIFI"):
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
    specs = [
        ("UI_LAN", "LAN", -6.0, -37.9, 158.5, 4.4),
        ("UI_BATT", "A 82%   B 79%", 0.0, -37.9, 151.0, 3.0),
        ("UI_WIFI", ")))", 8.5, -37.9, 159.5, 3.2),
    ]
    objs = []
    for name, body, x, y, z, size in specs:
        cu = bpy.data.curves.new(name, type="FONT")
        cu.body = body
        cu.size = size
        cu.align_x = "CENTER"
        cu.align_y = "CENTER"
        cu.extrude = 0.05
        ob = bpy.data.objects.new(name, cu)
        ob.location = (x, y, z)
        ob.rotation_euler = (math.radians(90), 0, 0)
        ob.data.materials.append(mats["led"])
        _collection("99_STUDIO").objects.link(ob)
        objs.append(ob)
    return objs


def add_head_led(mats):
    old = bpy.data.objects.get("HeadLED")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    me = bpy.data.meshes.new("HeadLED")
    w, h = 8.0, 1.6
    verts = [(-w, -53.4, 213.5 - h), (w, -53.4, 213.5 - h), (w, -53.4, 213.5 + h), (-w, -53.4, 213.5 + h)]
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new("HeadLED", me)
    ob.data.materials.append(mats["led"])
    _collection("99_STUDIO").objects.link(ob)
    return ob


def add_studio_lights():
    """Neutral product-studio rig: sun key/fill/rim plus a soft world dome."""
    suns = {
        "KeyLight": ((-0.55, -0.75, 0.95), 3.4, 0.09),
        "FillLight": ((0.75, -0.55, 0.35), 1.1, 0.30),
        "RimLight": ((0.15, 0.85, 0.55), 2.0, 0.18),
        "TopLight": ((0.0, 0.05, 1.0), 0.7, 0.40),
    }
    for name, (direction, energy, angle) in suns.items():
        light = bpy.data.objects.get(name)
        if light is not None and light.data.type != "SUN":
            bpy.data.objects.remove(light, do_unlink=True)
            light = None
        if light is None:
            data = bpy.data.lights.new(name, type="SUN")
            light = bpy.data.objects.new(name, data)
            _collection("99_STUDIO").objects.link(light)
        light.data.energy = energy
        light.data.angle = angle
        d = Vector(direction).normalized()
        light.location = d * 800
        light.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()

    world = bpy.data.worlds.get("GalahadWorld") or bpy.data.worlds.new("GalahadWorld")
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = (0.62, 0.64, 0.68, 1.0)
    bg.inputs[1].default_value = 0.85
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    bpy.context.scene.world = world

    view = bpy.context.scene.view_settings
    try:
        view.view_transform = "AgX"
        view.look = "AgX - Medium High Contrast"
    except TypeError:
        view.view_transform = "Filmic"
    view.exposure = 0.35


def add_cylinder(name, center, radius, depth, mat, axis="Z", segments=64):
    """Lightweight primitive built with bmesh-free maths (no operators needed)."""
    import numpy as np
    ang = np.linspace(0, 2 * np.pi, segments, endpoint=False)
    ring = np.stack([np.cos(ang) * radius, np.sin(ang) * radius], axis=1)
    verts = []
    for side in (-depth / 2.0, depth / 2.0):
        for u, v in ring:
            if axis == "Z":
                verts.append((u, v, side))
            elif axis == "X":
                verts.append((side, u, v))
            else:
                verts.append((u, side, v))
    n = segments
    c0 = len(verts)
    verts.append((0, 0, -depth / 2.0) if axis == "Z" else
                 ((-depth / 2.0, 0, 0) if axis == "X" else (0, -depth / 2.0, 0)))
    c1 = len(verts)
    verts.append((0, 0, depth / 2.0) if axis == "Z" else
                 ((depth / 2.0, 0, 0) if axis == "X" else (0, depth / 2.0, 0)))
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
        faces.append((c0, j, i))
        faces.append((c1, n + i, n + j))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = center
    ob.data.materials.append(mat)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def add_head_discs(mats, colls):
    """Brass shoulder-style discs on both cheeks of the head, as in the reference."""
    made = []
    for side, x in (("L", -40.0), ("R", 39.0)):
        name = "head_brass_disc_" + side
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        ob = add_cylinder(name, (x, -18.0, 219.0), 14.0, 3.0, mats["brass"], axis="X")
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        colls[HEAD].objects.link(ob)
        made.append(ob)
    return made


def recolor_hip(mats, z_max=109.0):
    """The torso shell mesh also carries the hip gimbal; paint that graphite."""
    obj = bpy.data.objects.get("torso_shell")
    if obj is None:
        return 0
    mat = mats["graphite"]
    if mat.name not in [m.name for m in obj.data.materials if m]:
        obj.data.materials.append(mat)
    idx = [i for i, m in enumerate(obj.data.materials) if m and m.name == mat.name][0]
    co = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    count = 0
    for poly in obj.data.polygons:
        z = co[poly.vertices].mean(axis=0)[2]
        if z < z_max:
            poly.material_index = idx
            count += 1
    obj.data.update()
    return count


def _bbox_center(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        return None
    co = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    lo, hi = co.min(axis=0), co.max(axis=0)
    return (lo + hi) / 2.0, lo, hi


def add_wheel_hubs(mats, colls):
    """Brass hub caps centred on the real sprocket geometry."""
    made = []
    for src, tag in (("drive_motor_L", "front_L"), ("drive_motor_R", "front_R"),
                     ("wheel_rear_L", "rear_L"), ("wheel_rear_R", "rear_R")):
        info = _bbox_center(src)
        if info is None:
            continue
        ctr, lo, hi = info
        outer = hi[0] if "_R" in tag else lo[0]
        x = outer + (-0.3 if "_R" in tag else 0.3)
        name = "wheel_hub_" + tag
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        ob = add_cylinder(name, (x, ctr[1], ctr[2]), 8.0, 1.6, mats["brass"], axis="X", segments=48)
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        colls[BASE].objects.link(ob)
        made.append(ob)
    return made


def shade_auto_smooth(angle_deg=38.0):
    """Crisp hard-surface shading: sharp edges above the angle threshold."""
    meshes = [o for o in bpy.data.objects if o.type == "MESH"
              and o.name not in ("StudioFloor",) and o.parent and o.parent.name == "GalahadRig"]
    if not meshes:
        return 0
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(angle_deg))
    except (AttributeError, RuntimeError):
        for obj in meshes:
            mod = obj.modifiers.new("EdgeSplit", "EDGE_SPLIT")
            mod.split_angle = math.radians(angle_deg)
            mod.use_edge_angle = True
    for obj in meshes:
        obj.select_set(False)
    return len(meshes)



def reset_geometry(root_name="GALAHAD"):
    """Delete built collections and the rig so a rebuild starts clean."""
    for name in ("Cube", "Camera", "Light"):
        obj = bpy.data.objects.get(name)
        if obj is not None and not obj.users_collection:
            bpy.data.objects.remove(obj, do_unlink=True)
        elif obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)
    old = bpy.data.collections.get(root_name)
    if old:
        for obj in list(old.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for child in list(old.children):
            bpy.data.collections.remove(child)
        bpy.data.collections.remove(old)
    rig = bpy.data.objects.get("GalahadRig")
    if rig:
        bpy.data.objects.remove(rig, do_unlink=True)
    arm = bpy.data.armatures.get("GalahadRig")
    if arm:
        bpy.data.armatures.remove(arm)
    # stray source meshes from a previous import
    for obj in list(bpy.data.objects):
        if obj.name.startswith("ref_"):
            bpy.data.objects.remove(obj, do_unlink=True)


def import_source(root):
    import import_3mf
    src = root + "\\reference\\humanoid robot 3d model.3mf"
    tmp = _collection("90_SOURCE")
    info = import_3mf.import_reference(src)
    for obj in list(tmp.objects):
        pass
    # centre X/Y on origin, sit on Z=0, scale to 240 mm overall height
    import numpy as np
    lo = np.array([1e9, 1e9, 1e9])
    hi = -lo.copy()
    for obj in info["objects"]:
        co = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
        obj.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        lo = np.minimum(lo, co.min(axis=0))
        hi = np.maximum(hi, co.max(axis=0))
    shift = Matrix.Translation((-(lo[0] + hi[0]) / 2.0, -(lo[1] + hi[1]) / 2.0, -lo[2]))
    for obj in info["objects"]:
        obj.data.transform(shift)
    return info


def build_scene(verbose=True, reimport=True, root=None):
    root = root or __file__.rsplit("\\blender\\scripts\\", 1)[0]
    mats = galahad_materials.build_library()
    make_scene_units()
    if reimport:
        reset_geometry()
        import_source(root)
    colls, unmapped = apply_parts(mats)
    add_head_discs(mats, colls)
    add_wheel_hubs(mats, colls)
    rig = build_rig()
    bound = bind_to_rig(rig, colls)
    hip = recolor_hip(mats)
    smooth = shade_auto_smooth()
    add_ground(mats)
    add_studio_lights()
    add_chest_ui(mats)
    add_head_led(mats)
    if verbose:
        counts = {k: len(v.objects) for k, v in colls.items()}
        print("PARTS", counts, "BOUND", bound, "HIPFACES", hip, "SMOOTH", smooth, "UNMAPPED", unmapped)
    return {"collections": colls, "rig": rig, "materials": mats, "unmapped": unmapped}

