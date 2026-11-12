"""Rebuild the whole sim2real package in one command.

    python tools/build_sim_model.py

Steps: generate the command script, run it through polykrom-cli, restore the
per-joint actuator limits, then validate in MuJoCo and write the report.

Set POLYKROM_CLI if the binary is not at tools/bin/polykrom-cli.exe.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def run(cmd, **kw):
    print("+", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=ROOT, **kw)
    if proc.returncode != 0:
        raise SystemExit(f"step failed ({proc.returncode}): {' '.join(cmd)}")
    return proc


def find_cli():
    for candidate in (os.environ.get("POLYKROM_CLI"),
                      os.path.join(ROOT, "tools", "bin", "polykrom-cli.exe"),
                      "polykrom-cli"):
        if candidate == "polykrom-cli" or os.path.exists(candidate):
            return candidate
    raise SystemExit("polykrom-cli not found; set POLYKROM_CLI")


def main():
    cli = find_cli()
    run([PY, os.path.join("tools", "build_polykrom.py")])
    run([cli, "run", os.path.join("design", "galahad.json"), "--quiet"])
    run([PY, os.path.join("tools", "patch_mjcf.py"), os.path.join("design", "galahad.mjcf")])
    run([PY, os.path.join("tools", "mujoco_check.py"), os.path.join("design", "galahad.mjcf"),
         "--out", os.path.join("docs", "mujoco_report.json"), "--roll"])
    print("\nsim2real package rebuilt in design/")


if __name__ == "__main__":
    main()
