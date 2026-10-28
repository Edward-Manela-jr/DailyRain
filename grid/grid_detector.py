import cv2
import numpy as np


def detect_grid(image_path):
    """
    Detect the horizontal and vertical table boundaries
    in the Chikuni rainfall record.

    Returns:
        horizontal_lines
        vertical_lines
    """

    image = cv2.imread(
        image_path,
        cv2.IMREAD_GRAYSCALE
    )

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {image_path}"
        )

    # --------------------------------------------------
    # Threshold the image
    # --------------------------------------------------

    binary = cv2.adaptiveThreshold(
        image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        21,
        8
    )

    # --------------------------------------------------
    # Restrict processing to the rainfall table
    #
    # These are the approximate Phase 2 table bounds.
    # --------------------------------------------------

    table_x1 = 45
    table_y1 = 170
    table_x2 = 1032
    table_y2 = 1330

    table = binary[
        table_y1:table_y2,
        table_x1:table_x2
    ]

    # --------------------------------------------------
    # Detect horizontal lines
    # --------------------------------------------------

    horizontal_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (80, 1)
    )

    horizontal = cv2.morphologyEx(
        table,
        cv2.MORPH_OPEN,
        horizontal_kernel
    )

    horizontal_projection = np.sum(
        horizontal > 0,
        axis=1
    )

    horizontal_positions = np.where(
        horizontal_projection > table.shape[1] * 0.25
    )[0]

    # Group neighboring pixels into one line
    horizontal_lines = _group_positions(
        horizontal_positions
    )

    # Convert table-relative coordinates back to
    # original image coordinates.
    horizontal_lines = [
        y + table_y1
        for y in horizontal_lines
    ]

    # --------------------------------------------------
    # Detect vertical lines
    # --------------------------------------------------

    vertical_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (1, 80)
    )

    vertical = cv2.morphologyEx(
        table,
        cv2.MORPH_OPEN,
        vertical_kernel
    )

    vertical_projection = np.sum(
        vertical > 0,
        axis=0
    )

    vertical_positions = np.where(
        vertical_projection > table.shape[0] * 0.25
    )[0]

    vertical_lines = _group_positions(
        vertical_positions
    )

    vertical_lines = [
        x + table_x1
        for x in vertical_lines
    ]

    return horizontal_lines, vertical_lines


def _group_positions(positions):
    """
    Convert consecutive pixel positions into
    one representative coordinate per line.
    """

    if len(positions) == 0:
        return []

    groups = []

    current_group = [positions[0]]

    for position in positions[1:]:

        if position <= current_group[-1] + 2:
            current_group.append(position)

        else:
            groups.append(current_group)
            current_group = [position]

    groups.append(current_group)

    # Use the center of each detected line
    centers = [
        int(round(np.mean(group)))
        for group in groups
    ]

    return centers