from ocr_providers.mathpix import MathpixOCR
import os
import re


INPUT_DIR = "test_data/problem_variants_upscaled"


def clean_ocr(text):
    if not text:
        return ""

    text = text.strip()

    text = text.replace(r"\(", "")
    text = text.replace(r"\)", "")
    text = text.replace("$", "")
    text = text.replace(r"\cdot", ".")
    text = text.replace(" ", "")

    match = re.search(
        r"\d+(?:\.\d+)?",
        text
    )

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
    print("=" * 85)
    print("MATHPIX PROBLEM-CELL CROP BENCHMARK")
    print("=" * 85)
    print()

    print(
        f"{'CELL':<25}"
        f"{'OCR':<12}"
        f"{'CONF':<12}"
        f"{'RATE':<12}"
    )

    print("-" * 85)

    for filename in files:

        path = os.path.join(
            INPUT_DIR,
            filename
        )

        try:

            result = ocr.recognize(path)

            raw_text = result.get(
                "text",
                ""
            )

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
                f"{filename:<25}"
                f"{cleaned:<12}"
                f"{str(confidence):<12}"
                f"{str(confidence_rate):<12}"
            )

        except Exception as e:

            print(
                f"{filename:<25}"
                f"ERROR: {e}"
            )

    print()
    print("=" * 85)


if __name__ == "__main__":
    main()
