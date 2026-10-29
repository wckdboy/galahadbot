# Meshes

The URDF currently uses box primitives for visuals and collisions so the package
stays small and clones quickly. The authoritative high-fidelity geometry is:

- `blender/galahad.glb` — 1.9 M triangles, full material set, 93 parts
- `blender/galahad.blend` — source scene with rig, collections and materials

## Exporting per-link meshes

Each part in the .blend is rigidly bound to one bone by a single vertex group,
so a per-link export is a group-by-vertex-group operation:

```python
for bone in ("base_link", "torso", "head_tilt", "shoulder_pitch_L", ...):
    objs = [o for o in meshes if o.vertex_groups[0].name == bone]
    # duplicate, join, decimate to ~30 %, export STL/DAE to meshes/<bone>.<ext>
```

Then in `urdf/galahad.urdf` swap each `<box>` for a `<mesh filename="..."/>`.
Keep collision meshes coarser than visual meshes — do not collide against the
1.9 M-triangle cosmetic shells.
