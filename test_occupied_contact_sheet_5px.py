import csv
import cv2
import math
import numpy as np


MANIFEST = "output/cell_manifest.csv"
OUTPUT = "output/occupied_contact_sheet_5px.png"

THUMB_W = 160
THUMB_H = 90
LABEL_H = 30
COLS = 7


def is_occupied(path):
    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

    if image is None:
        return False

    h, w = image.shape

    if h <= 10 or w <= 10:
        return False

    inner = image[5:h-5, 5:w-5]

    dark = (inner < 205).astype(np.uint8)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        dark,
        connectivity=8
    )

    meaningful = np.zeros_like(dark, dtype=bool)

    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        width = stats[label, cv2.CC_STAT_WIDTH]
        height = stats[label, cv2.CC_STAT_HEIGHT]

        if area < 3:
            continue

        if width >= inner.shape[1] * 0.80:
            continue

        if height >= inner.shape[0] * 0.80:
            continue

        meaningful[labels == label] = True

    ratio = np.count_nonzero(meaningful) / meaningful.size

    return ratio >= 0.004


with open(MANIFEST, newline="") as f:
    rows = list(csv.DictReader(f))


cells = [
    row for row in rows
    if is_occupied(row["path"])
]

rows_needed = math.ceil(len(cells) / COLS)

sheet = np.full(
    (
        rows_needed * (THUMB_H + LABEL_H),
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

    sheet[
        y:y + THUMB_H,
        x:x + THUMB_W
    ] = image

    label = f'{cell["month"][:3]} {cell["day"]}'

    cv2.putText(
        sheet,
        label,
        (x + 5, y + THUMB_H + 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        0,
        1,
        cv2.LINE_AA
    )


cv2.imwrite(OUTPUT, sheet)

print(f"5px candidates: {len(cells)}")
print(f"Contact sheet:  {OUTPUT}")
