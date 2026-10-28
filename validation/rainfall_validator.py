
"""Validation and review-status rules for OCR results."""

from dataclasses import dataclass


@dataclass
class ValidationResult:
    status: str
    reason: str


def validate_rainfall(normalized_value, confidence=None):
    """
    Decide whether a recognized cell can be accepted automatically.

    This is deliberately conservative. A high OCR confidence does not prove
    that the digit is correct, so the system retains raw OCR and supports
    human review.
    """
    if normalized_value is None:
        return ValidationResult("REVIEW", "OCR result could not be normalized.")

    try:
        value = float(normalized_value)
    except (TypeError, ValueError):
        return ValidationResult("REVIEW", "Normalized value is not numeric.")

    if value < 0 or value > 1000:
        return ValidationResult("REVIEW", "Value outside sanity range.")

    if confidence is None:
        return ValidationResult("REVIEW", "OCR confidence unavailable.")

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        return ValidationResult("REVIEW", "Invalid OCR confidence.")

    if confidence < 0.90:
        return ValidationResult(
            "REVIEW",
            f"OCR confidence {confidence:.3f} is below 0.900.",
        )

    return ValidationResult("ACCEPT", "OCR result passed basic validation.")
