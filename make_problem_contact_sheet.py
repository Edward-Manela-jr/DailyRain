import cv2
import os

INPUT_DIR = "test_data/problem_variants_upscaled"
OUTPUT = "test_data/problem_contact_sheet.png"

files = [
    "jan17_original.png",
    "jan17_xshort.png",
    "jan17_xwide.png",
    "jan17_yshort.png",
    "jan17_ywide.png",
    "dec30_original.png",
    "dec30_xshort.png",
    "dec30_xwide.png",
    "dec30_yshort.png",
    "dec30_ywide.png",
]

images = []

for filename in files:

    path = os.path.join(INPUT_DIR, filename)

    if not os.path.exists(path):
        print(f"Missing: {filename}")
        continue

    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

    # Enlarge display size if necessary
    image = cv2.resize(
        image,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_NEAREST
    )

    # Add a white area above for filename
    label_height = 40

    canvas = cv2.copyMakeBorder(
        image,
        label_height,
        0,
        0,
        0,
        cv2.BORDER_CONSTANT,
        value=255
    )

    cv2.putText(
        canvas,
        filename,
        (10, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        0,
        2
    )

    images.append(canvas)


# Make all images the same width
max_width = max(img.shape[1] for img in images)

normalized = []

for img in images:

    if img.shape[1] < max_width:

        img = cv2.copyMakeBorder(
            img,
            0,
            0,
            0,
            max_width - img.shape[1],
            cv2.BORDER_CONSTANT,
            value=255
        )

    normalized.append(img)


# Stack vertically
contact_sheet = cv2.vconcat(normalized)

cv2.imwrite(
    OUTPUT,
    contact_sheet
)

print()
print(f"Created: {OUTPUT}")
print(f"Images: {len(images)}")
