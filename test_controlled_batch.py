import csv
import json
import os
import re
import time

import cv2
import numpy as np

from ocr_providers.mathpix import MathpixOCR
from preprocessing.upscale_cell import upscale_cell


MANIFEST_PATH = "output/cell_manifest.csv"

UPSCALE_DIR = "output/full_benchmark_upscaled"
RESULTS_DIR = "output/full_benchmark"

RESULTS_CSV = os.path.join(
    RESULTS_DIR,
    "mathpix_benchmark_results.csv"
)

RAW_JSON = os.path.join(
    RESULTS_DIR,
    "mathpix_raw_responses.json"
)

PROGRESS_CSV = os.path.join(
    RESULTS_DIR,
    "mathpix_benchmark_progress.csv"
)

PROGRESS_JSON = os.path.join(
    RESULTS_DIR,
    "mathpix_raw_progress.json"
)


# These are the 15 cells for which we have manually established
# expected values.
KNOWN_VALUES = {
    ("february", "1"): "18.0",
    ("october", "3"): "1.0",
    ("november", "3"): "2.5",
    ("january", "3"): "6.5",
    ("january", "5"): "38.0",
    ("january", "6"): "11.5",
    ("january", "7"): "24.0",
    ("january", "17"): "44.0",
    ("october", "18"): "16.0",
    ("april", "19"): "43.5",
    ("november", "13"): "23.0",
    ("february", "11"): "21.0",
    ("march", "26"): "22.5",
    ("april", "27"): "23.5",
    ("december", "30"): "152.0",
}


def has_ink_5px(image_path):
    """
    Same 5px screening method approved from the contact sheet.
    """

    image = cv2.imread(
        image_path,
        cv2.IMREAD_GRAYSCALE
    )

    if image is None:
        raise FileNotFoundError(
            f"Could not read {image_path}"
        )

    if image.shape[0] <= 14 or image.shape[1] <= 14:
        return False

    inner = image[5:-5, 5:-5]

    dark = inner < 205

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        dark.astype(np.uint8),
        connectivity=8
    )

    meaningful = np.zeros_like(dark, dtype=bool)

    height, width = inner.shape

    for label in range(1, num_labels):

        area = stats[
            label,
            cv2.CC_STAT_AREA
        ]

        component_width = stats[
            label,
            cv2.CC_STAT_WIDTH
        ]

        component_height = stats[
            label,
            cv2.CC_STAT_HEIGHT
        ]

        # Ignore components that are probably pieces of
        # the printed table/grid.
        if component_width >= width * 0.80:
            continue

        if component_height >= height * 0.80:
            continue

        if area >= 3:
            meaningful[labels == label] = True

    ratio = (
        float(np.count_nonzero(meaningful))
        / meaningful.size
    )

    return ratio >= 0.004


