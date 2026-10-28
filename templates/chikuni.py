
"""Template/profile for the Chikuni rainfall daily record."""

MONTHS = [
    "july", "august", "september", "october", "november", "december",
    "january", "february", "march", "april", "may", "june",
]

# July-December belong to 2021; January-June belong to 2022.
YEAR_BY_MONTH = {
    "july": 2021,
    "august": 2021,
    "september": 2021,
    "october": 2021,
    "november": 2021,
    "december": 2021,
    "january": 2022,
    "february": 2022,
    "march": 2022,
    "april": 2022,
    "may": 2022,
    "june": 2022,
}

STATION_ID = "2554"
STATION_NAME = "CHIKUNI MISSION"

# Used as a starting profile for this form family.
TABLE_BOUNDS = {
    "x1": 45,
    "y1": 170,
    "x2": 1032,
    "y2": 1330,
}
