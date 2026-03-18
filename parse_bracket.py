import re
import json
from collections import Counter

#############################################
# STEP 1: INPUT RAW TEXT
#############################################
raw_text = """PASTE ESPN DUMP HERE"""

# Normalize apostrophes/quotes
raw_text = raw_text.replace("\u2019", "'").replace("\u2018", "'").replace("'", "'")

#############################################
# STEP 2: TEAM DEFINITIONS
# (region, seed, canonical_name, name_regex)
#
# Seeds anchor every search — e.g. "1 Michigan" vs "3 Michigan St"
# are already distinct by seed, so most negative lookaheads are
# just extra safety for substring cases.
#############################################
TEAMS = [
    # EAST
    ("East",    1,  "Duke",                r"Duke"),
    ("East",    2,  "UConn",               r"UConn"),
    ("East",    3,  "Michigan State",      r"Michigan\s+St(?:ate)?"),
    ("East",    4,  "Kansas",              r"Kansas"),
    ("East",    5,  "St. John's",          r"St\.?\s*John"),
    ("East",    6,  "Louisville",          r"Louisville"),
    ("East",    7,  "UCLA",                r"UCLA"),
    ("East",    8,  "Ohio State",          r"Ohio\s+State"),
    ("East",    9,  "TCU",                 r"TCU"),
    ("East",    10, "UCF",                 r"UCF"),
    ("East",    11, "South Florida",       r"South\s+Florida"),
    ("East",    12, "Northern Iowa",       r"Northern\s+Iowa"),
    ("East",    13, "Cal Baptist",         r"C[Aa]\.?\s*Baptist"),
    ("East",    14, "North Dakota State",  r"N(?:orth)?\s*\.?\s*Dakota\s+St"),
    ("East",    15, "Furman",              r"Furman"),
    ("East",    16, "Siena",               r"Siena"),
    # WEST
    ("West",    1,  "Arizona",             r"Arizona"),
    ("West",    2,  "Purdue",              r"Purdue"),
    ("West",    3,  "Gonzaga",             r"Gonzaga"),
    ("West",    4,  "Arkansas",            r"Arkansas"),
    ("West",    5,  "Wisconsin",           r"Wisconsin"),
    ("West",    6,  "BYU",                 r"BYU"),
    ("West",    7,  "Miami (FL)",          r"Miami(?!\s*\(?OH)"),
    ("West",    8,  "Villanova",           r"Villanova"),
    ("West",    9,  "Utah State",          r"Utah\s+State"),
    ("West",    10, "Missouri",            r"Missouri"),
    ("West",    11, "Texas/NC State",      r"TEX/NCSU|Texas\s*/\s*NC"),
    ("West",    12, "High Point",          r"High\s+Point"),
    ("West",    13, "Hawai'i",             r"Hawai.i"),
    ("West",    14, "Kennesaw State",      r"Kennesaw\s+St(?:ate)?"),
    ("West",    15, "Queens",              r"Queens"),
    ("West",    16, "Long Island",         r"Long\s+Island"),
    # MIDWEST
    ("Midwest", 1,  "Michigan",            r"Michigan(?!\s+St)"),
    ("Midwest", 2,  "Iowa State",          r"Iowa\s+State"),
    ("Midwest", 3,  "Virginia",            r"Virginia"),
    ("Midwest", 4,  "Alabama",             r"Alabama"),
    ("Midwest", 5,  "Texas Tech",          r"Texas\s+Tech"),
    ("Midwest", 6,  "Tennessee",           r"Tennessee(?!\s+St)"),
    ("Midwest", 7,  "Kentucky",            r"Kentucky"),
    ("Midwest", 8,  "Georgia",             r"Georgia"),
    ("Midwest", 9,  "Saint Louis",         r"Saint\s+Louis"),
    ("Midwest", 10, "Santa Clara",         r"Santa\s+Clara"),
    ("Midwest", 11, "Miami (OH)/SMU",      r"M-OH/SMU|Miami\s*\(?OH"),
    ("Midwest", 12, "Akron",               r"Akron"),
    ("Midwest", 13, "Hofstra",             r"Hofstra"),
    ("Midwest", 14, "Wright State",        r"Wright\s+St(?:ate)?"),
    ("Midwest", 15, "Tennessee State",     r"Tennessee\s+St(?:ate)?"),
    ("Midwest", 16, "UMBC/Howard",         r"UMBC(?:/HOW)?"),
    # SOUTH
    ("South",   1,  "Florida",             r"Florida"),
    ("South",   2,  "Houston",             r"Houston"),
    ("South",   3,  "Illinois",            r"Illinois"),
    ("South",   4,  "Nebraska",            r"Nebraska"),
    ("South",   5,  "Vanderbilt",          r"Vanderbilt"),
    ("South",   6,  "North Carolina",      r"North\s+Carolina"),
    ("South",   7,  "Saint Mary's",        r"Saint\s+Mary"),
    ("South",   8,  "Clemson",             r"Clemson"),
    ("South",   9,  "Iowa",                r"Iowa(?!\s+State)"),
    ("South",   10, "Texas A&M",           r"Texas\s+A&M"),
    ("South",   11, "VCU",                 r"VCU"),
    ("South",   12, "McNeese",             r"McNeese"),
    ("South",   13, "Troy",                r"Troy"),
    ("South",   14, "Penn",                r"Penn(?!\s+State)"),
    ("South",   15, "Idaho",               r"Idaho"),
    ("South",   16, "Prairie View/Lehigh", r"PV/LEH|Prairie\s+View"),
]

