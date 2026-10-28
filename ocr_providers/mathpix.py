import os
import json
import requests
from dotenv import load_dotenv


load_dotenv()


class MathpixOCR:
    """OCR provider using the Mathpix API."""

    API_URL = "https://api.mathpix.com/v3/text"

    def __init__(self):
        self.app_id = os.getenv("MATHPIX_APP_ID")
        self.app_key = os.getenv("MATHPIX_APP_KEY")

        if not self.app_id or not self.app_key:
            raise RuntimeError(
                "Mathpix credentials not found. "
                "Check your .env file."
            )

    def recognize(self, image_path):
        """
        Send an image to Mathpix and return the complete API response.
        """

        if not os.path.exists(image_path):
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

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
                timeout=30
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"Mathpix API error "
                f"{response.status_code}: "
                f"{response.text}"
            )

        return response.json()
