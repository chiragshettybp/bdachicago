#!/usr/bin/env python3
"""Map daily client energy into annual client groups. Input: daily.tsv."""
import math
import sys


def map_rows(source, destination):
    for number, line in enumerate(source, 1):
        fields = line.rstrip("\n").split("\t")
        if len(fields) != 6:
            raise ValueError(f"Expected six fields at line {number}")
        day, client, intervals, energy, _, peak = fields
        if len(day) != 10 or day[4] != "-" or int(intervals) != 96:
            raise ValueError(f"Invalid daily record at line {number}")
        total, peak_kw = float(energy), float(peak)
        if not math.isfinite(total) or not math.isfinite(peak_kw) or total < 0 or peak_kw < 0:
            raise ValueError(f"Invalid reading at line {number}")
        print(f"{client}|{day[:4]}\t{total!r}\t{total!r}\t{peak_kw!r}", file=destination)


if __name__ == "__main__":
    map_rows(sys.stdin, sys.stdout)
