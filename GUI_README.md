
# RainfallDigitizer — GUI Version

Run the whole-image OCR pipeline with a graphical human-review interface.

## Prerequisites

- Python 3.10+
- Virtual environment already set up (`.venv/`)
- Mathpix credentials in `.env` (`MATHPIX_APP_ID`, `MATHPIX_APP_KEY`)
- Internet access (Mathpix API is called once per sheet)

## Install dependencies

```bash
source .venv/bin/activate
pip install pillow
```

## Run the GUI

```bash
source .venv/bin/activate
python gui/main.py
```

## GUI workflow

| Step | Action |
|------|--------|
| 1 | Click **Load Sheet Image** — select your rainfall sheet (e.g. `test_data/testimage.png`) |
| 2 | Click **Run Whole-Image OCR** — sends the full sheet to Mathpix in **one API call**, parses the table, and writes `output_gui/rainfall_records.csv` |
| 3 | Review cells in the list — color-coded by flag: |
|   | 🟡 Yellow = `review` — OCR value detected, verify before accepting |
|   | 🔴 Red = `empty` — no value detected, human must type it in |
| 4 | Click a cell — see its cropped preview on the right |
| 5 | Edit the value, then: **Accept** / **Correct** / **Skip** / **Mark OK** |
| 6 | Click **Save Final CSV** — writes your corrected `rainfall_records.csv` |

## Output files

- `output_gui/rainfall_records.csv` — all 372 cells, sorted by year → month → day, with columns:
  `station_id, year, month, day, MAX, MIN, RAINFALL, flag`
- `output_gui/review_queue.csv` — same rows plus OCR evidence (`raw_ocr`, `normalized`, `confidence`, `validation_status`, etc.)
- `output_gui/run_summary.json` — run statistics

## Flag meanings

| Flag | Count (test image) | Meaning | GUI color |
|------|-------------------|---------|-----------|
| `review` | 66 | Value detected by OCR | Yellow — verify |
| `empty` | 306 | No value detected | Red — fill in manually |

## Example test run

```bash
source .venv/bin/activate
python whole_image_ocr/main.py test_data/testimage.png
python gui/main.py
```

Then in the GUI: **Run Whole-Image OCR** → review the 66 yellow + 306 red cells → **Save Final CSV**.

## Known values (benchmark) for spot-checking

| Month | Day | Expected |
|-------|-----|----------|
| february | 1 | 18.0 |
| january | 3 | 6.5 |
| january | 5 | 38.0 |
| october | 3 | 1.0 |
| december | 30 | 152.0 |

## Security

- Never commit `.env` — it contains Mathpix API credentials.
- The `.env` file is in `.gitignore`.
