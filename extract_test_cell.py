import cv2
import os


# Original Chikuni rainfall image
input_path = "test_data/testimage.png"

# Output directory
output_dir = "test_data/extracted"
os.makedirs(output_dir, exist_ok=True)


# Exact cell containing the handwritten 6.5
#
# x1 = 558
# y1 = 276
# x2 = 636
# y2 = 312
#
# These coordinates are based on the detected table grid.

x1 = 558
y1 = 276
x2 = 636
y2 = 312


image = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)

if image is None:
    raise FileNotFoundError(
        f"Could not read image: {input_path}"
    )


cell = image[y1:y2, x1:x2]


output_path = os.path.join(
    output_dir,
    "jan_cell_6_5_original.png"
)

cv2.imwrite(output_path, cell)


print("Exact cell extracted successfully.")
print(f"Size: {cell.shape[1]} x {cell.shape[0]}")
print(f"Saved to: {output_path}")