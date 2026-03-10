# trio-watch-trigger-skill

Skill + script to run **trio-core** for continuous stream monitoring (RTSP) and trigger actions when a condition is true.

Repository: https://github.com/simonerom/trio-watch-trigger-skill

---

## What this repository contains

- `SKILL.md` (AgentSkills/OpenClaw skill definition)
- `scripts/trio_watch_trigger.py` (SSE watcher that executes an action on alert)
- `references/trio-core-watch-reference.md` (verified Trio commands and API notes)

Use this when you want to:

1. monitor a camera/stream with TrioCore
2. define natural-language conditions (for example: “Is there a person at the door?”)
3. run an action when an alert fires

---

## Prerequisites

- macOS on Apple Silicon (M1/M2/M3/M4) for MLX-backed TrioCore
- OpenClaw already installed
- shell access on the host machine
- RTSP URL for your camera (or equivalent stream source)

---

## 1) Install the skill in OpenClaw

OpenClaw supports AgentSkills folders from:

- `<workspace>/skills` (per-workspace, highest precedence)
- `~/.openclaw/skills` (shared local skills)

### Option A (recommended): workspace-scoped install

```bash
mkdir -p ~/.openclaw/workspace/skills
cd ~/.openclaw/workspace/skills
git clone https://github.com/simonerom/trio-watch-trigger-skill.git trio-watch-trigger
```

### Option B: shared local install

```bash
mkdir -p ~/.openclaw/skills
cd ~/.openclaw/skills
git clone https://github.com/simonerom/trio-watch-trigger-skill.git trio-watch-trigger
```

After installing, start a new OpenClaw session (or reload skills) so the new skill is picked up.

---

## 2) Install runtime dependencies

### Install trio-core

```bash
pipx install 'trio-core[mlx,webcam,claw]'
```

### Install ffmpeg

```bash
brew install ffmpeg
```

### Install watcher script dependency

```bash
python3 -m pip install httpx
```

### Verify environment

```bash
trio doctor
```

If `trio doctor` fails, fix missing dependencies first.

---

## 3) Run it (2 terminals)

### Terminal A — start TrioCore API server

```bash
trio serve --host 127.0.0.1 --port 8000
```

### Terminal B — start watcher + trigger

```bash
python3 scripts/trio_watch_trigger.py \
  --server http://127.0.0.1:8000 \
  --source 'rtsp://admin:password@192.168.1.50:554/stream' \
  --condition 'Is there a person at the door?' \
  --condition 'Is there a package on the doorstep?' \
  --fps 1 \
  --resolution 672x448 \
  --cooldown 60 \
  --action-cmd 'echo "[ALERT] $TRIO_ALERT_NAMES :: $TRIO_ALERT_ANSWERS"'
```

When Trio emits an `alert` event, the script runs `--action-cmd` (at most once every `--cooldown` seconds).

---

## Environment variables exposed to the action

When an alert fires, the script exports these env vars to your command:

- `TRIO_ALERT_JSON` → full alert JSON payload
- `TRIO_ALERT_NAMES` → triggered condition IDs (CSV)
- `TRIO_ALERT_ANSWERS` → model answer summary

Example JSONL logging action:

```bash
--action-cmd 'mkdir -p ~/trio-alerts && echo "$TRIO_ALERT_JSON" >> ~/trio-alerts/alerts.jsonl'
```

---

## OpenClaw integration (recommended pattern)

When an alert arrives in OpenClaw:

1. send a notification with `message`
2. if urgent, also call `nodes.notify`
3. optionally capture extra evidence frames

Always keep actions idempotent and enforce cooldown to avoid flooding.

### Ready-to-use example: Telegram notification via OpenClaw

Requirements:

- OpenClaw gateway running
- Telegram plugin configured
- target chat id (for example `459267437`)

Action command example (use inside `--action-cmd`):

```bash
--action-cmd 'openclaw message send --channel telegram --target 459267437 --message "🚨 Trio alert: $TRIO_ALERT_NAMES | $TRIO_ALERT_ANSWERS"'
```

Full watcher + Telegram example:

```bash
python3 scripts/trio_watch_trigger.py \
  --server http://127.0.0.1:8000 \
  --source 'rtsp://admin:password@192.168.1.50:554/stream' \
  --condition 'Is there a person at the door?' \
  --fps 1 \
  --cooldown 60 \
  --action-cmd 'openclaw message send --channel telegram --target 459267437 --message "🚨 Trio alert: $TRIO_ALERT_NAMES | $TRIO_ALERT_ANSWERS"'
```

Notes:

- keep `--cooldown` enabled to avoid alert flooding
- notifications are sent only when Trio emits an `alert` event
- for quick testing, temporarily replace action with `echo ...`

---

## Quick troubleshooting

### `ModuleNotFoundError: httpx`

```bash
python3 -m pip install httpx
```

### Trio does not start / missing dependencies

```bash
trio doctor
```

### Cannot connect to server

Make sure Terminal A is running:

```bash
trio serve --host 127.0.0.1 --port 8000
```

### No alerts firing

- verify RTSP URL
- try simpler conditions (for example `Is there a person?`)
- increase FPS (for example `--fps 2`)
- reduce resolution for faster cycles

---

## Compatibility with OpenClaw-like systems

This repository follows the AgentSkills-style layout (`SKILL.md` + optional `scripts/` and `references/`).

To use it in other compatible agent runtimes:

1. Copy this folder into that runtime’s skills directory.
2. Keep the folder name as `trio-watch-trigger` (recommended).
3. Ensure the runtime can execute local scripts and shell commands.
4. Install the same runtime dependencies listed above (`trio`, `ffmpeg`, `httpx`).

If the runtime supports command/skill metadata filtering, keep `SKILL.md` as-is and only adjust paths if your platform requires a different skill root.

---

## Main files

- `SKILL.md` → OpenClaw skill instructions
- `scripts/trio_watch_trigger.py` → SSE watcher + action trigger
- `references/trio-core-watch-reference.md` → verified command/API references
