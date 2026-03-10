---
name: trio-watch-trigger
description: Install and run trio-core to monitor RTSP/live streams for natural-language conditions, then trigger follow-up actions when alerts fire. Use when OpenClaw needs continuous camera/stream monitoring with condition-based actions (message notifications, local command execution, or escalation workflows).
---

# trio-watch-trigger

Use this skill to set up `trio-core`, start watch mode, and trigger actions when one or more conditions are met.

## 1) Install and sanity-check TrioCore

Run exactly these commands:

```bash
pipx install 'trio-core[mlx,webcam,claw]'
brew install ffmpeg
python3 -m pip install httpx
trio doctor
```

If `trio doctor` fails, fix missing dependencies before continuing.

## 2) Start TrioCore API server

Use `trio serve` in a long-running session.

```bash
trio serve --host 127.0.0.1 --port 8000
```

## 3) Start stream watch with conditions

Use `scripts/trio_watch_trigger.py` to subscribe to `/v1/watch` SSE events.

Example:

```bash
python3 scripts/trio_watch_trigger.py \
  --server http://127.0.0.1:8000 \
  --source 'rtsp://admin:pass@192.168.1.50:554/stream' \
  --condition 'Is there a person at the door?' \
  --condition 'Is there a package on the doorstep?' \
  --cooldown 30 \
  --action-cmd 'echo "ALERT $(date)"'
```

## 4) Run follow-up actions when an alert fires

The watcher script executes `--action-cmd` once per cooldown window and exports alert data through environment variables:

- `TRIO_ALERT_JSON` (full alert JSON)
- `TRIO_ALERT_NAMES` (comma-separated triggered condition IDs)
- `TRIO_ALERT_ANSWERS` (model answer summary)

In OpenClaw flows, prefer these follow-ups:

1. Send notification with `message` tool.
2. If urgent, also call `nodes.notify`.
3. Optionally capture extra evidence frame via Trio/OpenClaw camera tools.

Keep actions idempotent and use cooldown to avoid flooding.

## References

- Trio CLI/API commands: `references/trio-core-watch-reference.md`
