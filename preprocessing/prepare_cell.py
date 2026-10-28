import cv2
import os


def prepare_cell(input_path, output_path, scale=4, crop=1):
    """
    Prepare an extracted rainfall cell for OCR.

    Processing:
    1. Read the original cell in grayscale.
    2. Remove a very small edge around the cell.
    3. Add a white border.
    4. Upscale using cubic interpolation.

    The small crop is intended to remove table-line remnants
    without damaging the handwritten rainfall value.
    """

    image = cv2.imread(
        input_path,
        cv2.IMREAD_GRAYSCALE
    )

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {input_path}"
        )

    height, width = image.shape

    if height <= crop * 2 or width <= crop * 2:
        raise ValueError(
            "Cell is too small for the requested crop."
        )

    # Remove only the outer edge.
    image = image[
        crop:height - crop,
        crop:width - crop
    ]

    # Add a small white border.
    image = cv2.copyMakeBorder(
        image,
        5,
        5,
        5,
        5,
        cv2.BORDER_CONSTANT,
        value=255
    )

    # Upscale.
    enlarged = cv2.resize(
        image,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC
    )

    output_directory = os.path.dirname(output_path)

    if output_directory:
        os.makedirs(
            output_directory,
            exist_ok=True
        )

    cv2.imwrite(
        output_path,
        enlarged
    )

    return output_path
