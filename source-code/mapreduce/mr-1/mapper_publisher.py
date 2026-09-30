#!/usr/bin/env python3

import sys

sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
sys.stdout.reconfigure(encoding='utf-8')

for line in sys.stdin:
    f = line.rstrip('\n').split('\t')

    if len(f) < 6:
        continue

    thuong_hieu = f[1].strip()
    gia_ban_raw = f[2].strip()

    if not thuong_hieu or thuong_hieu.lower() in ('none', 'null', ''):
        thuong_hieu = 'Không rõ'

    if not gia_ban_raw or gia_ban_raw.lower() in ('none', 'null', ''):
        continue

    try:
        gia_ban = float(gia_ban_raw)

        if gia_ban > 0:
            print(f"{thuong_hieu}\t{gia_ban}")

    except ValueError:
        continue
