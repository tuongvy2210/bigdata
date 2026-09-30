#!/usr/bin/env python3

import sys

sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
sys.stdout.reconfigure(encoding='utf-8')

for line in sys.stdin:
    fields = line.rstrip('\n').split('\t')
    if len(fields) < 6:
        continue
    tinh_trang = fields[5].strip()
    if not tinh_trang or tinh_trang.lower() in ('none', 'null', ''):
        tinh_trang = 'Không rõ'
    print(f"{tinh_trang[:100]}\t1")