def normalize_text(text):
    """
    Convert Mathpix output into a simple rainfall value.

    Examples:

        (6 \\cdot 5) -> 6.5
        (18-0)       -> 18.0
        (152 \\cdot 0) -> 152.0

    We deliberately do NOT remove unknown LaTeX commands such
    as \\angle because they may indicate an OCR error.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove Mathpix math wrappers.
    text = text.replace(r"\(", "")
    text = text.replace(r"\)", "")

    # Convert multiplication-dot notation.
    text = text.replace(r"\cdot", ".")

    # Remove whitespace around decimal points.
    text = re.sub(
        r"(?<=\d)\s*\.\s*(?=\d)",
        ".",
        text
    )

    # Sometimes Mathpix interprets a handwritten decimal
    # point as a hyphen.
    text = re.sub(
        r"(?<=\d)\s*-\s*(?=\d)",
        ".",
        text
    )

    return text.strip()


def is_numeric_rainfall(value):
    """
    Return True only when the normalized result is a simple
    non-negative decimal number.
    """

    if not value:
        return False

    return bool(
        re.fullmatch(
            r"\d+(?:\.\d+)?",
            value
        )
    )


def classify_result(
    normalized,
    confidence,
    expected=None
):
    """
    Classification is intentionally conservative.

    Confidence is NOT treated as proof of correctness.
    """

    numeric = is_numeric_rainfall(normalized)

    if expected is not None:

        if normalized == expected:
            return "CORRECT"

        return "OCR_MISMATCH"

    if not numeric:
        return "REVIEW_FORMAT"

    if confidence is not None and confidence < 0.90:
        return "REVIEW_LOW_CONFIDENCE"

    return "UNVERIFIED_NUMERIC"


def load_manifest():
    cells = []

    with open(
        MANIFEST_PATH,
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            path = row["path"]

            if not os.path.exists(path):
                print(
                    f"WARNING: missing cell: {path}"
                )
                continue

            # Apply the approved 5px screening.
            if not has_ink_5px(path):
                continue

            cells.append(row)

    return cells


def save_progress(results, raw_responses):
    """Save benchmark progress after every successful OCR request."""

    fieldnames = [
        "station_id",
        "year",
        "month",
        "day",
        "expected",
        "raw_ocr",
        "normalized",
        "confidence",
        "confidence_rate",
        "classification",
        "source_path",
        "upscaled_path",
        "request_id",
    ]

    with open(
        PROGRESS_CSV,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(results)

    with open(
        PROGRESS_JSON,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            raw_responses,
            file,
            indent=4,
            ensure_ascii=False
        )


def main():

    os.makedirs(
        UPSCALE_DIR,
        exist_ok=True
    )

    os.makedirs(
        RESULTS_DIR,
        exist_ok=True
    )

    print()
    print("=" * 80)
    print("RAINFALLDIGITIZER - FULL 67-CELL MATHPIX BENCHMARK")
    print("=" * 80)
    print()

    print("Loading cells...")
    cells = load_manifest()

    print(
        f"5px screening candidates: {len(cells)}"
    )

    if len(cells) != 67:
        print()
        print(
            "WARNING: Expected approximately 67 candidates."
        )
        print(
            "Please check the screening configuration "
            "before continuing."
        )
        print()

    ocr = MathpixOCR()

    results = []
    raw_responses = {}

    # Resume from previous successful requests if available.
    if os.path.exists(PROGRESS_CSV):

        print(
            f"Found previous benchmark progress: "
            f"{PROGRESS_CSV}"
        )

        with open(
            PROGRESS_CSV,
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:
                results.append(row)

        print(
            f"Already completed: {len(results)} cells"
        )

    if os.path.exists(PROGRESS_JSON):

        with open(
            PROGRESS_JSON,
            "r",
            encoding="utf-8"
        ) as file:

            raw_responses = json.load(file)

    for index, row in enumerate(cells, start=1):

        month = row["month"]
        day = row["day"]

        key = (month, day)

        cell_id = f"{month}_{int(day):02d}"

        # Do not send an already completed cell to Mathpix again.
        if cell_id in raw_responses:

            print(
                f"[SKIP] {month:<10} "
                f"day {int(day):02d} "
                f"(already completed)"
            )

            continue

        expected = KNOWN_VALUES.get(key)

        name = (
            f"{month[:3]}{int(day)}"
        )

        original_path = row["path"]

        upscaled_path = os.path.join(
            UPSCALE_DIR,
            f"{month}_{int(day):02d}.png"
        )

        print(
            f"[{index:02d}/{len(cells)}] "
            f"{month:<10} day {int(day):02d}",
            end="",
            flush=True
        )

        # Prepare cell.
        upscale_cell(
            original_path,
            upscaled_path,
            scale=4
        )

        try:

            response = ocr.recognize(
                upscaled_path
            )

        except Exception as error:

            print()
            print()
            print("=" * 80)
            print("MATHPIX REQUEST INTERRUPTED")
            print("=" * 80)
            print()
            print(
                f"Cell: {month} day {day}"
            )
            print(
                f"Error: {error}"
            )
            print()
            print(
                "Previously completed cells have been saved."
            )
            print(
                "Fix the network connection and rerun the script."
            )
            print(
                "Completed cells will automatically be skipped."
            )
            print()

            save_progress(
                results,
                raw_responses
            )

            return

        raw_text = response.get(
            "text",
            ""
        )

        normalized = normalize_text(
            raw_text
        )

        confidence = response.get(
            "confidence"
        )

        confidence_rate = response.get(
            "confidence_rate"
        )

        classification = classify_result(
            normalized,
            confidence,
            expected
        )

        result = {
            "station_id": row["station_id"],
            "year": row["year"],
            "month": month,
            "day": day,
            "expected": expected or "",
            "raw_ocr": raw_text,
            "normalized": normalized,
            "confidence": confidence,
            "confidence_rate": confidence_rate,
            "classification": classification,
            "source_path": original_path,
            "upscaled_path": upscaled_path,
            "request_id": response.get(
                "request_id",
                ""
            ),
        }

        results.append(result)

        raw_responses[
            f"{month}_{int(day):02d}"
        ] = response

        # Save immediately so a network interruption does not
        # lose completed OCR requests.
        save_progress(
            results,
            raw_responses
        )

        print(
            f" -> {normalized or '[blank]'}"
            f" | conf={confidence}"
            f" | {classification}"
        )

        # Small pause between API requests.
        time.sleep(0.15)

    # ------------------------------------------------------------
    # Save CSV
    # ------------------------------------------------------------

    fieldnames = [
        "station_id",
        "year",
        "month",
        "day",
        "expected",
        "raw_ocr",
        "normalized",
        "confidence",
        "confidence_rate",
        "classification",
        "source_path",
        "upscaled_path",
        "request_id",
    ]

    with open(
        RESULTS_CSV,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(results)

    # ------------------------------------------------------------
    # Save raw JSON
    # ------------------------------------------------------------

    with open(
        RAW_JSON,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            raw_responses,
            file,
            indent=4,
            ensure_ascii=False
        )

    # ------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------

    print()
    print("=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    print()

    known = [
        r for r in results
        if r["expected"]
    ]

    correct = [
        r for r in known
        if r["classification"] == "CORRECT"
    ]

    mismatches = [
        r for r in known
        if r["classification"] == "OCR_MISMATCH"
    ]

    print(
        f"Total screened candidates: {len(results)}"
    )

    print(
        f"Known-value benchmark cells: {len(known)}"
    )

    print(
        f"Correct known cells:          {len(correct)}"
    )

    print(
        f"Known OCR mismatches:         {len(mismatches)}"
    )

    if known:
        accuracy = (
            len(correct)
            / len(known)
            * 100
        )

        print(
            f"Known-value accuracy:         {accuracy:.1f}%"
        )

    print()

    print("Known-value results:")
    print()

    for result in known:

        print(
            f"{result['classification']:<15} "
            f"{result['month']:<10} "
            f"day {int(result['day']):02d} "
            f"expected={result['expected']:<6} "
            f"ocr={result['normalized']:<15} "
            f"confidence={result['confidence']}"
        )

    print()

    print("Unverified cells requiring later review/validation:")
    print()

    unverified = [
        r for r in results
        if not r["expected"]
    ]

    for result in unverified:

        print(
            f"{result['classification']:<22} "
            f"{result['month']:<10} "
            f"day {int(result['day']):02d} "
            f"ocr={result['normalized']:<15} "
            f"confidence={result['confidence']}"
        )

    print()
    print("=" * 80)
    print("FILES SAVED")
    print("=" * 80)
    print()
    print(f"CSV: {RESULTS_CSV}")
    print(f"RAW: {RAW_JSON}")
    print()
    print("Benchmark complete.")
    print()


if __name__ == "__main__":
    main()
