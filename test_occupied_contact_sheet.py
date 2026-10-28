import csv
import os
import cv2
import math
import numpy as np

MANIFEST = "output/cell_manifest.csv"
OUTPUT = "output/occupied_contact_sheet.png"

THUMB_W = 160
THUMB_H = 90
LABEL_H = 30
COLS = 7


# Read occupied cells
cells = []

with open(MANIFEST, newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row["occupied"].strip().lower() == "true":
            cells.append(row)


ROWS = math.ceil(len(cells) / COLS)

sheet = cv2.imread(cells[0]["path"], cv2.IMREAD_GRAYSCALE)

if sheet is None:
    raise RuntimeError("Could not read first cell image.")




contact_sheet = np.full(
    (
        ROWS * (THUMB_H + LABEL_H),
        COLS * THUMB_W
    ),
    255,
    dtype=np.uint8
)







for i, cell in enumerate(cells):

    image = cv2.imread(
        cell["path"],
        cv2.IMREAD_GRAYSCALE
    )

    if image is None:
        continue

    image = cv2.resize(
        image,
        (THUMB_W, THUMB_H)
    )

    x = (i % COLS) * THUMB_W
    y = (i // COLS) * (THUMB_H + LABEL_H)

    contact_sheet[
        y:y + THUMB_H,
        x:x + THUMB_W
    ] = image

    label = f'{cell["month"][:3]} {cell["day"]}'

    cv2.putText(
        contact_sheet,
        label,
        (x + 5, y + THUMB_H + 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        0,
        1,
        cv2.LINE_AA
    )


os.makedirs(
    os.path.dirname(OUTPUT),
    exist_ok=True
)

cv2.imwrite(
    OUTPUT,
    contact_sheet
)

print(f"Occupied cells: {len(cells)}")
print(f"Contact sheet:  {OUTPUT}")
