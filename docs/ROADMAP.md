# Roadmap

Completion is defined by evidence, not by a render. Each milestone below states
what exists, what has actually been run, and what is still open.

## M0 — Compatibility audit and budget

- [x] Actuator and interface compatibility reviewed against datasheets
- [x] Initial mass, power and cost budgets drafted
- [x] 14-joint kinematic tree defined
- [x] Ranked risk list (see below)
- [ ] Distributor stock and Denmark delivered pricing confirmed

## M1 — CAD, masses, kinematics — **current**

- [x] Full 93-part CAD scene with materials and subsystem collections
- [x] 18-bone armature, rigid skinning, parked pose preserved
- [x] URDF generated from the rig (18 links, 14 revolute, 2 tread, 1 fixed)
- [x] Turnaround and hero renders
- [x] Parked envelope measured: 194.6 × 186.1 × 240.0 mm
- [ ] Mass and inertia measured from the first print set
- [ ] Self-collision sweep across 1 000 sampled poses
- [ ] Cable service loops and screw-tool access verified in CAD

## M2 — Bench proof of the control chain

- [ ] One XC330 and one XL330: firmware, ID, baud, direction, zero, watchdog
- [ ] Teensy 4.1 encoder decode and PWM at 500 Hz
- [ ] U2D2 bus timing with all 14 devices
- [ ] Framed USB serial protocol with CRC and heartbeats

## M3 — Calibrated tread drive

- [ ] Straight-line and turn tests on hard floor, desk and low-pile carpet
- [ ] Odometry error under 5 % per metre, heading under 10° per turn
- [ ] Current, temperature and derailment limits at final mass

## M4 — Arm and waist mockup

- [ ] Worst-case gravity moment held for ten minutes; temperature logged
- [ ] Reach and jaw clearance measured against a 20 g block
- [ ] Support-polygon margin computed and verified

## M5 — Full assembly

- [ ] 14 joints moving under current/velocity limits
- [ ] Coordinated named motion sequences while stationary

## M6 — Supervised pickup

- [ ] 20 g floor pickup, 50 trials in simulation, then physically
- [ ] Failure handling: dropped object, jam, retreat

## M7 — Voice, chest UI, co-work

- [ ] Wake word and barge-in with treads and servos running
- [ ] Local supervisor survives network loss
- [ ] Cloud model cannot bypass action limits

## M8 — Dual-input exchange (optional)

- [ ] Per-cell protection validated
- [ ] 50 A/B swap cycles under supported load

## M9 — Isaac and dock-assisted exchange (optional)

## Ranked risks

1. **Waist pitch torque and thermal margin** — 0.265 N·m static at the target
   mass is 28 % of stall, before dynamics. Gate for the whole torso design.
2. **Depth envelope** — 186 mm against a 145–180 mm target band.
3. **Servo rail current** — 23.2 A simultaneous stall versus a 15 A-class
   regulator; scheduling and fault handling must be real.
4. **Track capability at final mass** — 330 rpm no-load is far too fast and the
   100:1 gearbox may not survive turn-in-place.
5. **Cliff sensing latency** — the stop budget must include overhang, sensor
   period, scheduling, braking and slip.
6. **Audio in a small torso** — the mic array may not fit the intended head.
