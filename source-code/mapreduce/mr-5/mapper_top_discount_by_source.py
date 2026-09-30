#!/usr/bin/env python3

import sys

sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
sys.stdout.reconfigure(encoding='utf-8')

for line in sys.stdin:
    f = line.rstrip('\n').split('\t')
    if len(f) >= 6:
        # books_hdfs format (0: nguon, 1: thuong_hieu, 2: gia_ban, 3: gia_goc, 4: ten_sach, 5: tinh_trang)
        nguon = f[0].strip()
        gia_ban_raw = f[2].strip()
        gia_goc_raw = f[3].strip()
        ten_sach = f[4].strip().replace('\t', ' ').replace('\n', ' ')
    elif len(f) == 4:
        # mapreduce_discount_hdfs format (0: nguon, 1: gia_goc, 2: gia_ban, 3: ten_sach)
        nguon = f[0].strip()
        gia_goc_raw = f[1].strip()
        gia_ban_raw = f[2].strip()
        ten_sach = f[3].strip().replace('\t', ' ').replace('\n', ' ')
    else:
        continue

    if not nguon or nguon.lower() in ('', 'null', 'none'):
        nguon = 'Không rõ'
        
    try:
        gb = float(gia_ban_raw)
        gg = float(gia_goc_raw)
    except ValueError:
        continue

    if gg <= 0 or gb <= 0 or gg <= gb:
        continue

    so_tien_giam = gg - gb
    ty_le_giam = (so_tien_giam / gg) * 100.0
    print(f"{nguon}\t{ty_le_giam:.4f}\t{gg:.2f}\t{gb:.2f}\t{so_tien_giam:.2f}\t{ten_sach}")
