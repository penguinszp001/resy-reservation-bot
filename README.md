# Resy Reservation Bot (Playwright)

This project automates the final booking flow for a specific Resy venue/time window.

It is designed for a **human-in-the-loop** workflow:
- You open a real browser window.
- You log in manually.
- The script waits for reservation release time.
- It refreshes, selects your target time, and clicks through Reserve/Confirm.

---

## Files

- `reserve.py` — original local script (unchanged).
- `reserve_docker.py` — Docker-oriented script that reads config from environment variables.
- `Dockerfile` — image definition for containerized runs.
- `docker-compose.yml` — compose service for running with environment parameters.
- `.env.example` — sample environment values.
- `requirements.txt` — Python dependencies.

---

## Configuration parameters

For Docker usage, configure these values as environment variables:

- `TARGET_RESERVATION_TIME` — target slot label (example: `8:30 PM`)
- `TARGET_RUN_TIME` — local machine time to start booking loop (`HH:MM:SS` 24h)
- `RELOAD_INTERVAL` — delay between retries (seconds)
- `URL` — exact Resy venue/date/seats URL
- `LOGIN_WAIT_SECONDS` — login wait mode for Docker script:
  - `0`: show interactive `press ENTER when logged in` prompt
  - `>0`: skip prompt and wait fixed seconds (default `120`)

`reserve_docker.py` validates and loads these values at startup.

---

## Run locally (non-Docker)

Keep using the existing script:

```bash
python reserve.py
```

Install requirements first if needed:

```bash
pip install playwright
playwright install chromium
```

---

## Run with Docker Compose

### 1) Prepare environment file

```bash
cp .env.example .env
```

Edit `.env` values for your target run.

If you want the old interactive behavior, set `LOGIN_WAIT_SECONDS=0`.
If you prefer automatic delay, set a positive value (for example `120`).

### 2) Allow Docker access to your Linux X display

```bash
export DISPLAY=${DISPLAY:-:0}
xhost +local:root
```

This is required because the script launches Chromium in headed mode (`headless=False`) for manual login.

### 3) Build and run

```bash
docker compose up --build
```

### 4) Stop when done

```bash
docker compose down
```

Logs are written to `./logging` on your host.

---

## What the scripts do

Both scripts perform the same booking flow:

1. Open configured Resy venue URL in Chromium.
2. Pause for manual login (`input(...)`).
3. Wait until `TARGET_RUN_TIME`.
4. Reload and scan visible reservation slots.
5. Click slot matching `TARGET_RESERVATION_TIME`.
6. Detect booking button on page or inside iframe.
7. Click **Reserve Now**, then **Confirm Reservation**.
8. Run post-confirm checks via URL + confirmation selectors.

---

## Notes / Caveats

- Manual login is still required.
- Headless mode is intentionally disabled because booking reliability is usually better in headed mode.
- Resy selectors/flows may change over time.
- Use responsibly and comply with Resy Terms of Service and venue policies.
