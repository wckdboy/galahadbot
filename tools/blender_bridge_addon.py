# blender_bridge_addon.py — local socket bridge for Galahad, based on the Niobium bridge.
#
# Difference from the original: commands are marshalled onto Blender's MAIN thread
# with bpy.app.timers, so bpy.ops.* (render, mode_set, import, save) is legal.
# Blender's API is not thread-safe; calling operators from the socket worker thread
# aborts the operation and tears down the socket server, which looks like a crash.
#
# Protocol unchanged: {"type": "ping" | "get_scene" | "execute", "code": "..."}
# Bound to 127.0.0.1:9876 only.

import io
import json
import socket
import threading
import traceback
from contextlib import redirect_stdout

import bpy

bl_info = {
    "name": "Galahad Blender Bridge",
    "author": "Galahad project",
    "version": (1, 1, 0),
    "blender": (4, 0, 0),
    "location": "127.0.0.1:9876",
    "description": "Main-thread-safe local bridge (no telemetry, loopback only).",
    "category": "Interface",
}

HOST = "127.0.0.1"
PORT = 9876

_server_thread = None
_running = False


def get_scene_info():
    return {
        "file": bpy.data.filepath,
        "objects": [o.name for o in bpy.data.objects],
        "meshes": [m.name for m in bpy.data.meshes],
        "armatures": [a.name for a in bpy.data.armatures],
        "materials": [m.name for m in bpy.data.materials],
        "collections": [c.name for c in bpy.data.collections],
        "object_count": len(bpy.data.objects),
    }


def _execute_now(code):
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            try:
                result = eval(code, {"bpy": bpy, "__builtins__": __builtins__})
            except SyntaxError:
                exec(compile(code, "<bridge>", "exec"), {"bpy": bpy, "__builtins__": __builtins__})
                result = None
        return {"ok": True, "result": repr(result), "stdout": buf.getvalue()}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "traceback": traceback.format_exc(),
                "stdout": buf.getvalue()}


def execute(code, timeout=600):
    """Run code on the main thread; block the worker until it finishes."""
    if threading.current_thread() is threading.main_thread():
        return _execute_now(code)

    box = {}
    done = threading.Event()

    def _run():
        try:
            box.update(_execute_now(code))
        finally:
            done.set()
        return None  # one-shot timer

    bpy.app.timers.register(_run, first_interval=0.0)
    if not done.wait(timeout):
        return {"ok": False, "error": "timeout waiting for Blender main thread"}
    return box


def _recv_all(conn):
    data = b""
    while True:
        chunk = conn.recv(65536)
        if not chunk:
            break
        data += chunk
        if len(chunk) < 65536:
            break
    return data


def handle(conn):
    try:
        req = json.loads(_recv_all(conn).decode("utf-8"))
        cmd = req.get("type", "")
        if cmd == "execute":
            resp = execute(req.get("code", ""))
        elif cmd == "get_scene":
            resp = {"ok": True, "scene": get_scene_info()}
        elif cmd == "ping":
            resp = {"ok": True, "pong": True}
        else:
            resp = {"ok": False, "error": "unknown command: " + cmd}
        conn.sendall(json.dumps(resp).encode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        try:
            conn.sendall(json.dumps({"ok": False, "error": str(exc)}).encode("utf-8"))
        except OSError:
            pass
    finally:
        conn.close()


def server_loop():
    global _running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(4)
    _running = True
    print("Galahad bridge listening on %s:%d" % (HOST, PORT))
    while _running:
        try:
            conn, _ = s.accept()
            threading.Thread(target=handle, args=(conn,), daemon=True).start()
        except OSError:
            break
    s.close()


def register():
    global _server_thread, _running
    if _server_thread is not None:
        return
    _running = True
    _server_thread = threading.Thread(target=server_loop, daemon=True)
    _server_thread.start()
    print("Galahad bridge registered")


def unregister():
    global _running
    _running = False


if __name__ == "__main__":
    register()
