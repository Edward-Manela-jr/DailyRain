import cv2
import os


IMAGE = "test_data/testimage.png"
OUTPUT = "test_data/benchmark"

# Known cells from the Chikuni sheet.
#
# Format:
# name: (x1, x2, y1, y2)
#
# These use the existing detected grid boundaries.
cells = {
    "jan3_6_5":   (558, 635, 276, 313),
    "jan5_38_0":  (558, 635, 349, 387),

    # Other known values from the sheet
    "nov3_2_5":   (403, 481, 276, 313),
    "jan6_11_5":  (558, 635, 386, 422),
    "jan7_24_0":  (558, 635, 422, 458),
    "jan17_44_0": (558, 635, 782, 818),

    "dec30_152":  (481, 558, 1212, 1249),
    "oct18_16":   (326, 403, 818, 854),
    "apr19_43_5": (791, 869, 854, 890),
    "nov13_23":   (403, 481, 639, 674),
}


def main():

    image = cv2.imread(
        IMAGE,
        cv2.IMREAD_GRAYSCALE
    )

    if image is None:
        raise FileNotFoundError(
            f"Could not read {IMAGE}"
        )

    os.makedirs(
        OUTPUT,
        exist_ok=True
    )

    for name, (x1, x2, y1, y2) in cells.items():

        cell = image[y1:y2, x1:x2]

        path = os.path.join(
            OUTPUT,
            f"{name}.png"
        )

        cv2.imwrite(
            path,
            cell
        )

        print(
            f"{name}: "
            f"{cell.shape[1]}x{cell.shape[0]} "
            f"-> {path}"
        )


if __name__ == "__main__":
    main()
