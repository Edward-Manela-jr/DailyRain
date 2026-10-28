
"""OCR provider abstraction for whole-image rainfall sheet OCR."""

import os
import json
import requests
from dotenv import load_dotenv


load_dotenv()


class MathpixOCR:
    """Mathpix API client — sends one full image per call."""

    API_URL = "https://api.mathpix.com/v3/text"

    def __init__(self):
        self.app_id = os.getenv("MATHPIX_APP_ID")
        self.app_key = os.getenv("MATHPIX_APP_KEY")

        if not self.app_id or not self.app_key:
            raise RuntimeError(
                "Mathpix credentials not found. Check your .env file."
            )

    def recognize(self, image_path):
        """
        Send a full rainfall sheet image to Mathpix and return the
        complete API response, including line data for position mapping.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        options = {
            "formats": ["text"],
            "include_line_data": True,
            "rm_spaces": True,
            "metadata": {
                "improve_mathpix": False
            }
        }

        with open(image_path, "rb") as image_file:
            response = requests.post(
                self.API_URL,
                files={
                    "file": image_file
                },
                data={
                    "options_json": json.dumps(options)
                },
                headers={
                    "app_id": self.app_id,
                    "app_key": self.app_key
                },
                timeout=60
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"Mathpix API error {response.status_code}: {response.text}"
            )

        return response.json()


def line_center(line):
    """Extract (cx, cy, text) from a Mathpix line_data entry."""
    bbox = line.get("bounding_box") or line.get("bbox") or {}
    if not bbox:
        return None

    # Mathpix bounding_box may be [x1, y1, x2, y2] or {x1, y1, x2, y2}
    if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
        x1, y1, x2, y2 = bbox[:4]
    elif isinstance(bbox, dict):
        x1 = bbox.get("x1", 0)
        y1 = bbox.get("y1", 0)
        x2 = bbox.get("x2", 0)
        y2 = bbox.get("y2", 0)
    else:
        return None

    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    text = line.get("text", "") or ""
    return cx, cy, text


def line_confidence(line):
    """Best-effort confidence extraction from a line entry."""
    for key in ("confidence", "confidence_rate", "score"):
        val = line.get(key)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                pass
    return None
