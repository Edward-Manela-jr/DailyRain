from ocr_providers.mathpix import MathpixOCR
import os
import re


INPUT_DIR = "test_data/benchmark_upscaled"


def clean_ocr(text):
    """Convert Mathpix text into a simple rainfall value."""

    if not text:
        return ""

    text = text.strip()

    # Remove common LaTeX wrappers
    text = text.replace(r"\(", "")
    text = text.replace(r"\)", "")
    text = text.replace("$", "")

    # Convert multiplication dot to decimal point
    text = text.replace(r"\cdot", ".")

    # Remove spaces
    text = text.replace(" ", "")

    # Keep only digits and decimal point
    match = re.search(r"\d+(?:\.\d+)?", text)

    if match:
        return match.group(0)

    return text


def main():

    ocr = MathpixOCR()

    files = sorted(
        f for f in os.listdir(INPUT_DIR)
        if f.endswith(".png")
    )

    print()
    print("=" * 75)
    print("MATHPIX RAINFALL OCR BENCHMARK")
    print("=" * 75)
    print()

    print(
        f"{'CELL':<18}"
        f"{'OCR':<15}"
        f"{'CONF':<12}"
        f"{'RATE':<12}"
    )

    print("-" * 75)

    for filename in files:

        path = os.path.join(
            INPUT_DIR,
            filename
        )

        try:

            result = ocr.recognize(path)

            raw_text = result.get("text", "")
            cleaned = clean_ocr(raw_text)

            confidence = result.get(
                "confidence",
                ""
            )

            confidence_rate = result.get(
                "confidence_rate",
                ""
            )

            print(
                f"{filename:<18}"
                f"{cleaned:<15}"
                f"{str(confidence):<12}"
                f"{str(confidence_rate):<12}"
            )

        except Exception as e:

            print(
                f"{filename:<18}"
                f"ERROR: {e}"
            )

    print()
    print("=" * 75)


if __name__ == "__main__":
    main()
