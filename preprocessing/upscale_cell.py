
import cv2
import os


def upscale_cell(input_path, output_path, scale=4):
    """Upscale an extracted cell without thresholding the handwriting."""
    image = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)

    if image is None:
        raise FileNotFoundError(f"Could not read image: {input_path}")

    image = cv2.copyMakeBorder(
        image, 5, 5, 5, 5,
        cv2.BORDER_CONSTANT,
        value=255,
    )

    enlarged = cv2.resize(
        image,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC,
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not cv2.imwrite(output_path, enlarged):
        raise RuntimeError(f"Could not write {output_path}")

    return output_path
