#!/usr/bin/env python3
"""Reduce sorted client/year rows into annual energy and peak summaries."""
import itertools
import math
import sys


def reduce_rows(source, destination):
    records = (line.rstrip("\n").split("\t") for line in source)
    for key, group in itertools.groupby(records, key=lambda record: record[0]):
        count = 0
        energy_values = []
        max_daily = peak_kw = 0.0
        for record in group:
            if len(record) != 4:
                raise ValueError("Expected key, daily energy, max daily energy, peak kW")
            energy, daily_peak, interval_peak = map(float, record[1:])
            if any(not math.isfinite(value) or value < 0 for value in (energy, daily_peak, interval_peak)):
                raise ValueError("Invalid partial aggregate")
            count += 1
            energy_values.append(energy)
            max_daily = max(max_daily, daily_peak)
            peak_kw = max(peak_kw, interval_peak)
        total = math.fsum(energy_values)
        client, year = key.rsplit("|", 1)
        print(f"{client}\t{year}\t{count}\t{total!r}\t{total / count!r}\t{max_daily!r}\t{peak_kw!r}",
              file=destination)


if __name__ == "__main__":
    reduce_rows(sys.stdin, sys.stdout)
