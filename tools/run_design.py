"""Run the generated Galahad command script through polykrom-cli.

    python tools/run_design.py [--cli PATH] [--stop-on-error]

Keeps the CLI's stdout/stderr, summarises the per-command results and returns a
non-zero exit code if any command failed.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "design", "galahad.json")


def find_cli(explicit):
    for candidate in (explicit, os.environ.get("POLYKROM_CLI"),
                      shutil.which("polykrom-cli"),
                      r"C:\Users\doome\polykrom\target\release\polykrom-cli.exe",
                      os.path.join(ROOT, "tools", "bin", "polykrom-cli.exe")):
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", default=None)
    ap.add_argument("--script", default=SCRIPT)
    ap.add_argument("--stop-on-error", action="store_true")
    args = ap.parse_args()

    cli = find_cli(args.cli)
    if not cli:
        print("polykrom-cli not found; pass --cli PATH", file=sys.stderr)
        return 2

    proc = subprocess.run([cli, "run", args.script], cwd=ROOT,
                          capture_output=True, text=True, timeout=1800)
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()

    # the CLI prints one JSON object per command when given --json, else text
    failures = [line for line in (out + "\n" + err).splitlines()
                if line.strip().lower().startswith("error") or "failed" in line.lower()]
    print("exit:", proc.returncode)
    if out:
        print("--- stdout ---")
        print(out[-6000:])
    if err:
        print("--- stderr ---")
        print(err[-6000:])
    if failures:
        print(f"--- {len(failures)} problem line(s) ---")
        for line in failures[:40]:
            print(line)
        return 1
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
