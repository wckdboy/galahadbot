# Joint limits

Supervisory limits, shared by ros2_control and the MuJoCo model.

These are **design targets**, not measurements. They come from the engineering
brief plus CAD clearance, and must be replaced by bench-characterised values
before the robot is driven with a payload.

| Joint | ID | Actuator | Lower (deg) | Upper (deg) | Vel (deg/s) | Effort (N·m) |
|---|---|---|---|---|---|---|
| waist_yaw | 01 | XC330-M288 | -90 | 90 | 20 | 0.93 |
| waist_pitch | 02 | XC330-M288 | -20 | 20 | 15 | 0.93 |
| head_pan | 03 | XL330-M288 | -80 | 80 | 60 | 0.52 |
| head_tilt | 04 | XL330-M288 | -25 | 35 | 60 | 0.52 |
| shoulder_yaw_L | 05 | XC330-M288 | -80 | 80 | 40 | 0.93 |
| shoulder_pitch_L | 06 | XC330-M288 | -100 | 95 | 40 | 0.93 |
| elbow_L | 07 | XC330-M288 | -120 | 90 | 40 | 0.93 |
| wrist_L | 08 | XL330-M288 | -90 | 90 | 60 | 0.52 |
| gripper_L | 09 | XL330-M288 | 0 | 55 | 40 | 0.52 |
| shoulder_yaw_R | 10 | XC330-M288 | -80 | 80 | 40 | 0.93 |
| shoulder_pitch_R | 11 | XC330-M288 | -100 | 95 | 40 | 0.93 |
| elbow_R | 12 | XC330-M288 | -120 | 90 | 40 | 0.93 |
| wrist_R | 13 | XL330-M288 | -90 | 90 | 60 | 0.52 |
| gripper_R | 14 | XL330-M288 | 0 | 55 | 40 | 0.52 |

Effort values are the manufacturer stall torque at the rated 5 V rail. They are
**not** continuous-duty limits: the supervisory layer should cap sustained
effort at roughly 30 % of stall until thermal data exists.

The waist-pitch axis is the critical feasibility gate described in the brief.
Do not treat 0.93 N·m as permission to lean the torso with both arms extended.
