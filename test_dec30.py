import cv2
import os

IMAGE = "test_data/testimage.png"
OUTPUT = "test_data/dec30_correct.png"

image = cv2.imread(IMAGE, cv2.IMREAD_GRAYSCALE)

if image is None:
    raise FileNotFoundError(f"Could not read {IMAGE}")

# December 30
x1, x2 = 481, 558
y1, y2 = 1249, 1285

cell = image[y1:y2, x1:x2]

os.makedirs("test_data", exist_ok=True)

cv2.imwrite(OUTPUT, cell)

print(f"Saved: {OUTPUT}")
print(f"Size: {cell.shape[1]}x{cell.shape[0]}")
