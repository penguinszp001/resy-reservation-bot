from playwright.sync_api import sync_playwright
import time
from datetime import datetime
import logging
import os

############################
# CONFIG
############################

TARGET_RESERVATION_TIME = "7:00 PM"
TARGET_RUN_TIME = "17:51:40"   # 24hr time when reservations open
RELOAD_INTERVAL = 0.75         # seconds between refresh attempts

URL = "https://resy.com/cities/jamaica-plain-ma-ma/venues/tres-gatos?date=2026-03-24&seats=2"


############################
# LOGGING SETUP
############################

os.makedirs("logging", exist_ok=True)

log_filename = datetime.now().strftime("logging/resy_log_%Y%m%d_%H%M%S.txt")

logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

def log(msg):
    print(msg)
    logging.info(msg)


############################
# WAIT FOR EXACT TIME
############################

def wait_until_target():
    now = datetime.now()
    today = now.date()

    target = datetime.strptime(TARGET_RUN_TIME, "%H:%M:%S").replace(
        year=today.year,
        month=today.month,
        day=today.day
    )

    log(f"Waiting until {target}")

    while datetime.now() < target:
        time.sleep(0.05)


############################
# MAIN SCRIPT
############################

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--start-maximized"]
    )
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()

    log("Opening venue page")
    page.goto(URL)

    input("Log into Resy in the browser, then press ENTER here to continue...")

    wait_until_target()

    log("Starting reservation search")

    while True:

        page.reload()

        # wait for reservation buttons to render
        try:
            page.wait_for_selector(".ReservationButton", timeout=5000)
        except:
            log("Reservation buttons not found, retrying...")
            time.sleep(RELOAD_INTERVAL)
            continue

        slots = page.locator(".ReservationButton")
        count = slots.count()
        log(f"Checking {count} available slots")

        found = False
        for i in range(count):
            slot = slots.nth(i)
            time_text = slot.locator(".ReservationButton__time").inner_text().strip()

            if time_text == TARGET_RESERVATION_TIME:
                log(f"Found target slot {TARGET_RESERVATION_TIME}")
                slot.click()
                log("Clicked reservation time")
                found = True
                break

        if found:
            log("Waiting for booking iframe to appear")

            frame = None
            for f in page.frames:
                if "resy.com/cities/jamaica-plain-ma-ma/venues/tres-gatos" in f.url:
                    frame = f
                    break

            if frame:
                with open("booking_frame.html", "w") as f:
                    f.write(frame.content())
                log("Saved booking frame DOM to booking_frame.html")

            # Wait for Resy booking iframe
            page.wait_for_selector("iframe", timeout=10000)
            frame = None
            for f in page.frames:
                if "resy" in f.url:
                    frame = f
                    break
            if frame is None:
                log("Could not find Resy booking iframe")
                continue

            log(f"Found booking frame: {frame.url}")

            # Click Reserve Now
            reserve_button = frame.locator('[data-test-id="order_summary_page-button-book"]')
            reserve_button.wait_for(state="visible", timeout=1000000)
            reserve_button.scroll_into_view_if_needed()
            reserve_button.click()
            log("Clicked Reserve Now")

            # Wait for confirm button to appear (same selector)
            confirm_button = frame.locator('[data-test-id="order_summary_page-button-book"]')
            confirm_button.wait_for(state="visible", timeout=10000)
            confirm_button.scroll_into_view_if_needed()
            confirm_button.click()
            log("Clicked Confirm Reservation")

            log("Reservation attempt completed")
            browser.close()
            exit()

        log("Target slot not found yet")
        time.sleep(RELOAD_INTERVAL)