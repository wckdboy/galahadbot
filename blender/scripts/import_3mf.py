"""Parse a 3MF (OPC zip) into Blender meshes without an addon.

Blender 5.2 ships no 3MF importer, so we read the core model XML directly.
The Galahad reference asset is a single 165 MB .model file with 87 objects.
"""
import re
import zipfile
from pathlib import Path

import bpy
import numpy as np

VERT_RE = re.compile(r'<vertex x="([-0-9.eE+]+)"\s+y="([-0-9.eE+]+)"\s+z="([-0-9.eE+]+)"')
TRI_RE = re.compile(r'<triangle v1="(\d+)"\s+v2="(\d+)"\s+v3="(\d+)"')
OBJ_RE = re.compile(r'<object id="(\d+)"[^>]*>')


def _model_xml(path):
    path = Path(path)
    if path.suffix.lower() == ".3mf":
        with zipfile.ZipFile(path) as zf:
            name = next(n for n in zf.namelist() if n.lower().endswith(".model"))
            return zf.read(name).decode("utf-8", "replace")
    return path.read_text(encoding="utf-8", errors="replace")


def parse(path):
    """Return {object_id: (verts Nx3 float32, tris Mx3 int32)} in file units."""
    text = _model_xml(path)
    starts = [(int(m.group(1)), m.start()) for m in OBJ_RE.finditer(text)]
    parts = {}
    for i, (oid, start) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else len(text)
        chunk = text[start:end]
        vm = re.search(r"<vertices>(.*?)</vertices>", chunk, re.S)
        tm = re.search(r"<triangles>(.*?)</triangles>", chunk, re.S)
        if not vm or not tm:
            continue
        verts = np.array(VERT_RE.findall(vm.group(1)), dtype=np.float32)
        tris = np.array(TRI_RE.findall(tm.group(1)), dtype=np.int32)
        if len(verts) and len(tris):
            parts[oid] = (verts, tris)
    return parts


def build_meshes(parts, collection, scale=1.0, offset=(0.0, 0.0, 0.0)):
    """Create one mesh object per 3MF object using the fast foreach_set path."""
    made = []
    for oid, (verts, tris) in sorted(parts.items()):
        me = bpy.data.meshes.new("ref_%03d" % oid)
        v = verts * scale + np.array(offset, dtype=np.float32)
        me.vertices.add(len(v))
        me.vertices.foreach_set("co", v.ravel())
        me.loops.add(len(tris) * 3)
        me.loops.foreach_set("vertex_index", tris.ravel())
        me.polygons.add(len(tris))
        me.polygons.foreach_set("loop_start", np.arange(0, len(tris) * 3, 3, dtype=np.int32))
        me.update(calc_edges=False)
        me.validate(verbose=False)
        ob = bpy.data.objects.new("ref_%03d" % oid, me)
        collection.objects.link(ob)
        made.append(ob)
    return made


def import_reference(path, collection_name="REF_3MF", target_height_mm=240.0, axis_z=2):
    parts = parse(path)
    allv = np.concatenate([v for v, t in parts.values()], axis=0)
    lo, hi = allv.min(axis=0), allv.max(axis=0)
    height = (hi - lo)[axis_z]
    scale = target_height_mm / float(height)
    offset = (-lo[0], -lo[1], -lo[2])
    coll = bpy.data.collections.get(collection_name) or bpy.data.collections.new(collection_name)
    if coll.name not in {c.name for c in bpy.context.scene.collection.children}:
        bpy.context.scene.collection.children.link(coll)
    made = build_meshes(parts, coll, scale=scale, offset=offset)
    return {
        "objects": made,
        "source_bbox_units": (hi - lo).tolist(),
        "scale": scale,
        "size_mm": ((hi - lo) * scale).tolist(),
    }
