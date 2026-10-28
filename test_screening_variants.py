import csv
import cv2
import numpy as np


MANIFEST = "output/cell_manifest.csv"


def analyze(path, border):
    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

    if image is None:
        return False, 0.0

    h, w = image.shape

    if h <= border * 2 or w <= border * 2:
        return False, 0.0

    inner = image[border:h-border, border:w-border]

    dark = (inner < 205).astype(np.uint8)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        dark,
        connectivity=8
    )

    meaningful = np.zeros_like(dark, dtype=bool)

    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        x = stats[label, cv2.CC_STAT_LEFT]
        y = stats[label, cv2.CC_STAT_TOP]
        width = stats[label, cv2.CC_STAT_WIDTH]
        height = stats[label, cv2.CC_STAT_HEIGHT]

        # Ignore tiny noise.
        if area < 3:
            continue

        # Ignore components that look like table borders.
        # Handwritten characters should not normally span
        # most of the cell width or height.
        if width >= inner.shape[1] * 0.80:
            continue

        if height >= inner.shape[0] * 0.80:
            continue

        meaningful[labels == label] = True

    ratio = (
        np.count_nonzero(meaningful) /
        meaningful.size
    )

    return ratio >= 0.004, ratio


with open(MANIFEST, newline="") as f:
    rows = list(csv.DictReader(f))


for border in [3, 5, 7]:

    occupied = 0

    for row in rows:
        result, ratio = analyze(
            row["path"],
            border
        )

        if result:
            occupied += 1

    print(
        f"Border {border}px -> "
        f"{occupied} occupied / "
        f"{len(rows)} total"
    )
