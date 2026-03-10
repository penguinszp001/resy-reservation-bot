# Resy Reservation Bot (Playwright)

This project automates the final booking flow for a specific Resy venue/time window.

It is designed for a **human-in-the-loop** workflow:
- You open a real browser window.
- You log in manually.
- The script waits for reservation release time.
- It refreshes, selects your target time, and clicks through Reserve/Confirm.

---

## What this script does

`reserve.py` performs the following steps:

1. Opens the configured Resy venue URL in Chromium (headed mode).
2. Pauses for manual login (`input(...)`).
3. Waits until `TARGET_RUN_TIME`.
4. Repeatedly reloads and scans visible reservation slots.
5. Clicks the slot that matches `TARGET_RESERVATION_TIME`.
6. Detects the booking button either on the page or inside an iframe.
7. Clicks **Reserve Now** and then **Confirm Reservation**.
8. Runs post-confirm verification checks (URL and confirmation selectors).
9. Closes browser only if confirmation signals are detected; otherwise pauses for manual inspection.

---

## Files

- `reserve.py` — main booking script.
- `api_test.py` — auxiliary/testing script (not required for core flow).

---

## Requirements

- Python 3.9+
- Playwright for Python
- Chromium browser installed through Playwright

Install:

```bash
pip install playwright
playwright install chromium
```

---

## Configuration

Edit these constants near the top of `reserve.py`:

- `TARGET_RESERVATION_TIME` — target slot label (example: `"7:00 PM"`)
- `TARGET_RUN_TIME` — local machine time to start booking loop (`HH:MM:SS` 24h)
- `RELOAD_INTERVAL` — delay between retries
- `URL` — exact Resy venue/date/seats URL
- `POST_CONFIRM_TIMEOUT_MS` — max wait for post-confirm success signals
- `POST_CONFIRM_SUCCESS_SELECTORS` — known confirmation selectors/text patterns

---

## Usage

Run:

```bash
python reserve.py
```

Then:

1. Log in to Resy in the opened browser.
2. Return to terminal and press Enter.
3. Let the script run through release time and booking attempts.

If post-confirm verification is inconclusive, script pauses with Playwright inspector so you can manually inspect the state.

---

## Logging

Logs are written to the `logging/` directory with timestamps, for example:

- `logging/resy_log_YYYYMMDD_HHMMSS.txt`

Use logs to review:
- slot scan count
- detection of reserve/confirm buttons
- post-confirm success detection

---

## Notes / Caveats

- This script currently relies on manual login and headed browser mode.
- Headless mode may be less reliable due to anti-bot checks/challenges.
- Resy selectors and flow can change; be ready to update selectors and timeouts.
- Successful click does not always mean successful reservation; that is why post-confirm checks are included.

---

## Possible improvements

### 1) Make booking faster

- **Warm-up before release**: navigate and pre-load all resources 30–60 seconds before `TARGET_RUN_TIME` so only minimal UI updates happen at release.
- **Lower reload interval carefully**: reduce `RELOAD_INTERVAL` (e.g. 0.75 → 0.25) while monitoring rate limiting/challenges.
- **Use lightweight waits**: prefer targeted element waits over broad page load waits.
- **Pre-locate key selectors**: keep locator objects ready where possible to reduce repeated lookup overhead.
- **Move to persistent authenticated context**: save/reuse login session so there is no manual login latency each run.
- **System-level tuning**: run on stable low-latency network, wired connection, and low CPU load machine around release time.
- **Clock sync**: ensure machine clock is synced (NTP) to minimize timing drift around the exact release second.

### 2) Book multiple times simultaneously

- **Parallel browser contexts**: run multiple Playwright contexts/pages in parallel against same target slot to increase chance of one succeeding first.
- **Parallel process strategy**: run multiple script processes with slight jittered start offsets (e.g. 50–200ms) to avoid identical request timing.
- **Different network paths** (careful): if allowed by platform policies, separate attempts over different networks/hosts to reduce single-path failures.
- **Coordinator lock**: if one worker confirms success, signal others to stop immediately to avoid duplicate bookings.

### 3) Add backup-time strategy

- **Priority list of times**: replace single `TARGET_RESERVATION_TIME` with ordered list, e.g. `['7:00 PM', '7:15 PM', '6:45 PM']`.
- **Fallback window logic**: if top choice fails within N seconds, automatically attempt next best time.
- **Dynamic acceptable range**: allow nearest-time matching (within ±30 min) if exact time unavailable.
- **Retry tree**: attempt `primary -> backup1 -> backup2` across a short deadline, then continue loop.

### 4) Increase confidence in success detection

- **Network-response verification**: wait for booking API response status/body indicating confirmation.
- **Capture confirmation ID**: parse and log reservation number from page/API once booked.
- **Screenshot on success/failure**: save artifacts automatically for post-run auditing.

### 5) Improve maintainability

- Split script into functions/modules (`auth`, `slot_scan`, `booking`, `verification`).
- Add CLI arguments (`--date`, `--time`, `--seats`, `--url`, `--headless`).
- Add structured logs (JSON) for easier troubleshooting.

---

## Disclaimer

Use responsibly and comply with Resy Terms of Service and venue policies.
