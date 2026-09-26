"""Hardware-in-the-loop smoke test — run manually ON the Pi 4, not in CI
(no camera/GPIO in GitHub Actions). Invoke directly:

    python -m tests.hardware.test_capture_smoke

Checks the full loop: capture -> OCR -> submit to a running API instance.
Point a real receipt at the camera before running.
"""

from pathlib import Path

from src.edge.capture_service import capture_image, process_and_submit


def main() -> None:
    print("Capturing image from Pi Camera in 3 seconds — point a receipt at it...")
    image_path = capture_image(Path("data/raw"))
    print(f"Captured: {image_path}")

    result = process_and_submit(image_path, api_base_url="http://localhost:8000")
    print(f"Ingested as receipt id: {result.get('id')}")

    assert "id" in result, "expected ingestion API to return a receipt id"
    print("Smoke test PASSED")


if __name__ == "__main__":
    main()
