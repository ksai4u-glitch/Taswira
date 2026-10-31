"""
One place for the settings every Taswira script shares.
Change AREA or the dates here and every stage (fetch, save, clean, map) follows.
"""

API_VERSION = "26.1"          # stable yearly GED release (covers events up to the end of 2025)

# Preliminary GED Candidate releases for the months after the stable release, oldest first.
# "26.01.26.06" is the quarterly release for January-June 2026; "26.0.7" and "26.0.8" are the
# monthly releases after it. The weekly GitHub Actions job (update_candidates.py) adds new
# monthly versions here automatically; you can also add one by hand.
# Set to [] to leave preliminary data out entirely.
CANDIDATE_VERSIONS = ["26.01.26.06", "26.0.7", "26.0.8", "26.0.9"]

# African countries by Gleditsch-Ward code (the codes the API's Country filter uses)
AFRICA = [
    402, 403, 404, 411, 420, 432, 433, 434, 435, 436, 437, 438, 439,  # West
    450, 451, 452, 461, 471, 475, 481, 482, 483, 484, 490,            # West / Central
    500, 501, 510, 516, 517, 520, 522, 530, 531,                      # East / Horn
    540, 541, 551, 552, 553, 560, 565, 570, 571, 572,                 # Southern
    580, 581, 590, 591,                                               # Indian Ocean
    600, 615, 616, 620, 625, 626, 651,                                # North
]

# Each area: a display name, the countries to fetch, a rough box that every precise
# location must fall inside, and how much heat counts as "hot" per year on the map
# (a bigger area squeezes more events into each pixel, so it needs a higher ceiling).
AREAS = {
    "nigeria": {"name": "Nigeria", "countries": [475],
                "bounds": ((4.0, 2.5), (14.0, 15.0)), "heat_max": 15},
    "africa":  {"name": "Africa", "countries": AFRICA,
                "bounds": ((-35.0, -26.0), (38.0, 60.0)), "heat_max": 60},
}
AREA = "africa"

START_DATE = "2020-01-01"     # the API filters both dates on date_end
END_DATE = "2025-12-31"       # the stable release; Candidate data covers what comes after

PAGE_SIZE = 1000              # events per request; fewer, bigger pages save requests
MAX_REQUESTS = 200            # hard cap per dataset version (at least 1 request per country); the daily limit is 5,000
MAX_REQUESTS_PER_RUN = 2000   # hard cap for one run of a script, all versions and retries included

# Derived values, e.g. "Africa", [402, ...], "2020-2025", "africa_2020-2025"
AREA_NAME = AREAS[AREA]["name"]
COUNTRIES = AREAS[AREA]["countries"]
BOUNDS = AREAS[AREA]["bounds"]
HEAT_MAX = AREAS[AREA]["heat_max"]
FIRST_YEAR, LAST_YEAR = START_DATE[:4], END_DATE[:4]
PERIOD = FIRST_YEAR if FIRST_YEAR == LAST_YEAR else f"{FIRST_YEAR}-{LAST_YEAR}"
FILE_STEM = f"{AREA}_{PERIOD}"
