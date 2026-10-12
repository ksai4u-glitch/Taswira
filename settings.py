"""
One place for the settings every Taswira script shares.
Change the dates here and every stage (fetch, save, clean, map) follows.
"""

API_VERSION = "26.1"          # stable yearly GED release

COUNTRY = 475                 # Nigeria (Gleditsch-Ward code)
COUNTRY_NAME = "Nigeria"

START_DATE = "2015-01-01"     # the API filters both dates on date_end
END_DATE = "2024-12-31"

PAGE_SIZE = 100               # events per request
MAX_REQUESTS = 100            # hard cap for one download; the daily limit is 5,000

# Derived labels, e.g. "2015-2024" and "nigeria_2015-2024"
FIRST_YEAR, LAST_YEAR = START_DATE[:4], END_DATE[:4]
PERIOD = FIRST_YEAR if FIRST_YEAR == LAST_YEAR else f"{FIRST_YEAR}-{LAST_YEAR}"
FILE_STEM = f"{COUNTRY_NAME.lower()}_{PERIOD}"
