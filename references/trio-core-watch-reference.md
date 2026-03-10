# TrioCore watch reference

Verified from trio-core source (`src/trio_core/cli.py`, `README.md`).

## Install

- `pipx install 'trio-core[mlx]'`
- `pipx install 'trio-core[mlx,webcam]'`
- `pipx install 'trio-core[mlx,webcam,claw]'`
- `brew install ffmpeg`

## Health check

- `trio doctor`

## Serve API

- `trio serve --host 127.0.0.1 --port 8000`

## Watch API (SSE)

Start watch (`POST /v1/watch`):

```json
{
  "source": "rtsp://...",
  "conditions": [
    {"id": "person", "question": "Is there a person?"}
  ],
  "fps": 1,
  "resolution": "672x448"
}
```

Events include: `status`, `result`, `alert`, `heartbeat`, `error`.

List active watches:

- `GET /v1/watch`

Stop a watch:

- `DELETE /v1/watch/{id}`
