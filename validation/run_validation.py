"""Run rainfall OCR validation against a benchmark CSV."""

from __future__ import annotations

import csv
from pathlib import Path

from rainfall_validator import validate_rainfall


INPUT_CSV = Path("output/full_benchmark/mathpix_benchmark_results.csv")

OUTPUT_DIR = Path("output/validation")
REVIEW_QUEUE = OUTPUT_DIR / "review_queue.csv"
VALIDATED_RECORDS = OUTPUT_DIR / "validated_records.csv"
VALIDATION_AUDIT = OUTPUT_DIR / "validation_audit.csv"


REVIEW_FIELDS = [
    "station_id",
    "year",
    "month",
    "day",
    "raw_ocr",
    "normalized",
    "confidence",
    "confidence_rate",
    "validation_status",
    "validation_reason",
    "source_path",
    "upscaled_path",
    "request_id",
]


FINAL_FIELDS = [
    "station_id",
    "year",
    "month",
    "day",
    "MAX",
    "MIN",
    "RAINFALL",
]


AUDIT_FIELDS = [
    "station_id",
    "year",
    "month",
    "day",
    "raw_ocr",
    "normalized",
    "confidence",
    "confidence_rate",
    "validation_status",
    "validation_reason",
    "original_classification",
    "source_path",
    "upscaled_path",
    "request_id",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(
    path: Path,
    rows: list[dict[str, str]],
    fields: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"Benchmark CSV not found: {INPUT_CSV}"
        )

    rows = read_csv(INPUT_CSV)

    review_rows = []
    validated_rows = []
    audit_rows = []

    for row in rows:
        normalized = row.get("normalized", "").strip()

        if normalized == "":
            normalized_value = None
        else:
            normalized_value = normalized

        confidence = row.get("confidence", "").strip()

        if confidence == "":
            confidence_value = None
        else:
            confidence_value = confidence

        result = validate_rainfall(
            normalized_value,
            confidence_value,
        )

        audit_row = {
            "station_id": row["station_id"],
            "year": row["year"],
            "month": row["month"],
            "day": row["day"],
            "raw_ocr": row["raw_ocr"],
            "normalized": normalized,
            "confidence": row["confidence"],
            "confidence_rate": row["confidence_rate"],
            "validation_status": result.status,
            "validation_reason": result.reason,
            "original_classification": row["classification"],
            "source_path": row["source_path"],
            "upscaled_path": row["upscaled_path"],
            "request_id": row["request_id"],
        }

        audit_rows.append(audit_row)

        if result.status == "ACCEPT":
            validated_rows.append(
                {
                    "station_id": row["station_id"],
                    "year": row["year"],
                    "month": row["month"],
                    "day": row["day"],
                    "MAX": "",
                    "MIN": "",
                    "RAINFALL": normalized,
                }
            )

        else:
            review_rows.append(
                {
                    "station_id": row["station_id"],
                    "year": row["year"],
                    "month": row["month"],
                    "day": row["day"],
                    "raw_ocr": row["raw_ocr"],
                    "normalized": normalized,
                    "confidence": row["confidence"],
                    "confidence_rate": row["confidence_rate"],
                    "validation_status": result.status,
                    "validation_reason": result.reason,
                    "source_path": row["source_path"],
                    "upscaled_path": row["upscaled_path"],
                    "request_id": row["request_id"],
                }
            )

    # Sort records chronologically.
    validated_rows.sort(
        key=lambda r: (
            r["year"],
            r["month"],
            int(r["day"]),
        )
    )

    review_rows.sort(
        key=lambda r: (
            r["year"],
            r["month"],
            int(r["day"]),
        )
    )

    write_csv(
        REVIEW_QUEUE,
        review_rows,
        REVIEW_FIELDS,
    )

    write_csv(
        VALIDATED_RECORDS,
        validated_rows,
        FINAL_FIELDS,
    )

    write_csv(
        VALIDATION_AUDIT,
        audit_rows,
        AUDIT_FIELDS,
    )

    print()
    print("RAINFALLDIGITIZER - VALIDATION")
    print("=" * 42)
    print(f"Input rows:       {len(rows)}")
    print(f"Accepted:         {len(validated_rows)}")
    print(f"Sent to review:   {len(review_rows)}")
    print()
    print(f"Review queue:     {REVIEW_QUEUE}")
    print(f"Validated CSV:    {VALIDATED_RECORDS}")
    print(f"Validation audit: {VALIDATION_AUDIT}")
    print()


if __name__ == "__main__":
    main()
