#!/usr/bin/env python3

import sys

sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
sys.stdout.reconfigure(encoding='utf-8')

def clean(s):
    s = s.strip()
    return '' if s.lower() in ('null', 'none', '') else s

for line in sys.stdin:
    f = line.rstrip('\n').split('\t')
    if len(f) >= 6:
        # books_hdfs format (0: nguon, 1: thuong_hieu, 2: gia_ban, 3: gia_goc, 4: ten_sach, 5: tinh_trang)
        nguon = clean(f[0])
        thuong_hieu = clean(f[1])
        gia_ban_str = f[2].strip()
    elif len(f) == 4:
        # overview_hdfs format (0: _id, 1: thuong_hieu, 2: gia_ban, 3: nguon)
        thuong_hieu = clean(f[1])
        gia_ban_str = f[2].strip()
        nguon = clean(f[3])
    else:
        continue

    print("book\t1")

    try:
        price = float(gia_ban_str)
        if price > 0:
            print(f"price\t{price}")
    except ValueError:
        pass

    if thuong_hieu:
        print(f"pub\t{thuong_hieu}")
    if nguon:
        print(f"src\t{nguon}")
