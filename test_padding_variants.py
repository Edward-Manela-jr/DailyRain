import cv2
import os

IMAGE = "test_data/testimage.png"
OUTPUT = "test_data/padding_variants"

image = cv2.imread(IMAGE, cv2.IMREAD_GRAYSCALE)

if image is None:
    raise FileNotFoundError(f"Could not read {IMAGE}")

os.makedirs(OUTPUT, exist_ok=True)

cells = {
    "jan17": (558, 635, 782, 818),
    "dec30": (481, 558, 1212, 1249),
}

padding_sizes = [2, 4, 6, 8]

for cell_name, (x1, x2, y1, y2) in cells.items():

    cell = image[y1:y2, x1:x2]

    for padding in padding_sizes:

        padded = cv2.copyMakeBorder(
            cell,
            padding,
            padding,
            padding,
            padding,
            cv2.BORDER_CONSTANT,
            value=255
        )

        filename = f"{cell_name}_pad{padding}.png"
        path = os.path.join(OUTPUT, filename)

        cv2.imwrite(path, padded)

        print(
            f"{filename}: "
            f"{padded.shape[1]}x{padded.shape[0]}"
        )

print("\nDone.")
