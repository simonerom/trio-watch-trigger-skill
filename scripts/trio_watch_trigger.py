#!/usr/bin/env python3
"""Subscribe to trio-core /v1/watch SSE and trigger an action on alert."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time

try:
    import httpx
except ImportError:
    print("[error] missing dependency: httpx. Install with: python3 -m pip install httpx", file=sys.stderr)
    raise


def _condition_id(text: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() else "_" for ch in text)
    while "__" in clean:
        clean = clean.replace("__", "_")
    return clean.strip("_")[:32] or "cond"


def _run_action(action_cmd: str, data: dict) -> int:
    triggered = [c for c in data.get("conditions", []) if c.get("triggered")]
    names = ",".join(c.get("id", "?") for c in triggered)
    answers = " | ".join(f"{c.get('id','?')}: {c.get('answer','')}" for c in triggered)

    env = os.environ.copy()
    env["TRIO_ALERT_JSON"] = json.dumps(data, ensure_ascii=False)
    env["TRIO_ALERT_NAMES"] = names
    env["TRIO_ALERT_ANSWERS"] = answers

    print(f"[action] running: {action_cmd}")
    proc = subprocess.run(action_cmd, shell=True, env=env)
    return proc.returncode


def watch(server: str, source: str, conditions: list[dict], fps: float, resolution: str | None,
          action_cmd: str, cooldown: float):
    url = f"{server.rstrip('/')}/v1/watch"
    payload = {"source": source, "conditions": conditions, "fps": fps}
    if resolution:
        payload["resolution"] = resolution

    print(f"[watch] POST {url}")
    print(f"[watch] source={source}")
    print(f"[watch] conditions={[c['id'] for c in conditions]}")

    last_action = 0.0

    with httpx.stream("POST", url, json=payload, timeout=None) as resp:
        if resp.status_code != 200:
            raise RuntimeError(f"watch failed: HTTP {resp.status_code} {resp.text}")

        watch_id = resp.headers.get("X-Watch-ID", "unknown")
        print(f"[watch] started watch_id={watch_id}")

        event_type = None
        for line in resp.iter_lines():
            if not line:
                continue
            if line.startswith("event: "):
                event_type = line[7:]
                continue
            if not line.startswith("data: "):
                continue

            raw = line[6:]
            if raw == "[DONE]":
                print("[watch] stream ended")
                return

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if event_type == "alert":
                now = time.time()
                if cooldown > 0 and now - last_action < cooldown:
                    print("[alert] skipped (cooldown)")
                    continue
                print(f"[alert] {json.dumps(data, ensure_ascii=False)}")
                rc = _run_action(action_cmd, data)
                print(f"[action] exit={rc}")
                last_action = now
            elif event_type == "error":
                raise RuntimeError(data.get("error", "unknown watch error"))
            elif event_type == "status":
                print(f"[status] {data.get('state', '?')}")


def main() -> int:
    p = argparse.ArgumentParser(description="trio-core watch -> trigger action")
    p.add_argument("--server", default="http://127.0.0.1:8000")
    p.add_argument("--source", required=True, help="RTSP URL or stream source")
    p.add_argument("--condition", action="append", required=True,
                   help="Natural language condition question (repeatable)")
    p.add_argument("--fps", type=float, default=1.0)
    p.add_argument("--resolution", default=None, help="Optional, e.g. 672x448")
    p.add_argument("--action-cmd", required=True,
                   help="Shell command executed on alert")
    p.add_argument("--cooldown", type=float, default=30.0,
                   help="Minimum seconds between action runs")
    args = p.parse_args()

    conditions = [{"id": _condition_id(c), "question": c} for c in args.condition]

    try:
        watch(
            server=args.server,
            source=args.source,
            conditions=conditions,
            fps=args.fps,
            resolution=args.resolution,
            action_cmd=args.action_cmd,
            cooldown=args.cooldown,
        )
    except KeyboardInterrupt:
        print("\n[watch] stopped by user")
        return 130
    except httpx.ConnectError:
        print(f"[error] cannot connect to {args.server}. Start trio first: trio serve", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
