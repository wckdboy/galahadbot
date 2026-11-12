"""Generate the Galahad Polykrom design script.

Units: millimetres, degrees. +X forward, +Y left, +Z up. Ground is z = 0.

Emits design/galahad.json, a command list for `polykrom-cli run`. Every
dimension comes from P, so the whole robot is parametric.

    python tools/build_polykrom.py
    polykrom-cli run design/galahad.json

Masses: Polykrom derives them from modelled volume x material density. Real
printed shells are 2.5 mm walls; modelling them as solids would overstate mass
by ~4x, so shell-like parts use an "effective density" material chosen so the
solid volume yields the measured mass of the real part. This is the same
convention the TinyRex design used for bought envelopes, and it is flagged in
docs/SIM2REAL.md.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "design", "galahad.json")

P = {
    # ground running gear
    "tread_len": 124.0, "tread_h": 39.0, "tread_w": 14.6, "tread_y": 52.0,
    "sprocket_r": 19.5, "sprocket_dx": 42.5,
    # base
    "base_l": 120.0, "base_w": 88.0, "base_h": 36.0, "base_z": 4.0,
    "deck_l": 128.0, "deck_w": 88.0, "deck_h": 5.0,
    "batt_l": 60.0, "batt_w": 30.0, "batt_h": 22.0,
    # waist
    "tt_r": 30.0, "tt_h": 13.0, "waist_z0": 45.0,
    "yaw_pivot_z": 51.5,
    "pitch_pivot_z": 70.0,
    # torso
    "torso_l": 100.0, "torso_w": 70.0, "torso_h": 102.0, "torso_z0": 82.0,
    # neck + head
    "neck_r": 13.0, "neck_z0": 184.0, "neck_h": 14.0,
    "pan_z": 191.0, "tilt_z": 200.0,
    "head_l": 62.0, "head_w": 96.0, "head_h": 38.0, "head_z0": 198.0,
    # arms
    "shoulder_pivot_y": 46.0, "shoulder_pivot_z": 170.0,
    "arm_y": 78.0,
    "shoulder_pitch_z": 166.0,
    "elbow_z": 120.0,
    "wrist_z": 84.0,
    "grip_z": 60.0,
}

CMDS = []


def cmd(command, **params):
    CMDS.append({"command": command, "params": params})


def box(name, l, w, h, center, body=None):
    cmd("solid.box", length=l, width=w, height=h, center=center,
        name=name, body_name=body or name)


def cyl(name, r, h, base, axis="Z", body=None, join=None):
    params = dict(radius=r, height=h, base=base, axis=axis,
                  name=name, body_name=body or name)
    if join:
        params["operation"] = "join"
        params["targets"] = [join]
    cmd("solid.cylinder", **params)


def part(name):
    """Start a new top-level component (one rigid link) and make it active."""
    cmd("component.create", name=name, parent=0, activate=True)


def joint(name, kind, a_occ, b_occ, point, axis, limits=None, flip=True):
    a = {"point": point, "z": axis}
    if a_occ is not None:
        a["occurrence"] = a_occ
    p = {
        "type": kind,
        "a": a,
        "b": {"occurrence": b_occ, "point": point, "z": axis},
        "name": name,
        "flip": flip,
    }
    if limits is not None:
        p["limits"] = [list(limits)]
    cmd("joint.create", **p)


def build():
    cmd("file.new")
    cmd("document.units", units="mm")
    cmd("component.rename", component=0, name="base")

    # density g/cm3; shell-like solids use effective densities (see docstring)
    cmd("material.create", name="Galahad Ivory", density_g_cm3=0.40, color="#EDE4D1")
    cmd("material.create", name="Galahad Navy", density_g_cm3=0.40, color="#2A3346")
    cmd("material.create", name="Galahad Graphite", density_g_cm3=0.60, color="#22252B")
    cmd("material.create", name="Galahad Tread", density_g_cm3=0.24, color="#141518")
    cmd("material.create", name="Galahad Battery", density_g_cm3=1.92, color="#3A4356")
    cmd("material.create", name="Galahad Electronics", density_g_cm3=1.90, color="#2E6B45")
    cmd("material.create", name="Galahad Brass", density_g_cm3=1.05, color="#C9A050")
    # arm links carry their DYNAMIXEL inside; effective densities give the real link mass
    cmd("material.create", name="Galahad Arm Shoulder", density_g_cm3=1.10, color="#EDE4D1")
    cmd("material.create", name="Galahad Arm Upper", density_g_cm3=3.00, color="#EDE4D1")
    cmd("material.create", name="Galahad Arm Lower", density_g_cm3=3.80, color="#EDE4D1")
    cmd("material.create", name="Galahad Hand", density_g_cm3=2.00, color="#EDE4D1")
    cmd("material.create", name="Galahad Jaw", density_g_cm3=3.40, color="#22252B")

    # ---- base (the root component itself) -------------------------------
    box("chassis", P["base_l"], P["base_w"], P["base_h"],
        (0, 0, P["base_z"] + P["base_h"] / 2))
    box("deck", P["deck_l"], P["deck_w"], P["deck_h"],
        (0, 0, P["base_z"] + P["base_h"] + P["deck_h"] / 2))
    box("bumper", 8, 76, 24, (P["base_l"] / 2 + 4, 0, 14))
    box("battery_A", P["batt_l"], P["batt_w"], P["batt_h"], (-34, 20, 26))
    box("battery_B", P["batt_l"], P["batt_w"], P["batt_h"], (-34, -20, 26))
    box("pcb_stack", 60, 50, 12, (-20, 0, 46))

    # ---- rear panel (own fixed link; also absorbs the exporter's first-child joint drop)
    part("rear_panel")
    box("rear_panel", 6, 76, 26, (-P["base_l"] / 2 - 3, 0, 18))

    # ---- treads --------------------------------------------------------
    for side, sign in (("L", 1), ("R", -1)):
        part(f"tread_{side}")
        box(f"track_bar_{side}", 85, P["tread_w"], P["tread_h"],
            (0, sign * P["tread_y"], P["tread_h"] / 2), body=f"track_{side}")
        for dx in (-P["sprocket_dx"], P["sprocket_dx"]):
            cyl(f"track_end_{side}_{int(dx)}", P["sprocket_r"], P["tread_w"],
                (dx, sign * P["tread_y"], P["tread_h"] / 2), axis="Y",
                body=f"track_{side}", join=f"track_{side}")

    # ---- waist ---------------------------------------------------------
    part("waist")
    cyl("turntable", P["tt_r"], P["tt_h"], (0, 0, P["waist_z0"]))
    box("waist_block", 44, 44, 24, (0, 0, P["waist_z0"] + P["tt_h"] + 12))

    # ---- torso ---------------------------------------------------------
    part("torso")
    box("torso_shell", P["torso_l"], P["torso_w"], P["torso_h"],
        (0, 0, P["torso_z0"] + P["torso_h"] / 2))
    box("chest_screen", 4, 46, 38, (P["torso_l"] / 2 + 2, 0, 146))
    box("chest_speaker", 4, 46, 24, (P["torso_l"] / 2 + 2, 0, 112))

    # ---- neck (pan) and head (tilt) ------------------------------------
    part("neck")
    cyl("neck_post", P["neck_r"], P["neck_h"], (0, 0, P["neck_z0"]))

    part("head")
    box("head_shell", P["head_l"], P["head_w"], P["head_h"],
        (0, 0, P["head_z0"] + P["head_h"] / 2))
    box("visor", 6, 84, 22, (P["head_l"] / 2 + 3, 0, 220))
    cyl("lens", 9, 5, (P["head_l"] / 2 + 5, 26, 220), axis="X")

    # ---- arms ----------------------------------------------------------
    for side, sign in (("L", 1), ("R", -1)):
        part(f"shoulder_{side}")
        box(f"shoulder_bracket_{side}", 30, 52, 24,
            (0, sign * 60, P["shoulder_pivot_z"]))
        box(f"shoulder_pad_{side}", 26, 12, 26,
            (0, sign * (P["shoulder_pivot_y"] + 10), P["shoulder_pivot_z"]))

        part(f"upperarm_{side}")
        box(f"upperarm_plate_{side}", 18, 18, 46,
            (0, sign * P["arm_y"], (P["shoulder_pitch_z"] + P["elbow_z"]) / 2))

        part(f"forearm_{side}")
        box(f"forearm_plate_{side}", 16, 14, 36,
            (0, sign * P["arm_y"], (P["elbow_z"] + P["wrist_z"]) / 2))

        part(f"hand_{side}")
        box(f"palm_{side}", 22, 28, 24,
            (0, sign * P["arm_y"], (P["wrist_z"] + P["grip_z"]) / 2))
        box(f"finger_fixed_{side}", 20, 10, 14,
            (9, sign * P["arm_y"], P["grip_z"] - 4))

        part(f"jaw_{side}")
        box(f"finger_moving_{side}", 20, 10, 14,
            (-9, sign * P["arm_y"], P["grip_z"] - 4))

    # ---- materials -----------------------------------------------------
    ivory = ["chassis", "deck", "torso_shell", "head_shell"]
    cmd("material.assign", material="Galahad Ivory", bodies=ivory)
    cmd("material.assign", material="Galahad Navy",
        bodies=["chest_speaker", "rear_panel"])
    cmd("material.assign", material="Galahad Graphite",
        bodies=["bumper", "waist_block", "visor", "lens"])
    cmd("material.assign", material="Galahad Tread", bodies=["track_L", "track_R"])
    cmd("material.assign", material="Galahad Battery", bodies=["battery_A", "battery_B"])
    cmd("material.assign", material="Galahad Electronics",
        bodies=["pcb_stack", "chest_screen"])
    cmd("material.assign", material="Galahad Brass", bodies=["turntable"])

    for side in ("L", "R"):
        cmd("material.assign", material="Galahad Arm Shoulder",
            bodies=[f"shoulder_bracket_{side}", f"shoulder_pad_{side}"])
        cmd("material.assign", material="Galahad Arm Upper", bodies=[f"upperarm_plate_{side}"])
        cmd("material.assign", material="Galahad Arm Lower", bodies=[f"forearm_plate_{side}"])
        cmd("material.assign", material="Galahad Hand",
            bodies=[f"palm_{side}", f"finger_fixed_{side}"])
        cmd("material.assign", material="Galahad Jaw", bodies=[f"finger_moving_{side}"])

    # ---- joints --------------------------------------------------------
    joint("rear_panel_weld", "rigid", 0, "rear_panel",
          (-P["base_l"] / 2 - 3, 0, 18), [1, 0, 0])

    for side, sign in (("L", 1), ("R", -1)):
        joint(f"tread_{side}_drive", "revolute", 0, f"tread_{side}",
              (P["sprocket_dx"], sign * P["tread_y"], P["tread_h"] / 2), [0, 1, 0])

    joint("waist_yaw", "revolute", 0, "waist",
          (0, 0, P["yaw_pivot_z"]), [0, 0, 1], limits=(-90, 90))
    joint("waist_pitch", "revolute", "waist", "torso",
          (0, 0, P["pitch_pivot_z"]), [0, 1, 0], limits=(-20, 20))
    joint("head_pan", "revolute", "torso", "neck",
          (0, 0, P["pan_z"]), [0, 0, 1], limits=(-80, 80))
    joint("head_tilt", "revolute", "neck", "head",
          (0, 0, P["tilt_z"]), [0, 1, 0], limits=(-25, 35))

    for side, sign in (("L", 1), ("R", -1)):
        joint(f"shoulder_yaw_{side}", "revolute", "torso", f"shoulder_{side}",
              (0, sign * P["shoulder_pivot_y"], P["shoulder_pivot_z"]), [0, 0, 1],
              limits=(-80, 80))
        joint(f"shoulder_pitch_{side}", "revolute", f"shoulder_{side}", f"upperarm_{side}",
              (0, sign * P["arm_y"], P["shoulder_pitch_z"]), [0, 1, 0],
              limits=(-100, 95))
        joint(f"elbow_{side}", "revolute", f"upperarm_{side}", f"forearm_{side}",
              (0, sign * P["arm_y"], P["elbow_z"]), [0, 1, 0], limits=(-120, 90))
        joint(f"wrist_{side}", "revolute", f"forearm_{side}", f"hand_{side}",
              (0, sign * P["arm_y"], P["wrist_z"]), [0, 1, 0], limits=(-90, 90))
        joint(f"gripper_{side}", "revolute", f"hand_{side}", f"jaw_{side}",
              (0, sign * P["arm_y"], P["grip_z"]), [1, 0, 0], limits=(0, 45))

    # base is the grounded root
    # base is the rooted component; floating export lets the sim drop it on the floor
    cmd("file.save_as", path="design/galahad.polykrom")
    moving = (["waist_yaw", "waist_pitch", "head_pan", "head_tilt"]
              + [f"{j}_{s}" for s in ("L", "R")
                 for j in ("shoulder_yaw", "shoulder_pitch", "elbow", "wrist", "gripper")]
              + ["tread_L_drive", "tread_R_drive"])
    cmd("file.export", path="design/galahad.mjcf", format="mjcf",
        floating=True, effort=1.0, actuated=moving)
    cmd("file.export", path="design/galahad.urdf", format="urdf", effort=1.0, velocity=3.0)


def main():
    build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"commands": CMDS}, fh, indent=1)
    print(f"wrote {OUT}: {len(CMDS)} commands")


if __name__ == "__main__":
    main()
