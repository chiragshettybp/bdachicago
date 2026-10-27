#!/usr/bin/env python3
"""Map daily service request counts into annual groups. Input: daily.tsv."""
import math
import sys


def map_rows(source, destination):
    for number, line in enumerate(source, 1):
        fields = line.rstrip("\n").split("\t")
        if len(fields) != 6:
            raise ValueError(f"Expected six fields at line {number}")
        day, sr_type, requests, completed, canceled, resolution = fields
        if len(day) != 10 or day[4] != "-" or not sr_type:
            raise ValueError(f"Invalid daily record at line {number}")
        try:
            request_count = int(requests)
            completed_count = int(completed)
            resolution_days = float(resolution)
        except ValueError as error:
            raise ValueError(f"Invalid reading at line {number}") from error
        if request_count < 0 or completed_count < 0 or resolution_days < 0:
            raise ValueError(f"Invalid reading at line {number}")
        year = day[:4]
        print(f"{sr_type}|{year}\t{request_count}\t{request_count}\t{resolution_days}\t{completed_count}",
              file=destination)


if __name__ == "__main__":
    map_rows(sys.stdin, sys.stdout)
