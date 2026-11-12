"""Set per-joint actuator force limits on an exported MJCF.

Polykrom writes one global `effort` for joints that no *library* servo drives.
Galahad's DYNAMIXEL XC330/XL330 are not in the parts library, so the export uses
envelopes and every actuator gets the same default. This restores the real
datasheet limits, per joint.

    python tools/patch_mjcf.py design/galahad.mjcf [--scale 0.3]
"""
import argparse
import sys
import xml.etree.ElementTree as ET

# ROBOTIS datasheet stall torque at 5 V, N m.
LIMITS = {
    "waist_yaw": 0.93, "waist_pitch": 0.93,
    "shoulder_yaw_L": 0.93, "shoulder_pitch_L": 0.93, "elbow_L": 0.93,
    "shoulder_yaw_R": 0.93, "shoulder_pitch_R": 0.93, "elbow_R": 0.93,
    "head_pan": 0.52, "head_tilt": 0.52,
    "wrist_L": 0.52, "gripper_L": 0.52,
    "wrist_R": 0.52, "gripper_R": 0.52,
    # Pololu 100:1 HPCB 6 V: 1.6 kg cm extrapolated stall torque
    "tread_L_drive": 0.157, "tread_R_drive": 0.157,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="multiply every limit (0.3 = sustained-duty cap)")
    args = ap.parse_args()

    tree = ET.parse(args.model)
    root = tree.getroot()
    actuator = root.find("actuator")
    if actuator is None:
        print("no <actuator> section", file=sys.stderr)
        return 1

    patched, missing = [], []
    for el in actuator:
        joint = el.get("joint")
        limit = LIMITS.get(joint)
        if limit is None:
            missing.append(joint)
            continue
        value = limit * args.scale
        el.set("forcerange", f"{-value:.4f} {value:.4f}")
        patched.append((joint, value))

    tree.write(args.model, encoding="utf-8", xml_declaration=True)
    print(f"patched {len(patched)} actuators in {args.model}")
    for joint, value in patched:
        print(f"  {joint:20s} {value:.3f} N m")
    if missing:
        print("WARNING: no datasheet limit for:", ", ".join(map(str, missing)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
