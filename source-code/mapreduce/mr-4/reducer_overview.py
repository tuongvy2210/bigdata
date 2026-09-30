#!/usr/bin/env python3

import sys

sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
sys.stdout.reconfigure(encoding='utf-8')

so_sach = 0
gia_sum, gia_cnt = 0.0, 0
pubs, srcs = set(), set()

for line in sys.stdin:
    parts = line.rstrip('\n').split('\t', 1)
    if len(parts) != 2:
        continue
    k, v = parts
    if k == 'book':
        so_sach += 1
    elif k == 'price':
        try:
            gia_sum += float(v)
            gia_cnt += 1
        except ValueError:
            pass
    elif k == 'pub':
        pubs.add(v)
    elif k == 'src':
        srcs.add(v)

print(f"so_sach\t{so_sach}")
print(f"gia_ban_trung_binh\t{(gia_sum / gia_cnt) if gia_cnt else 0:.2f}")
print(f"so_nha_xuat_ban\t{len(pubs)}")
print(f"so_nguon\t{len(srcs)}")
