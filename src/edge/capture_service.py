"""Raspberry Pi 4 scanning-station service.

Runs headless (NFR-2): watches for a capture trigger (button/GPIO or MQTT
message), takes a photo, runs OCR + parsing + classification locally, and
POSTs the result to the ingestion API. Designed to keep the Pi's job small —
it does NOT talk to the DB directly, only to the API, so the Pi can be
swapped/reimaged without touching schema credentials.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import httpx

from src.common.config import settings
from src.ml.inference.ocr_parser import parse_receipt_text, run_ocr

logger = logging.getLogger("edge.capture")


def capture_image(save_dir: Path) -> Path:
    """Capture a still image from the Pi Camera.

    Uses picamera2 on-device; kept as a separate function so the rest of the
    pipeline can be tested on a dev machine with a sample image file instead.
    """
    from picamera2 import Picamera2

    save_dir.mkdir(parents=True, exist_ok=True)
    out_path = save_dir / f"receipt_{int(time.time())}.jpg"

    cam = Picamera2()
    cam.start()
    time.sleep(1)  # let auto-exposure settle
    cam.capture_file(str(out_path))
    cam.stop()

    return out_path


def process_and_submit(image_path: Path, api_base_url: str) -> dict:
    """Run OCR + parsing on `image_path` and POST the result to the
    ingestion API. Returns the API response body. Raises on HTTP failure so
    the caller can retry/queue (NFR-1 budget: this whole call should stay
    under 5s on the Pi 4, excluding network).
    """
    raw_text = run_ocr(image_path)
    parsed = parse_receipt_text(raw_text)

    response = httpx.post(
        f"{api_base_url}/receipts/ingest",
        json={"parsed": parsed.model_dump(mode="json"), "image_path": str(image_path)},
        timeout=10.0,
    )
    response.raise_for_status()
    logger.info("submitted receipt from %s", image_path)
    return response.json()


def run_forever(api_base_url: str = "http://localhost:8000") -> None:
    """Main loop for the headless scanning station. Placeholder trigger:
    poll a local directory for new drop-in images (e.g. from a phone synced
    over the network). Swap for GPIO-button or MQTT-triggered capture once
    the hardware is wired up.
    """
    watch_dir = Path(settings.receipt_image_dir)
    seen: set[Path] = set()

    while True:
        for path in watch_dir.glob("*.jpg"):
            if path not in seen:
                seen.add(path)
                try:
                    process_and_submit(path, api_base_url)
                except Exception:
                    logger.exception("failed to process %s", path)
        time.sleep(2)


if __name__ == "__main__":
    logging.basicConfig(level=settings.log_level)
    run_forever()