#############################################
# STEP 3: COUNT seed-anchored occurrences
#
# Pattern: \bSEED\s+TEAM_NAME
# The seed number makes each pattern specific to
# exactly one team even when names are substrings.
#############################################
team_counts = {}
for region, seed, canonical, name_pat in TEAMS:
    pat = r'\b' + str(seed) + r'\s+(?:' + name_pat + r')'
    team_counts[(region, seed)] = len(re.findall(pat, raw_text, re.IGNORECASE))

#############################################
# STEP 4: DETECT CHAMPION
# Look for any team name in the ~50 chars before "Champion"
#############################################
champion = None
champ_match = re.search(r'(.{3,60}?)\s*Champion', raw_text, re.IGNORECASE)
if champ_match:
    ctx = champ_match.group(1)
    for region, seed, canonical, name_pat in TEAMS:
        if re.search(name_pat, ctx, re.IGNORECASE):
            champion = (region, seed)
            break

#############################################
# STEP 5: BUILD PICKS
#
# Count interpretation (each appearance = 1 round played):
#   count 1 → lost R64           (0 wins)
#   count 2 → lost R32           (won R64)
#   count 3 → lost S16           (won R64, R32)
#   count 4 → lost E8            (won R64, R32, S16)
#   count 5 → lost FF            (won R64, R32, S16, E8)
#   count 6 → finalist           (won R64, R32, S16, E8, FF)
#   "Champion" label → CHAMP pick
#
# A team contributes one pick per round it WON.
#############################################
ROUND_THRESHOLDS = [
    ("R64", 2),
    ("R32", 3),
    ("S16", 4),
    ("E8",  5),
    ("FF",  6),
]

picks = []
for region, seed, canonical, _ in TEAMS:
    count = team_counts[(region, seed)]
    for rnd, threshold in ROUND_THRESHOLDS:
        if count >= threshold:
            picks.append({"round": rnd, "winnerRegion": region, "winnerSeed": seed})

if champion:
    picks.append({"round": "CHAMP", "winnerRegion": champion[0], "winnerSeed": champion[1]})

#############################################
# STEP 6: VALIDATION + OUTPUT
#############################################
EXPECTED = {"R64": 32, "R32": 16, "S16": 8, "E8": 4, "FF": 2, "CHAMP": 1}
round_counts = Counter(p["round"] for p in picks)

print("=== Picks per round ===")
for rnd, exp in EXPECTED.items():
    got = round_counts.get(rnd, 0)
    status = "✓" if got == exp else f"⚠️  expected {exp}"
    print(f"  {rnd:5s}: {got}  {status}")

# Debug: show teams with unexpected counts
print("\n=== Team counts (non-1 losers) ===")
for region, seed, canonical, _ in TEAMS:
    c = team_counts[(region, seed)]
    if c == 0:
        print(f"  ⚠️  {region} {seed} {canonical}: count={c}  (NOT FOUND — check abbreviation)")
    elif c > 1:
        print(f"  {region} {seed} {canonical}: count={c}")

print("\n=== JSON output ===")
print(json.dumps({"picks": picks}, indent=2))
