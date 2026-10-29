# tools

## `gen_urdf.py`

Reads `docs/joint_map.json` (exported from the Blender rig) and writes
`ros2_ws/src/galahad_description/urdf/galahad.urdf`.

```bash
python tools/gen_urdf.py
```

Joint origins are millimetre-exact from CAD. Visuals are approximating boxes so
the package stays small; masses and limits are engineering estimates and are
flagged as such in the generated file header.

## `blender_bridge_addon.py`

A loopback-only socket bridge (`127.0.0.1:9876`) that lets an MCP server run
Python inside a live Blender session.

```bash
blender --python tools/start_bridge.py
```

Difference from the upstream Niobium bridge: commands are dispatched to
Blender's **main thread** through `bpy.app.timers`. Operator calls
(`bpy.ops.render.render`, `bpy.ops.object.mode_set`, imports) are only legal
there. Called from the socket worker thread they abort and tear down the server,
which presents as a Blender "crash" even though the process is still alive.

Protocol (unchanged):

```json
{"type": "ping"}
{"type": "get_scene"}
{"type": "execute", "code": "bpy.data.objects.keys()"}
```
