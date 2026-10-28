import csv
import cv2
import numpy as np


MANIFEST = "output/cell_manifest.csv"


def get_ratio(path, border):
    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

    if image is None:
        return 0.0

    h, w = image.shape

    if h <= border * 2 or w <= border * 2:
        return 0.0

    inner = image[border:h-border, border:w-border]

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

    return np.count_nonzero(meaningful) / meaningful.size


with open(MANIFEST, newline="") as f:
    rows = list(csv.DictReader(f))


results = []

for row in rows:

    ratio3 = get_ratio(row["path"], 3)
    ratio5 = get_ratio(row["path"], 5)
    ratio7 = get_ratio(row["path"], 7)

    occupied3 = ratio3 >= 0.004
    occupied5 = ratio5 >= 0.004
    occupied7 = ratio7 >= 0.004

    results.append({
        "month": row["month"],
        "day": row["day"],
        "path": row["path"],
        "3px": occupied3,
        "5px": occupied5,
        "7px": occupied7,
        "ratio3": ratio3,
        "ratio5": ratio5,
        "ratio7": ratio7,
    })


print("\nCELLS REMOVED BY 5px BUT KEPT BY 3px")
print("=" * 70)

for r in results:
    if r["3px"] and not r["5px"]:
        print(
            f'{r["month"]:9s} day {int(r["day"]):2d} | '
            f'3px={r["ratio3"]:.4f} | '
            f'5px={r["ratio5"]:.4f}'
        )


print("\nCELLS REMOVED BY 7px BUT KEPT BY 5px")
print("=" * 70)

for r in results:
    if r["5px"] and not r["7px"]:
        print(
            f'{r["month"]:9s} day {int(r["day"]):2d} | '
            f'5px={r["ratio5"]:.4f} | '
            f'7px={r["ratio7"]:.4f}'
        )
