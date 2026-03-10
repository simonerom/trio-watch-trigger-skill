# trio-watch-trigger-skill

Skill + script per usare **trio-core** con monitoraggio continuo stream (RTSP) e trigger di azioni quando una condizione è vera.

Repository: https://github.com/simonerom/trio-watch-trigger-skill

---

## A chi serve

Se hai già OpenClaw installato e vuoi:

1. monitorare una camera/stream con TrioCore
2. descrivere una condizione in linguaggio naturale (es. “c’è una persona alla porta?”)
3. eseguire un’azione quando scatta un alert

---

## Prerequisiti minimi

- macOS su Apple Silicon (M1/M2/M3/M4)
- OpenClaw già installato
- accesso shell sul Mac
- URL RTSP della camera (o stream equivalente)

---

## Installazione da zero

### 1) Installa trio-core

```bash
pipx install 'trio-core[mlx,webcam,claw]'
```

### 2) Installa ffmpeg

```bash
brew install ffmpeg
```

### 3) Installa dipendenza script watcher

```bash
python3 -m pip install httpx
```

### 4) Verifica ambiente

```bash
trio doctor
```

Se `trio doctor` fallisce, risolvi prima le dipendenze mancanti.

---

## Clona questo repo

```bash
git clone https://github.com/simonerom/trio-watch-trigger-skill.git
cd trio-watch-trigger-skill
```

---

## Uso base (2 terminali)

## Terminale A — avvia server TrioCore

```bash
trio serve --host 127.0.0.1 --port 8000
```

## Terminale B — avvia watcher + trigger

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

Quando Trio emette evento `alert`, lo script esegue `--action-cmd` (max una volta ogni `--cooldown` secondi).

---

## Variabili disponibili nell’action

Quando scatta un alert, lo script passa queste env vars al comando:

- `TRIO_ALERT_JSON` → payload JSON completo dell’alert
- `TRIO_ALERT_NAMES` → ID condizioni triggerate (CSV)
- `TRIO_ALERT_ANSWERS` → sintesi risposte modello

Esempio salvataggio log:

```bash
--action-cmd 'mkdir -p ~/trio-alerts && echo "$TRIO_ALERT_JSON" >> ~/trio-alerts/alerts.jsonl'
```

---

## Integrazione OpenClaw (pattern consigliato)

In OpenClaw, quando arriva un alert:

1. invia notifica con `message`
2. se urgente, aggiungi `nodes.notify`
3. opzionale: acquisisci frame extra come evidenza

Mantieni sempre cooldown/idempotenza per evitare spam.

---

## Troubleshooting rapido

### `ModuleNotFoundError: httpx`

```bash
python3 -m pip install httpx
```

### Trio non parte / dipendenze mancanti

```bash
trio doctor
```

### Non si connette al server

Assicurati che Terminale A sia attivo:

```bash
trio serve --host 127.0.0.1 --port 8000
```

### Nessun alert

- verifica URL RTSP
- prova condizioni più semplici (es. `Is there a person?`)
- aumenta FPS (es. `--fps 2`)
- riduci risoluzione per più reattività

---

## File principali

- `SKILL.md` → istruzioni skill OpenClaw
- `scripts/trio_watch_trigger.py` → watcher SSE + trigger action
- `references/trio-core-watch-reference.md` → riferimenti comandi/API verificati
