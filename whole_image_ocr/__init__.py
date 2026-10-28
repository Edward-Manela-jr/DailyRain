
"""Whole-image OCR experiment for RainfallDigitizer.

Sends the full rainfall sheet to an OCR provider once (instead of
cell-by-cell), parses the returned text into rainfall records, and runs
the same validation + review queue as the existing pipeline.

This is a separate experiment — it does not modify the existing pipeline.
"""
