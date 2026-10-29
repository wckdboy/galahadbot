# Blender source

`galahad.blend` is the authoritative CAD scene. `galahad.glb` is the portable
export used for viewers, the web and game engines.

- Blender 5.2 (4.2+ should work; EEVEE enum names differ before 5.0 and
  `render_utils.pick_engine()` handles that)
- Scene units: millimetres, 1 unit = 1 mm
- 93 mesh parts, 6 subsystem collections, 18-bone rig, `99_STUDIO` for lights and
  camera, `00_RIG` for the armature

## Scripts

| File | Purpose |
|---|---|
| `scripts/import_3mf.py` | 3MF → Blender meshes without an addon |
| `scripts/build_galahad.py` | materials, naming, collections, rig, studio, UI |
| `scripts/build_from_scratch.py` | headless full rebuild |
| `scripts/galahad_materials.py` | material library |
| `scripts/render_views.py` | turnaround from any saved .blend |
| `scripts/final_renders.py` | deliverable renders + GLB/FBX export |
| `scripts/render_utils.py` | camera, lights, engine selection helpers |

## Commands

```bash
# rebuild the scene from the reference mesh
blender -b -P blender/scripts/build_from_scratch.py

# re-render and re-export
blender -b blender/galahad.blend -P blender/scripts/final_renders.py

# quick turntable of any file
blender -b blender/galahad.blend -P blender/scripts/render_views.py -- renders shot
```

## Posing

Select `GalahadRig`, enter Pose Mode and rotate the joint bones. Every part is
rigidly weighted to exactly one bone, so the mesh cannot shear. The parked pose
is the rest pose.

After moving a joint, re-export the joint map and regenerate the URDF:

```python
# in Blender's Python console
import bpy, json
rig = bpy.data.objects["GalahadRig"]
json.dump([{"name": b.name, "head_mm": list(b.head_local), "tail_mm": list(b.tail_local),
            "parent": b.parent.name if b.parent else None} for b in rig.data.bones],
          open("docs/joint_map.json", "w"), indent=2)
```

```bash
python tools/gen_urdf.py
```
