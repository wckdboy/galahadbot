# Galahad specification

Every quantitative claim carries a tag:

- **[spec]** manufacturer specification
- **[calc]** derived by calculation here
- **[target]** engineering goal, not yet proven
- **[est]** estimate with no measurement behind it
- **[todo]** must be measured on hardware

## 1. Envelope and mass

| Item | Value | Tag |
|---|---|---|
| Parked height | 240.0 mm | [calc] from CAD |
| Parked width, arms folded | 194.6 mm | [calc] |
| Parked depth | 186.1 mm | [calc] — 6 mm over the 145–180 mm target band |
| Absolute limit | 250 × 250 × 250 mm | [target] |
| Track outside diameter | ≈39 mm | [spec] Pololu 3033, 35 mm sprocket + belt |
| Track width | 14.6 mm | [spec] |
| Sprocket axle spacing | ≈85 mm | [spec] |
| Ground clearance to chassis | ≈6 mm | [calc] |
| Total mass | 1.25 kg | [est] split of the 0.9–1.3 kg target |

### Mass budget [est]

| Subsystem | Mass |
|---|---|
| Base: chassis, 2 tracks, 2 gearmotors, 2 batteries, deck | 0.46 kg |
| Waist yaw + pitch blocks | 0.08 kg |
| Torso: shell, Pi 5, cooler, audio board, display, regulators | 0.30 kg |
| Head: shell, camera, ToF imager, neck | 0.105 kg |
| Two arms (shoulder → gripper) | 0.32 kg |

These are allocations, not measurements. The 14 actuators alone are 292 g of
that before horns, cables or brackets. **Recalculate after weighing the first
print set.**

## 2. Actuators

| Model | Qty | Size | Mass | Stall torque @5 V | Stall current @5 V |
|---|---|---|---|---|---|
| ROBOTIS XC330-M288-T | 8 | 20 × 34 × 26 mm | 23 g | 0.93 N·m | 1.80 A |
| ROBOTIS XL330-M288-T | 6 | 20 × 34 × 26 mm | 18 g | 0.52 N·m | 1.47 A |

[spec] Manufacturer datasheets. Use the **M288** (low-voltage) variant; the
T288 is the higher-voltage part and is a different product despite the `-T`
suffix meaning TTL on both.

Worst-case simultaneous stall: 8 × 1.80 + 6 × 1.47 = **23.22 A** on the 5 V
servo rail. The 15 A-class D24V150F5 cannot supply that. The controller must
schedule motion, bound simultaneous effort, and treat stall as a fault.

## 3. Joint table

| ID | Joint | Actuator | Axis | Range | Notes |
|---|---|---|---|---|---|
| 01 | waist_yaw | XC330 | Z | ±90° | cable-protected mechanical stop |
| 02 | waist_pitch | XC330 | X | ±20° | critical gate — see §6 |
| 03 | head_pan | XL330 | Z | ±80° | |
| 04 | head_tilt | XL330 | X | −25…+35° | |
| 05 | shoulder_yaw_L | XC330 | Z | ±80° | |
| 06 | shoulder_pitch_L | XC330 | Y | −100…+95° | |
| 07 | elbow_L | XC330 | Y | −120…+90° | |
| 08 | wrist_L | XL330 | Y | ±90° | |
| 09 | gripper_L | XL330 | Y | 0…55° | one actuator, parallel fingers |
| 10–14 | right arm | mirror of 05–09 | | | |

Passive elements that do **not** count as actuators: gripper finger linkages,
idler sprockets, support bearings.

Four positioning axes per arm cannot reach arbitrary 6-D poses. Plan position
plus a limited approach direction, and use base yaw and waist motion when needed.

## 4. Running gear

- Pololu 30T Track Set, item 3033 — two silicone tracks, sprockets, idlers [spec]
- 2 × Pololu 100:1 Micro Metal Gearmotor HPCB 6 V with 12 CPR encoder, item 5190 [spec]
  - 330 rpm no-load, 1.5 A extrapolated stall, 1.6 kg·cm extrapolated stall torque at 6 V
- 2 × Pololu DRV8838 carrier, item 2990 — 1.7 A continuous / 1.8 A peak nominal [spec]

330 rpm at the sprocket is far too fast for a desk. Enforce encoder velocity and
acceleration limits; consider 150:1 or 210:1 after measuring turn-in-place load.

## 5. Compute, sensing, interaction

| Function | Part |
|---|---|
| Primary compute | Raspberry Pi 5, 4 GB, high-endurance microSD, Active Cooler |
| Motion supervisor | PJRC Teensy 4.1 (3.3 V GPIO, not 5 V tolerant) |
| Actuator bus | ROBOTIS U2D2 (comms only — never servo power) |
| Vision | Raspberry Pi Camera Module 3 (standard autofocus) |
| Head depth | SparkFun VL53L5CX Qwiic ToF imager, SEN-18642 |
| Cliff/edge | 4 × Adafruit VL53L4CD, product 5396, downward at chassis corners |
| Obstacle | 2 × Adafruit VL53L1X, product 3967, fore and aft |
| Orientation | Adafruit BNO085, product 4754, SPI on the chassis (not the torso) |
| Chest display | Adafruit 1.3″ 240×240 ST7789, product 4313, SPI |
| Voice | Seeed reSpeaker XVF3800 USB 4-mic array + Visaton BF 32 (4 Ω, 2 W) |
| Power sensing | INA228-based pack monitoring, shunt to be selected |

Duplicate I2C addresses need a TCA9548A mux or controlled XSHUT addressing.
Sensor invalid/stale is **not** equivalent to clear space.

## 6. The waist-pitch gate

A 0.45 kg torso-and-head assembly with its centre of mass 60 mm ahead of the
hinge produces ≈0.265 N·m of static gravity moment [calc]. That is 28 % of the
XC330's 0.93 N·m stall rating — but stall torque is not a continuous rating, and
the moment grows with arm extension, acceleration and any payload.

Before mounting the full set: build the waist mockup, hang the real torso mass at
the real offset, and measure temperature and current over a ten-minute duty
cycle. If the margin fails, change leverage (move the hinge, counterweight,
torsion spring) or move to a larger actuator and re-budget mass, power and cost.

## 7. Power architecture

```
2 × Tattu 850 mAh 3S 45C (XT30)      11.1 V nominal, 12.6 V full
        │
        ├── D24V150F5  5 V / 15 A class ── fused, star-branched ── 14 × DYNAMIXEL
        ├── D24V50F5   5 V logic ── filters ── Pi 5 / audio / MCU
        └── D24V50F6   6 V ── 2 × DRV8838 ── tread motors
```

- 3S LiPo at 12.6 V must never reach low-voltage X330 servos or 6 V motors [spec]
- Two packs contain ≈18.87 Wh nominal; at 80 % usable that is ≈45 min at 20 W or
  ≈26 min at 35 W [calc] — examples, not measured runtime
- These are hobby LiPo packs, **not** protected smart batteries: per-cell
  protection, fusing, undervoltage handling and external balance charging are
  mandatory
- Buck converters are not energy sinks; torso lowering and motor braking can
  push the rail up. Scope it before trusting it.

## 8. Software stack (planned)

ROS 2 Jazzy on Ubuntu 24.04 arm64, `ros2_control` with DYNAMIXEL SDK over U2D2,
`joint_trajectory_controller` for arms/head/waist, `diff_drive_controller` for
the treads, MuJoCo as the primary regression simulator. Skid-steer tracks only
approximate differential drive — calibrate effective radius and separation.

The URDF here already matches the rig. `galahad_description` is the first package
of the planned workspace.
