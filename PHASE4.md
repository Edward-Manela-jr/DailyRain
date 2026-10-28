
# RainfallDigitizer — Phase 4

Phase 4 changes the project from individual OCR experiments into an
end-to-end pipeline prototype.

## Pipeline

image
-> grid detection
-> cell extraction
-> blank-cell screening
-> 4x upscaling
-> OCR provider
-> normalization
-> validation
-> CSV + review queue

## Run

Activate the virtual environment first:

```bash
source .venv/bin/activate
```

Then:

```bash
python main.py test_data/testimage.png
```

The pipeline expects the existing Chikuni rainfall form layout.

## Output

```text
output/
├── cells/
│   ├── july/
│   ├── august/
│   └── ...
├── ocr/
│   └── ...
├── rainfall_records.csv
├── review_queue.csv
└── run_summary.json
```

`rainfall_records.csv` uses the required schema:

```text
station_id,year,month,day,MAX,MIN,RAINFALL
```

`review_queue.csv` preserves the OCR text, confidence, cell path and reason
for anything that should be checked by a human.

## Important design principle

The pipeline does not attempt to perfect every individual handwriting cell.
OCR is treated as one component in a larger process.

A difficult cell is allowed to become:

```text
REVIEW
```

rather than forcing the OCR engine to produce a value.

## Current limitations

1. The current grid detector is tuned to the Chikuni form family.
2. Automatic acceptance uses OCR confidence plus basic numeric validation.
3. Confidence does not guarantee correctness; future phases should add
   stronger validation, including monthly-total reconciliation where the
   source form provides reliable totals.
4. Human review UI is not implemented yet.
5. Other OCR providers are not implemented yet, but the provider boundary
   is kept separate so they can be added later.


## Phase 4.1

`--screen-only` now writes `output/cell_manifest.csv` containing all extracted
cells, their coordinates, and the blank/non-blank screening decision.
No OCR requests are made in screen-only mode.
