#!/usr/bin/env python3

import sys

sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
sys.stdout.reconfigure(encoding='utf-8')

cur_key = None
total_count = 0

for line in sys.stdin:
    parts = line.rstrip('\n').split('\t')
    if len(parts) != 3:
        continue
    nguon, price_str, count_str = parts
    key = f"{nguon}\t{price_str}"

    try:
        c = int(count_str)
    except ValueError:
        continue

    if key == cur_key:
        total_count += c
    else:
        if cur_key is not None:
            print(f"{cur_key}\t{total_count}")
        cur_key = key
        total_count = c

if cur_key is not None:
    print(f"{cur_key}\t{total_count}")
