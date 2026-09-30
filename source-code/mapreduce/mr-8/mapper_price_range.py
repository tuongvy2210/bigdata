#!/usr/bin/env python3

import sys

sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
sys.stdout.reconfigure(encoding='utf-8')

for line in sys.stdin:
    f = line.rstrip('\n').split('\t')
    if len(f) < 6:
        continue

    gia_ban_raw = f[2].strip()

    try:
        gb = float(gia_ban_raw)
        if gb < 100000:
            kg = "0 - 100.000 VNĐ"
        elif gb < 200000:
            kg = "100.000 - 200.000 VNĐ"
        elif gb < 300000:
            kg = "200.000 - 300.000 VNĐ"
        elif gb < 500000:
            kg = "300.000 - 500.000 VNĐ"
        else:
            kg = "Trên 500.000 VNĐ"
        print(f"{kg}\t1")
    except ValueError:
        continue
