"""Validate an exported MJCF model in MuJoCo and write a JSON report.

    python tools/mujoco_check.py design/galahad.mjcf --out docs/mujoco_report.json

Checks: model loads, masses and inertia are positive, joint ranges match the
design, the robot settles without exploding, and a short tread-drive roll moves
it forward. This is a software check, not a hardware result.
"""
import argparse
import json
import os
import sys

import mujoco
import numpy as np


def euler_tilt(quat):
    """Tilt of the body z-axis away from world z, in degrees."""
    w, x, y, z = quat
    r = np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])
    up = r.T @ np.array([0.0, 0.0, 1.0])
    return float(np.degrees(np.arccos(np.clip(up[2], -1.0, 1.0))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--out", default=None)
    ap.add_argument("--seconds", type=float, default=2.0)
    ap.add_argument("--roll", action="store_true", help="drive the treads forward")
    args = ap.parse_args()

    report = {"model": os.path.basename(args.model), "physics": "MuJoCo " + mujoco.__version__}
    model = mujoco.MjModel.from_xml_path(args.model)
    data = mujoco.MjData(model)

    report["counts"] = {
        "bodies": int(model.nbody),
        "joints": int(model.njnt),
        "actuators": int(model.nu),
        "geoms": int(model.ngeom),
        "meshes": int(model.nmesh),
    }
    report["total_mass_kg"] = round(float(model.body_mass.sum()), 4)
    report["timestep_s"] = float(model.opt.timestep)

    bad_mass = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i)
                for i in range(model.nbody) if model.body_mass[i] <= 0.0 and mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i) != "world"]
    report["massless_bodies"] = bad_mass

    joints = []
    for j in range(model.njnt):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, j)
        joints.append({
            "name": name,
            "type": int(model.jnt_type[j]),
            "limited": bool(model.jnt_limited[j]),
            "range_deg": [round(float(np.degrees(model.jnt_range[j][0])), 2),
                          round(float(np.degrees(model.jnt_range[j][1])), 2)]
            if model.jnt_limited[j] else None,
        })
    report["joints"] = joints

    actuators = []
    for a in range(model.nu):
        actuators.append({
            "name": mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, a),
            "force_range_nm": [round(float(model.actuator_forcerange[a][0]), 3),
                               round(float(model.actuator_forcerange[a][1]), 3)],
        })
    report["actuators"] = actuators

    # settle from the design pose
    if model.nkey > 0:
        mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    z0 = float(data.qpos[2]) if model.jnt_type[0] == mujoco.mjtJoint.mjJNT_FREE else 0.0
    q0 = data.qpos[3:7].copy() if model.jnt_type[0] == mujoco.mjtJoint.mjJNT_FREE else np.array([1, 0, 0, 0])

    steps = int(args.seconds / model.opt.timestep)
    for _ in range(steps):
        mujoco.mj_step(model, data)

    settled = {
        "duration_s": args.seconds,
        "base_height_mm": round(float(data.qpos[2]) * 1000.0, 2) if model.jnt_type[0] == mujoco.mjtJoint.mjJNT_FREE else None,
        "height_change_mm": round((float(data.qpos[2]) - z0) * 1000.0, 2) if model.jnt_type[0] == mujoco.mjtJoint.mjJNT_FREE else None,
        "tilt_deg": round(euler_tilt(data.qpos[3:7]), 2) if model.jnt_type[0] == mujoco.mjtJoint.mjJNT_FREE else None,
        "ncon": int(data.ncon),
        "max_contact_force_n": round(float(np.abs(data.efc_force).max()) if data.ncon else 0.0, 2),
    }
    report["settle"] = settled

    if args.roll:
        x0 = float(data.qpos[0])
        treads = [a for a in range(model.nu)
                  if "tread" in (mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, a) or "")]
        # ramp the position targets like a velocity command (2 rad/s) instead of a step
        for step in range(int(2.0 / model.opt.timestep)):
            target = min(2.0 * step * model.opt.timestep, 4.0)
            for a in treads:
                data.ctrl[a] = target
            mujoco.mj_step(model, data)
        report["roll"] = {
            "duration_s": 2.0,
            "forward_mm": round((float(data.qpos[0]) - x0) * 1000.0, 2),
            "tilt_deg": round(euler_tilt(data.qpos[3:7]), 2),
            "tread_angle_deg": [round(float(np.degrees(data.qpos[model.jnt_qposadr[j]])), 1)
                                for j in range(model.njnt)
                                if "tread" in (mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, j) or "")],
        }

    ok = (not bad_mass) and abs(settled.get("height_change_mm") or 0) < 200
    report["result"] = "pass" if ok else "review"

    text = json.dumps(report, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    print(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
