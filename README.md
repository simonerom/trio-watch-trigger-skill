# trio-watch-trigger-skill

Skill + script to run **trio-core** for continuous stream monitoring (RTSP) and trigger actions when a condition is true.

Repository: https://github.com/simonerom/trio-watch-trigger-skill

---

## Who this is for

Use this if you already have OpenClaw installed and want to:

1. monitor a camera/stream with TrioCore
2. define natural-language conditions (for example: “Is there a person at the door?”)
3. run an action when an alert fires

---

## Minimum requirements

- macOS on Apple Silicon (M1/M2/M3/M4)
- OpenClaw already installed
- shell access on the Mac
- RTSP URL for your camera (or equivalent stream source)

---

## Fresh install (from zero)

### 1) Install trio-core

```bash
pipx install 'trio-core[mlx,webcam,claw]'
```

### 2) Install ffmpeg

```bash
brew install ffmpeg
```

### 3) Install watcher script dependency

```bash
python3 -m pip install httpx
```

### 4) Verify environment

```bash
trio doctor
```

If `trio doctor` fails, fix missing dependencies first.

---

## Clone this repository

```bash
git clone https://github.com/simonerom/trio-watch-trigger-skill.git
cd trio-watch-trigger-skill
```

---

## Basic usage (2 terminals)

## Terminal A — start TrioCore API server

```bash
trio serve --host 127.0.0.1 --port 8000
```

## Terminal B — start watcher + trigger

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

## Main files

- `SKILL.md` → OpenClaw skill instructions
- `scripts/trio_watch_trigger.py` → SSE watcher + action trigger
- `references/trio-core-watch-reference.md` → verified command/API references
