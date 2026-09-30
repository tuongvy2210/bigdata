#!/usr/bin/env python3

import sys

sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
sys.stdout.reconfigure(encoding='utf-8')

cur_nguon = None
max_price = -1.0
max_name = ""

for line in sys.stdin:
    parts = line.rstrip('\n').split('\t', 2)
    if len(parts) != 3:
        continue

    nguon, price_str, ten_sach = parts
    try:
        price = float(price_str)
    except ValueError:
        continue

    if nguon == cur_nguon:
        if price > max_price:
            max_price = price
            max_name = ten_sach
    else:
        if cur_nguon is not None:
            print(f"{cur_nguon}\t{max_price:.2f}\t{max_name}")
        cur_nguon = nguon
        max_price = price
        max_name = ten_sach

if cur_nguon is not None:
    print(f"{cur_nguon}\t{max_price:.2f}\t{max_name}")
