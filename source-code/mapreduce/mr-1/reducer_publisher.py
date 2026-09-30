#!/usr/bin/env python3

import sys

sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
sys.stdout.reconfigure(encoding='utf-8')

current_publisher = None
total_price = 0.0
count = 0

for line in sys.stdin:
    parts = line.rstrip('\n').split('\t', 1)

    if len(parts) != 2:
        continue

    publisher = parts[0].strip()
    price_str = parts[1].strip()

    try:
        price = float(price_str)
    except ValueError:
        continue

    if current_publisher == publisher:
        total_price += price
        count += 1
    else:
        if current_publisher is not None and count > 0:
            avg_price = total_price / count
            print(f"{current_publisher}\t{avg_price:.2f}")

        current_publisher = publisher
        total_price = price
        count = 1

if current_publisher is not None and count > 0:
    avg_price = total_price / count
    print(f"{current_publisher}\t{avg_price:.2f}")
