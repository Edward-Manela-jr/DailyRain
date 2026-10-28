from ocr_providers.mathpix import MathpixOCR
import json


def main():

    image_path = "test_data/dec30_correct_upscaled.png"

    print("Starting Mathpix OCR test...")
    print(f"Image: {image_path}")

    ocr = MathpixOCR()

    result = ocr.recognize(image_path)

    print("\n--- COMPLETE MATHPIX RESPONSE ---")
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
