import cv2
import os

from grid.grid_detector import detect_grid


MONTHS = [
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
]


def extract_cells(image_path, output_directory):
    """
    Detect the rainfall table grid and extract all
    daily/monthly cells.

    The first vertical interval is the DAY column.
    The remaining 12 intervals are the rainfall
    month columns.

    Returns a list containing information about
    every extracted cell.
    """

    horizontal, vertical = detect_grid(image_path)

    if len(horizontal) != 33:
        raise RuntimeError(
            f"Expected 33 horizontal boundaries, "
            f"found {len(horizontal)}"
        )

    if len(vertical) != 14:
        raise RuntimeError(
            f"Expected 14 vertical boundaries, "
            f"found {len(vertical)}"
        )

    image = cv2.imread(
        image_path,
        cv2.IMREAD_GRAYSCALE
    )

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {image_path}"
        )

    os.makedirs(
        output_directory,
        exist_ok=True
    )

    cells = []

    # --------------------------------------------------
    # Vertical intervals
    #
    # vertical[0] -> vertical[1] = DAY column
    # vertical[1] -> vertical[2] = JULY
    # ...
    # vertical[12] -> vertical[13] = JUNE
    # --------------------------------------------------

    for row_index in range(32):

        y1 = horizontal[row_index]
        y2 = horizontal[row_index + 1]

        # Row 0 is the header area.
        # Rows 1-31 are the daily rainfall rows.
        if row_index == 0:
            continue

        day = row_index

        for month_index, month in enumerate(MONTHS):

            column_index = month_index + 1

            x1 = vertical[column_index]
            x2 = vertical[column_index + 1]

            cell = image[
                y1:y2,
                x1:x2
            ]

            month_directory = os.path.join(
                output_directory,
                month
            )

            os.makedirs(
                month_directory,
                exist_ok=True
            )

            filename = f"day_{day:02d}.png"

            output_path = os.path.join(
                month_directory,
                filename
            )

            cv2.imwrite(
                output_path,
                cell
            )

            cells.append({
                "month": month,
                "day": day,
                "path": output_path,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
            })

    return cells