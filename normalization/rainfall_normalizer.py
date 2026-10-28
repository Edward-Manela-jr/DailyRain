
"""Normalize common Mathpix representations into rainfall numbers."""

import re


def normalize_rainfall(text):
    """
    Convert OCR text such as:
      '\\( 6 \\cdot 5 \\)' -> '6.5'
      '\\( 152 \\cdot 0 \\)' -> '152.0'
      '38.0' -> '38.0'

    Returns None when a reliable numeric value cannot be extracted.
    """
    if not text:
        return None

    value = text.strip()

    value = value.replace(r"\(", "")
    value = value.replace(r"\)", "")
    value = value.replace("$", "")
    value = value.replace(r"\,", "")
    value = value.replace(r"\cdot", ".")
    value = value.replace(r"\times", ".")
    value = value.replace("·", ".")
    value = value.replace("•", ".")
    value = value.replace("−", "-")
    value = value.replace(",", ".")
    value = re.sub(r"\s+", "", value)

    # Prefer a normal decimal/integer number.
    match = re.search(r"(?<!\d)(\d+(?:\.\d+)?)(?!\d)", value)
    if not match:
        return None

    number = match.group(1)

    try:
        numeric = float(number)
    except ValueError:
        return None

    # Daily rainfall is non-negative. Keep the upper bound generous so
    # unusual heavy-rain events are not rejected just because of a
    # conservative threshold.
    if numeric < 0 or numeric > 1000:
        return None

    # Store consistently as one decimal place.
    return f"{numeric:.1f}"
