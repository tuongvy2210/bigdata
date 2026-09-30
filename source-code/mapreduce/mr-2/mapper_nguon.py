#!/usr/bin/env python3

import sys

sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
sys.stdout.reconfigure(encoding='utf-8')

for line in sys.stdin:
    fields = line.rstrip('\n').split('\t')
    if len(fields) < 1:
        continue
    nguon = fields[0].strip()
    if nguon and nguon.lower() not in ('none', 'null', ''):
        print(f"{nguon}\t1")
