#!/usr/bin/env python3

import sys

sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
sys.stdout.reconfigure(encoding='utf-8')

cur_kg = None
total_count = 0

for line in sys.stdin:
    parts = line.rstrip('\n').split('\t')
    if len(parts) != 2:
        continue

    kg, count_str = parts
    try:
        c = int(count_str.strip())
    except ValueError:
        continue

    if kg == cur_kg:
        total_count += c
    else:
        if cur_kg is not None:
            print(f"{cur_kg}\t{total_count}")
        cur_kg = kg
        total_count = c

if cur_kg is not None:
    print(f"{cur_kg}\t{total_count}")
