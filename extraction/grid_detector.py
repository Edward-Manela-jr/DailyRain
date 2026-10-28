
"""Grid detection wrapper used by the Phase 4 pipeline."""

from grid.grid_detector import detect_grid


def detect_rainfall_grid(image_path):
    """Return detected horizontal and vertical table boundaries."""
    horizontal, vertical = detect_grid(image_path)

    if len(horizontal) != 33:
        raise RuntimeError(
            f"Expected 33 horizontal boundaries for this form, "
            f"found {len(horizontal)}."
        )

    if len(vertical) != 14:
        raise RuntimeError(
            f"Expected 14 vertical boundaries for this form, "
            f"found {len(vertical)}."
        )

    return horizontal, vertical
