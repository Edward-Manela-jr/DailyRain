import cv2
import os


IMAGE = "test_data/testimage.png"
OUTPUT = "test_data/problem_variants"

image = cv2.imread(
    IMAGE,
    cv2.IMREAD_GRAYSCALE
)

os.makedirs(
    OUTPUT,
    exist_ok=True
)


cells = {
    "jan17": (558, 635, 782, 818),
    "dec30": (481, 558, 1249, 1285),
}


variants = {
    "original": (0, 0, 0, 0),
    "xwide":    (0, 1, 0, 0),
    "xshort":   (1, 0, 0, 0),
    "ywide":    (0, 0, 0, 1),
    "yshort":   (0, 0, 1, 0),
}


for cell_name, (x1, x2, y1, y2) in cells.items():

    for variant_name, (left, right, top, bottom) in variants.items():

        xx1 = x1 - left
        xx2 = x2 + right
        yy1 = y1 - top
        yy2 = y2 + bottom

        cell = image[yy1:yy2, xx1:xx2]

        filename = (
            f"{cell_name}_{variant_name}.png"
        )

        path = os.path.join(
            OUTPUT,
            filename
        )

        cv2.imwrite(
            path,
            cell
        )

        print(
            f"{filename}: "
            f"{cell.shape[1]}x{cell.shape[0]}"
        )
