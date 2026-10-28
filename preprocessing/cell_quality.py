
"""Lightweight cell screening.

This intentionally does not try to 'perfect' handwriting. Its job is only
to decide whether a cell is probably blank before spending an OCR request.
"""

import cv2
import numpy as np


def has_ink(image_path, threshold=205, min_ratio=0.004):
    """
    Return True when the interior of a cell contains meaningful dark pixels.

    A small border is ignored because the extracted cell may still contain
    part of the printed grid line.
    """
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Could not read {image_path}")

    if image.shape[0] <= 8 or image.shape[1] <= 8:
        return False

    inner = image[3:-3, 3:-3]
    dark = inner < threshold

    # Remove tiny isolated specks without aggressively altering handwriting.
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        dark.astype(np.uint8), connectivity=8
    )

    meaningful = np.zeros_like(dark, dtype=bool)
    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        if area >= 3:
            meaningful[labels == label] = True

    ratio = float(np.count_nonzero(meaningful)) / meaningful.size
    return ratio >= min_ratio
