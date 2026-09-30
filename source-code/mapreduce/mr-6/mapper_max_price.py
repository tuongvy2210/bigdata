#!/usr/bin/env python3

import sys

sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
sys.stdout.reconfigure(encoding='utf-8')

for line in sys.stdin:
    f = line.rstrip('\n').split('\t')
    if len(f) < 6:
        continue

    nguon = f[0].strip()
    gia_ban_raw = f[2].strip()
    ten_sach = f[4].strip().replace('\t', ' ').replace('\n', ' ')

    if not nguon or nguon.lower() in ('', 'null', 'none'):
        nguon = 'Không rõ'

    try:
        gb = float(gia_ban_raw)
        if gb > 0:
            print(f"{nguon}\t{gb:.2f}\t{ten_sach}")
    except ValueError:
        continue
