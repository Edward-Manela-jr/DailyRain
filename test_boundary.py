import cv2
import os

image_path = "test_data/testimage.png"
output_path = "test_data/extracted/jan_cell_6_5_reproduced.png"

image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

if image is None:
    raise FileNotFoundError(image_path)

# Exact coordinates of the previously successful 6.5 cell
x1, x2 = 558, 636
y1, y2 = 276, 312

cell = image[y1:y2, x1:x2]

os.makedirs(
    os.path.dirname(output_path),
    exist_ok=True
)

cv2.imwrite(output_path, cell)

print("Created:", output_path)
print("Dimensions:", cell.shape)
