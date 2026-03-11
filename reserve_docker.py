from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
from datetime import datetime
import logging
import os

############################
# CONFIG
############################

DEFAULT_TARGET_RESERVATION_TIME = "8:30 PM"
DEFAULT_TARGET_RUN_TIME = "21:30:20"   # 24hr time when reservations open
DEFAULT_RELOAD_INTERVAL = 0.75          # seconds between refresh attempts
DEFAULT_URL = "https://resy.com/cities/boston-ma/venues/spiga?date=2026-03-18&seats=2"

# How long to wait for confirmation after clicking final confirm.
POST_CONFIRM_TIMEOUT_MS = 20000

# Update these if you find better selectors/text from your success page.
POST_CONFIRM_SUCCESS_SELECTORS = [
    '[data-test-id="booking-confirmation"]',
    '[data-test-id="reservation-confirmation"]',
    'text=/confirmed|reservation confirmed|you\'re booked/i',
]


def get_required_env(name: str, default: str | None = None) -> str:
    """Read an environment variable and raise a clear error if missing."""
    value = os.getenv(name, default)
    if value is None or value.strip() == "":
        raise ValueError(f"Missing required environment variable: {name}")
    return value.strip()


def get_reload_interval() -> float:
    value = get_required_env("RELOAD_INTERVAL", str(DEFAULT_RELOAD_INTERVAL))
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError("RELOAD_INTERVAL must be a valid number") from exc

    if parsed <= 0:
        raise ValueError("RELOAD_INTERVAL must be greater than 0")

    return parsed


def load_config() -> dict:
    target_reservation_time = get_required_env("TARGET_RESERVATION_TIME", DEFAULT_TARGET_RESERVATION_TIME)
    target_run_time = get_required_env("TARGET_RUN_TIME", DEFAULT_TARGET_RUN_TIME)
    datetime.strptime(target_run_time, "%H:%M:%S")

    return {
        "TARGET_RESERVATION_TIME": target_reservation_time,
        "TARGET_RUN_TIME": target_run_time,
        "RELOAD_INTERVAL": get_reload_interval(),
        "URL": get_required_env("URL", DEFAULT_URL),
    }


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


def find_visible_button_context(page, selector, timeout_ms=20000, poll_ms=150):
    """
    Return (context_name, context_obj, locator) for the first visible selector.
    Context can be page or any loaded frame.
    """
    deadline = time.time() + (timeout_ms / 1000)

    while time.time() < deadline:
        try:
            page_locator = page.locator(selector)
            if page_locator.count() > 0 and page_locator.first.is_visible():
                return "page", page, page_locator.first
        except Exception:
            pass

        for frame in page.frames:
            try:
                frame_locator = frame.locator(selector)
                if frame_locator.count() > 0 and frame_locator.first.is_visible():
                    return "frame", frame, frame_locator.first
            except Exception:
                # Cross-origin frame can be in a transient state while loading.
                continue

        time.sleep(poll_ms / 1000)

    return None, None, None


def click_with_fallback(locator):
    """Try normal click first, then JS click if Playwright actionability blocks."""
    locator.scroll_into_view_if_needed()

    try:
        locator.click(timeout=5000)
    except Exception:
        locator.click(force=True, timeout=5000)


def wait_for_post_confirm_success(page, timeout_ms=POST_CONFIRM_TIMEOUT_MS):
    """Wait for a strong signal that reservation submission has completed."""
    deadline = time.time() + (timeout_ms / 1000)

    while time.time() < deadline:
        # 1) URL signal
        try:
            current_url = page.url.lower()
            if any(token in current_url for token in ["confirm", "confirmed", "booking", "itinerary"]):
                log(f"Post-confirm URL indicates success flow: {page.url}")
                return True
        except Exception:
            pass

        # 2) Known confirmation UI signals on page or frames
        for selector in POST_CONFIRM_SUCCESS_SELECTORS:
            context_name, _, success_locator = find_visible_button_context(page, selector, timeout_ms=600, poll_ms=100)
            if success_locator is not None:
                log(f"Detected confirmation signal ({selector}) in {context_name}")
                return True

        time.sleep(0.2)

    return False


############################
# WAIT FOR EXACT TIME
############################


def wait_until_target(target_run_time):
    now = datetime.now()
    today = now.date()

    target = datetime.strptime(target_run_time, "%H:%M:%S").replace(
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


def main():
    config = load_config()
    log(
        "Loaded config: "
        f"TARGET_RESERVATION_TIME={config['TARGET_RESERVATION_TIME']}, "
        f"TARGET_RUN_TIME={config['TARGET_RUN_TIME']}, "
        f"RELOAD_INTERVAL={config['RELOAD_INTERVAL']}, "
        f"URL={config['URL']}"
    )

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=False,
                args=["--start-maximized"]
            )
        except Exception as exc:
            raise RuntimeError(
                "Failed to launch headed Chromium. Ensure Docker can access your X server "
                "(for example: export DISPLAY=:0 && xhost +local:root)."
            ) from exc
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        log("Opening venue page")
        page.goto(config["URL"])

        input("Log into Resy in the browser, then press ENTER here to continue...")

        wait_until_target(config["TARGET_RUN_TIME"])

        log("Starting reservation search")

        while True:

            page.reload()

            # wait for reservation buttons to render
            try:
                page.wait_for_selector(".ReservationButton", timeout=5000)
            except PlaywrightTimeoutError:
                log("Reservation buttons not found, retrying...")
                time.sleep(config["RELOAD_INTERVAL"])
                continue

            slots = page.locator(".ReservationButton")
            count = slots.count()
            log(f"Checking {count} available slots")

            found = False
            for i in range(count):
                slot = slots.nth(i)
                time_text = slot.locator(".ReservationButton__time").inner_text().strip()

                if time_text == config["TARGET_RESERVATION_TIME"]:
                    log(f"Found target slot {config['TARGET_RESERVATION_TIME']}")
                    slot.click()
                    log("Clicked reservation time")
                    found = True
                    break

            if found:
                log("Waiting for Reserve Now button in page/iframe")

                reserve_selector = '[data-test-id="order_summary_page-button-book"]'
                context_name, booking_context, reserve_button = find_visible_button_context(
                    page,
                    reserve_selector,
                    timeout_ms=20000
                )

                if reserve_button is None:
                    log("Could not find a visible Reserve Now button")
                    continue

                context_url = booking_context.url if context_name == "frame" else page.url
                log(f"Found Reserve Now in {context_name}: {context_url}")

                reserve_button.wait_for(state="visible", timeout=15000)
                click_with_fallback(reserve_button)
                log("Clicked Reserve Now")

                # The confirm step reuses the same selector in many Resy flows.
                _, _, confirm_button = find_visible_button_context(
                    page,
                    reserve_selector,
                    timeout_ms=10000
                )
                if confirm_button is None:
                    log("Confirm button not visible after Reserve Now click")
                    continue

                confirm_button.wait_for(state="visible", timeout=10000)
                click_with_fallback(confirm_button)
                log("Clicked Confirm Reservation")

                if wait_for_post_confirm_success(page):
                    log("Reservation confirmed by post-confirm verification checks")
                    browser.close()
                    exit()

                log("Post-confirm verification did not detect success; leaving browser open for manual check")
                page.pause()

            log("Target slot not found yet")
            time.sleep(config["RELOAD_INTERVAL"])


if __name__ == "__main__":
    main()
