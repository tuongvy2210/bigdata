#!/usr/bin/env python3

import sys

sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
sys.stdout.reconfigure(encoding='utf-8')

current_key = None
current_count = 0

for line in sys.stdin:
    parts = line.rstrip('\n').split('\t', 1)
    if len(parts) != 2:
        continue
    key = parts[0].strip()
    try:
        count = int(parts[1].strip())
    except ValueError:
        continue

    if current_key == key:
        current_count += count
    else:
        if current_key is not None:
            print(f"{current_key}\t{current_count}")
        current_key = key
        current_count = count

if current_key is not None:
    print(f"{current_key}\t{current_count}")
