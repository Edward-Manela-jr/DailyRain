
"""CLI entry point for whole-image RainfallDigitizer OCR experiment."""

import argparse
import json
import os
import sys

# Allow imports from the parent project (existing validation/normalization).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from whole_image_ocr.extract import extract_sheet, write_outputs


def main():
    parser = argparse.ArgumentParser(
        description="Whole-image rainfall sheet OCR (experiment)."
    )

    parser.add_argument(
        "image",
        help="Path to the rainfall sheet image.",
    )

    parser.add_argument(
        "--output",
        default="output_whole_image",
        help="Output directory (default: output_whole_image).",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("RAINFALLDIGITIZER - WHOLE-IMAGE OCR (EXPERIMENT)")
    print("=" * 70)
    print()
    print(f"Sheet:   {args.image}")
    print(f"Output:  {args.output}")
    print()

    result = extract_sheet(args.image)

    records_path, review_path, summary_path = write_outputs(
        args.output, result, args.image
    )

    print("Processing complete.")
    print()
    print(json.dumps(result["stats"], indent=2))
    print()
    print(f"Records: {records_path}")
    print(f"Review:  {review_path}")
    print(f"Summary: {summary_path}")
    print()
    print("Only ONE Mathpix API call was made (whole image).")


if __name__ == "__main__":
    main()
