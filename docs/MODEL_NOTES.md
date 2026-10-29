# Model notes — how the Blender scene was built

## Pipeline

```
reference/humanoid robot 3d model.3mf
        │  tools/blender_bridge_addon.py (MCP bridge, main-thread dispatch)
        ▼
blender/scripts/import_3mf.py      parse OPC/XML, 87 objects, 945 k vertices
        ▼
blender/scripts/build_galahad.py    centre, scale to 240 mm, materials,
        │                            collections, armature, rigid skinning,
        │                            studio, chest UI, brass details
        ▼
blender/galahad.blend               source scene
        ▼
blender/scripts/final_renders.py   6 ortho views + hero, GLB/FBX export
```

Everything is deterministic: deleting the `GALAHAD` collection and re-running
`build_scene()` rebuilds from the source mesh.

## Why the mesh is parsed by hand

Blender 5.2 ships no 3MF importer. `import_3mf.py` reads the core model XML out
of the OPC zip and builds meshes through `foreach_set`, which imports the
1.9 M-triangle asset in a few seconds instead of minutes.

## Materials

| Key | Colour | Use |
|---|---|---|
| `ivory` | `#EDE4D1` | printed shells, track guards |
| `navy` | `#2A3346` | service plates, deck, battery cartridges |
| `graphite` | `#22252B` | joint housings, sprockets, gimbal |
| `brass` | `#C9A050` | turntable, side bosses, hub caps, wrist rings |
| `rubber` | `#141518` | silicone treads |
| `led` | `#2E7BFF` emissive | head status bar, chest UI |
| `glass` | `#0B0E14` | camera lens, IR window |

Materials are Principled BSDF with coat on the shells. Shading uses auto-smooth
at 38° — without it the 1.9 M-triangle asset reads as melted plastic.

## Part mapping

87 source meshes were mapped to descriptive names and subsystems by position and
by ray-casting the rendered surface (see `PART_MAP` in `build_galahad.py`).
Ray-casting beats guessing: it is how the chest screen and speaker were found to
be swapped, and how the rear idler wheels were identified as ivory side plates.

Some source objects merge several real parts — `torso_shell` includes the hip
gimbal, so faces below z = 109 mm are re-assigned to graphite per-face.

## Rig

18 bones: base, treads, waist yaw/pitch, torso, head pan/tilt and five joints per
arm. Parts are rigidly skinned with a single vertex group at weight 1 plus an
Armature modifier, so the rest pose equals the built pose and binding cannot move
geometry.

`docs/joint_map.json` is exported from the same armature and is the input to
`tools/gen_urdf.py`, which keeps CAD and ROS transforms in sync.

## Known deviations from the reference renders

| Item | Status |
|---|---|
| Cable looms | Ivory in the source mesh; reference shows black braided hose. Needs a per-component re-material pass. |
| Right arm detail | The source arm has fewer distinct parts than the left; brass wrist ring placement is asymmetric. |
| Head side plates | Reference shows a clean brass disc; here a brass boss sits on an ivory plate. |
| Battery latches | Source geometry only; no spring, contact or retention feature modelled. |
| Fasteners | Surface detail only — no screw threads, insert bosses or torque features. |
| Internals | No Pi 5, Teensy, U2D2, regulators or wiring in CAD yet; the torso is an empty shell. |

## Bridge note

`tools/blender_bridge_addon.py` differs from the upstream Niobium bridge in one
important way: it marshals commands onto Blender's **main thread** with
`bpy.app.timers`. Blender's API is not thread-safe, and calling operators such as
`bpy.ops.render.render()` from the socket worker thread aborts the operation and
kills the socket server — which looks exactly like a crash.
