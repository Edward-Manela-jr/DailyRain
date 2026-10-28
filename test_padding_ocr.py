from ocr_providers.mathpix import MathpixOCR
import os
import re

INPUT_DIR = "test_data/padding_variants_upscaled"


def clean_ocr(text):
    if not text:
        return ""

    text = text.strip()
    text = text.replace(r"\(", "")
    text = text.replace(r"\)", "")
    text = text.replace("$", "")
    text = text.replace(r"\cdot", ".")
    text = text.replace(" ", "")

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
    print("=" * 90)
    print("MATHPIX PADDING BENCHMARK")
    print("=" * 90)
    print()

    print(
        f"{'CELL':<25}"
        f"{'OCR':<12}"
        f"{'CONF':<15}"
        f"{'RATE':<15}"
    )

    print("-" * 90)

    for filename in files:

        path = os.path.join(INPUT_DIR, filename)

        try:

            result = ocr.recognize(path)

            raw_text = result.get("text", "")
            cleaned = clean_ocr(raw_text)

            confidence = result.get("confidence", "")
            confidence_rate = result.get(
                "confidence_rate",
                ""
            )

            print(
                f"{filename:<25}"
                f"{cleaned:<12}"
                f"{str(confidence):<15}"
                f"{str(confidence_rate):<15}"
            )

        except Exception as e:

            print(
                f"{filename:<25}"
                f"ERROR: {e}"
            )

    print()
    print("=" * 90)


if __name__ == "__main__":
    main()
