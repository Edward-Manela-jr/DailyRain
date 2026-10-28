"""Interactive review workflow for questionable rainfall OCR results.

Usage:
    python validation/review_queue.py
    python validation/review_queue.py --queue output/validation/review_queue.csv

For each flagged cell, the reviewer can:
    [a] accept the OCR value
    [c] enter a corrected value
    [s] skip for now
    [q] quit and save progress

The script keeps the OCR evidence and reviewer decision separate. The final
rainfall CSV is regenerated after each saved decision.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
from pathlib import Path


DEFAULT_QUEUE = Path("output/validation/review_queue.csv")
DEFAULT_DECISIONS = Path("output/validation/review_decisions.csv")
DEFAULT_FINAL = Path("output/validation/final_rainfall_records.csv")

NUMBER_RE = re.compile(r"^\d+(?:\.\d+)?$")

FINAL_FIELDS = [
    "station_id",
    "year",
    "month",
    "day",
    "MAX",
    "MIN",
    "RAINFALL",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_value(value: str) -> bool:
    value = value.strip()
    if not NUMBER_RE.fullmatch(value):
        return False
    try:
        number = float(value)
    except ValueError:
        return False
    return 0 <= number <= 1000


def image_path_for(row: dict[str, str]) -> Path:
    day = int(row["day"])
    return Path("output") / "cells" / row["month"] / f"day_{day:02d}.png"


def open_image(path: Path) -> None:
    if not path.exists():
        print(f"  Image not found: {path}")
        return

    try:
        subprocess.Popen(
            ["xdg-open", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        print("  Could not open the image automatically.")
        print(f"  Image: {path}")


def load_decisions(path: Path) -> dict[tuple[str, str, str, str], dict[str, str]]:
    if not path.exists():
        return {}

    rows = read_csv(path)
    return {
        (r["station_id"], r["year"], r["month"], r["day"]): r
        for r in rows
    }


def save_decisions(path: Path, decisions: dict[tuple[str, str, str, str], dict[str, str]]) -> None:
    fields = [
        "station_id",
        "year",
        "month",
        "day",
        "raw_ocr",
        "ocr_value",
        "confidence",
        "review_status",
        "final_value",
        "reviewer_note",
        "image_path",
    ]
    rows = list(decisions.values())
    rows.sort(key=lambda r: (r["year"], r["month"], int(r["day"])))
    write_csv(path, rows, fields)


def rebuild_final(queue_rows: list[dict[str, str]], decisions: dict[tuple[str, str, str, str], dict[str, str]], output: Path) -> None:
    rows: list[dict[str, str]] = []

    for row in queue_rows:
        key = (row["station_id"], row["year"], row["month"], row["day"])
        decision = decisions.get(key)
        if not decision or decision["review_status"] != "ACCEPTED":
            continue

        rows.append(
            {
                "station_id": row["station_id"],
                "year": row["year"],
                "month": row["month"],
                "day": row["day"],
                "MAX": "",
                "MIN": "",
                "RAINFALL": decision["final_value"],
            }
        )

    # Deduplicate by date while preserving the latest decision.
    unique: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (row["station_id"], row["year"], row["month"], row["day"])
        unique[key] = row

    final_rows = list(unique.values())
    final_rows.sort(key=lambda r: (r["year"], r["month"], int(r["day"])))
    write_csv(output, final_rows, FINAL_FIELDS)


def review(queue_path: Path, decisions_path: Path, final_path: Path) -> None:
    if not queue_path.exists():
        raise FileNotFoundError(f"Review queue not found: {queue_path}")

    queue_rows = read_csv(queue_path)
    decisions = load_decisions(decisions_path)

    pending = [
        row for row in queue_rows
        if (row["station_id"], row["year"], row["month"], row["day"]) not in decisions
    ]

    print("\nRAINFALLDIGITIZER - HUMAN REVIEW")
    print("=" * 42)
    print(f"Review queue: {len(queue_rows)}")
    print(f"Already decided: {len(queue_rows) - len(pending)}")
    print(f"Pending: {len(pending)}")
    print()

    for index, row in enumerate(pending, start=1):
        key = (row["station_id"], row["year"], row["month"], row["day"])
        image_path = image_path_for(row)

        print("-" * 60)
        print(f"[{index}/{len(pending)}] {row['month']} day {int(row['day']):02d} ({row['year']})")
        print(f"Station:       {row['station_id']}")
        print(f"Raw OCR:       {row['raw_ocr']}")
        print(f"Normalized:    {row['normalized']}")
        print(f"Confidence:    {row['confidence']}")
        print(f"Reason:        {row['validation_reason']}")
        print(f"Image:         {image_path}")

        open_image(image_path)

        while True:
            choice = input("\n[a]ccept  [c]orrect  [s]kip  [q]uit: ").strip().lower()

            if choice == "a":
                value = row["normalized"].strip()
                if not validate_value(value):
                    print("That OCR value is not a valid rainfall number. Use [c] to enter the corrected value.")
                    continue

                decisions[key] = {
                    "station_id": row["station_id"],
                    "year": row["year"],
                    "month": row["month"],
                    "day": row["day"],
                    "raw_ocr": row["raw_ocr"],
                    "ocr_value": row["normalized"],
                    "confidence": row["confidence"],
                    "review_status": "ACCEPTED",
                    "final_value": value,
                    "reviewer_note": "Accepted OCR result during human review.",
                    "image_path": str(image_path),
                }
                break

            if choice == "c":
                value = input("Enter corrected rainfall value (0-1000 mm): ").strip()
                if not validate_value(value):
                    print("Invalid value. Enter a number such as 0, 1.5, 24.0, or 152.0.")
                    continue

                note = input("Optional note: ").strip()
                decisions[key] = {
                    "station_id": row["station_id"],
                    "year": row["year"],
                    "month": row["month"],
                    "day": row["day"],
                    "raw_ocr": row["raw_ocr"],
                    "ocr_value": row["normalized"],
                    "confidence": row["confidence"],
                    "review_status": "ACCEPTED",
                    "final_value": value,
                    "reviewer_note": note or "Corrected during human review.",
                    "image_path": str(image_path),
                }
                break

            if choice == "s":
                decisions[key] = {
                    "station_id": row["station_id"],
                    "year": row["year"],
                    "month": row["month"],
                    "day": row["day"],
                    "raw_ocr": row["raw_ocr"],
                    "ocr_value": row["normalized"],
                    "confidence": row["confidence"],
                    "review_status": "SKIPPED",
                    "final_value": "",
                    "reviewer_note": "Skipped for later review.",
                    "image_path": str(image_path),
                }
                break

            if choice == "q":
                save_decisions(decisions_path, decisions)
                rebuild_final(queue_rows, decisions, final_path)
                print("\nProgress saved.")
                print(f"Decisions: {decisions_path}")
                print(f"Final CSV: {final_path}")
                return

            print("Please enter a, c, s, or q.")

        save_decisions(decisions_path, decisions)
        rebuild_final(queue_rows, decisions, final_path)
        print("Decision saved.")

    save_decisions(decisions_path, decisions)
    rebuild_final(queue_rows, decisions, final_path)

    accepted = sum(1 for d in decisions.values() if d["review_status"] == "ACCEPTED")
    skipped = sum(1 for d in decisions.values() if d["review_status"] == "SKIPPED")

    print("\n" + "=" * 42)
    print("REVIEW COMPLETE")
    print(f"Accepted: {accepted}")
    print(f"Skipped:  {skipped}")
    print(f"Final CSV: {final_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Review questionable rainfall OCR results.")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--final", type=Path, default=DEFAULT_FINAL)
    args = parser.parse_args()

    review(args.queue, args.decisions, args.final)


if __name__ == "__main__":
    main()
