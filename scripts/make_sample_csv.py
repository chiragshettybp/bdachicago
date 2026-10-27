"""Generate a realistic Chicago 311 sample CSV for local testing.

Uses real request types, short codes, owner departments, origins, and addresses
taken from the City of Chicago 311 Service Requests dataset so the dashboard
preview mirrors real data.
"""

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


BASE_TYPES = [
    ("311 INFORMATION ONLY CALL", "311IOC", "311 City Services", 26, None),
    ("Aircraft Noise Complaint", "AVN", "Aviation", 14, None),
    ("Graffiti Removal Request", "GRAF", "Streets and Sanitation", 10, 7),
    ("Pothole in Street Complaint", "PHF", "CDOT - Department of Transportation", 8, 3),
    ("Street Light Out Complaint", "SFD", "CDOT - Department of Transportation", 7, 12),
    ("Garbage Cart Maintenance", "SIE", "Streets and Sanitation", 6, 8),
    ("Rodent Baiting/Rat Complaint", "SGA", "Streets and Sanitation", 6, 6),
    ("Abandoned Vehicle Complaint", "SKA", "Streets and Sanitation", 5, 5),
    ("Tree Debris Clean-Up Request", "SEL", "Streets and Sanitation", 4, 10),
    ("Traffic Signal Out Complaint", "SFB", "CDOT - Department of Transportation", 3, 11),
    ("Building Violation", "BBA", "DOB - Buildings", 3, 4),
    ("Water Lead Test Kit Request", "WCA2", "DWM - Department of Water Management", 2, 5),
    ("Dead Animal Pick-Up Request", "SGQ", "Streets and Sanitation", 1, None),
]
TOTAL_WEIGHT = sum(t[3] for t in BASE_TYPES)

ORIGINS = [
    ("Phone Call", 0.57), ("Internet", 0.27), ("Mobile Device", 0.08),
    ("Alderman's Office", 0.05), ("Generated In House", 0.03),
]
STREETS = [
    "WESTERN", "ASHLAND", "KEDZIE", "MILWAUKEE", "HALSTED", "DAMEN",
    "CALIFORNIA", "MICHIGAN", "PULASKI", "ARCHER", "CLARK", "PAULINA",
    "STATE", "CAMPBELL", "INDIANA", "BELMONT", "ALBANY", "RACINE",
]
STREET_TYPES = ["ST", "AVE", "RD", "PL", "BLVD", "DR"]
DIRECTIONS = ["N", "S", "W", "E"]
ZIPS = ["60608", "60612", "60617", "60618", "60620", "60623", "60625", "60629", "60632", "60647"]


def _pick_origin():
    roll = random.random()
    cumulative = 0.0
    for origin, share in ORIGINS:
        cumulative += share
        if roll <= cumulative:
            return origin
    return "Phone Call"


def _seasonal_factor(month, peak):
    if peak is None:
        return 1.0
    distance = abs(((month - peak + 6) % 12) - 6)
    return 1.5 if distance <= 1 else 0.7


def _status(origin_type):
    if origin_type == "311 INFORMATION ONLY CALL":
        roll = random.random()
        return "Completed" if roll < 0.99 else "Canceled"
    roll = random.random()
    if roll < 0.88:
        return "Completed"
    if roll < 0.95:
        return "Open"
    return "Canceled"


def _address(origin_type):
    if origin_type == "311 INFORMATION ONLY CALL":
        return "2111 W LEXINGTON ST", "60612"
    if origin_type == "Aircraft Noise Complaint":
        return "10510 W ZEMKE RD", "60666"
    number = random.randint(1, 99) * 100
    direction = random.choice(DIRECTIONS)
    street = random.choice(STREETS)
    suffix = random.choice(STREET_TYPES)
    return f"{number} {direction} {street} {suffix}", random.choice(ZIPS)


def make_sample(output, start="2023-01-01", end="2025-06-30", base_per_day=40, seed=11):
    random.seed(seed)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    day = datetime.strptime(start, "%Y-%m-%d")
    last_day = datetime.strptime(end, "%Y-%m-%d")
    serial = random.randint(1_000_000, 5_000_000)
    rows = []
    while day <= last_day:
        years_elapsed = (day - datetime(2023, 1, 1)).days / 365.0
        trend = 1.0 + 0.04 * years_elapsed
        weekday = 1.15 if day.weekday() < 5 else 0.85
        for sr_type, short_code, department, weight, peak in BASE_TYPES:
            expected = (base_per_day * weight / TOTAL_WEIGHT * trend
                        * weekday * _seasonal_factor(day.month, peak))
            count = max(0, int(random.gauss(expected, max(1.0, expected * 0.5))))
            for _ in range(count):
                created = day + timedelta(
                    hours=random.randint(6, 21), minutes=random.randint(0, 59)
                )
                status = _status(sr_type)
                if status == "Completed":
                    if sr_type == "311 INFORMATION ONLY CALL":
                        closed = created + timedelta(minutes=random.randint(1, 30))
                    else:
                        closed = created + timedelta(hours=random.randint(2, 240))
                else:
                    closed = ""
                origin = _pick_origin()
                address, zip_code = _address(sr_type)
                serial += 1
                rows.append([
                    f"SR{created.strftime('%y')}-{serial:08d}",
                    sr_type, short_code,
                    "311 City Services" if origin in ("Phone Call", "Internet", "Mobile Device") else "",
                    department, status, origin,
                    created.isoformat(), (closed or created).isoformat(),
                    closed.isoformat() if closed else "",
                    address, "Chicago", "IL", zip_code,
                ])
        day += timedelta(days=1)

    header = [
        "SR_NUMBER", "SR_TYPE", "SR_SHORT_CODE", "CREATED_DEPARTMENT",
        "OWNER_DEPARTMENT", "STATUS", "ORIGIN", "CREATED_DATE",
        "LAST_MODIFIED_DATE", "CLOSED_DATE", "STREET_ADDRESS", "CITY",
        "STATE", "ZIP_CODE",
    ]
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"Wrote {len(rows)} sample rows to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/source/sample_311.csv")
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default="2025-06-30")
    parser.add_argument("--base-per-day", type=int, default=40)
    args = parser.parse_args()
    make_sample(args.output, args.start, args.end, args.base_per_day)
