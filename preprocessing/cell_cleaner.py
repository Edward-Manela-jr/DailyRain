import cv2
import numpy as np
import os


def clean_cell(input_path, output_directory, scale=4):
    """
    Create several preprocessing stages for one table cell.

    Outputs:
        inner   = cell with outer table borders cropped away
        cleaned = thresholded version with remaining long lines removed
    """

    image = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {input_path}"
        )

    os.makedirs(output_directory, exist_ok=True)

    height, width = image.shape

    # ==================================================
    # STAGE 1 — INNER CROP
    # ==================================================
    #
    # Remove the outer edges where the table grid exists.
    #
    # We deliberately do NOT threshold the image yet.
    #

    x_margin = int(width * 0.08)
    y_margin = int(height * 0.12)

    inner = image[
        y_margin:height - y_margin,
        x_margin:width - x_margin
    ]

    inner_path = os.path.join(
        output_directory,
        "test_cell_inner.png"
    )

    cv2.imwrite(inner_path, inner)

    # ==================================================
    # STAGE 2 — LIGHT CLEANING
    # ==================================================

    blurred = cv2.GaussianBlur(
        inner,
        (3, 3),
        0
    )

    binary = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        21,
        7
    )

    # --------------------------------------------------
    # Detect long horizontal lines
    # --------------------------------------------------

    horizontal_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (max(15, inner.shape[1] // 4), 1)
    )

    horizontal_lines = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        horizontal_kernel
    )

    # --------------------------------------------------
    # Detect long vertical lines
    # --------------------------------------------------

    vertical_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (1, max(15, inner.shape[0] // 4))
    )

    vertical_lines = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        vertical_kernel
    )

    # --------------------------------------------------
    # Remove detected lines
    # --------------------------------------------------

    cleaned = binary.copy()

    cleaned[horizontal_lines > 0] = 0
    cleaned[vertical_lines > 0] = 0

    # ==================================================
    # STAGE 3 — CROP AROUND REMAINING INK
    # ==================================================

    points = cv2.findNonZero(cleaned)

    if points is not None:

        x, y, w, h = cv2.boundingRect(points)

        padding = 8

        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(cleaned.shape[1], x + w + padding)
        y2 = min(cleaned.shape[0], y + h + padding)

        cleaned = cleaned[y1:y2, x1:x2]

    # ==================================================
    # STAGE 4 — WHITE BACKGROUND / BLACK HANDWRITING
    # ==================================================

    cleaned = cv2.bitwise_not(cleaned)

    # ==================================================
    # STAGE 5 — UPSCALE
    # ==================================================

    cleaned = cv2.resize(
        cleaned,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC
    )

    cleaned_path = os.path.join(
        output_directory,
        "test_cell_cleaned.png"
    )

    cv2.imwrite(
        cleaned_path,
        cleaned
    )

    return {
        "inner": inner_path,
        "cleaned": cleaned_path
    }