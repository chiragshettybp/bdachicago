#!/usr/bin/env python3
"""Reduce sorted service request rows into annual summaries."""
import itertools
import math
import sys


def reduce_rows(source, destination):
    records = (line.rstrip("\n").split("\t") for line in source)
    for key, group in itertools.groupby(records, key=lambda record: record[0]):
        days = 0
        request_values = []
        max_daily = 0
        resolution_days = 0.0
        completed = 0
        for record in group:
            if len(record) != 5:
                raise ValueError("Expected key, daily requests, max daily requests, resolution days, completed")
            daily_requests, daily_peak, daily_resolution, daily_completed = map(float, record[1:])
            if any(not math.isfinite(value) or value < 0 for value in (daily_requests, daily_peak, daily_resolution, daily_completed)):
                raise ValueError("Invalid partial aggregate")
            days += 1
            request_values.append(daily_requests)
            max_daily = max(max_daily, daily_peak)
            resolution_days += daily_resolution
            completed += int(daily_completed)
        total = math.fsum(request_values)
        avg_resolution = resolution_days / completed if completed else 0.0
        sr_type, year = key.rsplit("|", 1)
        print(f"{sr_type}\t{year}\t{days}\t{total!r}\t{total / days!r}\t{max_daily!r}\t{avg_resolution!r}",
              file=destination)


if __name__ == "__main__":
    reduce_rows(sys.stdin, sys.stdout)
