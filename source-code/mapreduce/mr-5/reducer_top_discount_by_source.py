#!/usr/bin/env python3
import sys
sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
sys.stdout.reconfigure(encoding='utf-8')
 
def emit(nguon, b):
    ty_le, gg, gb, giam, ten = b
    print(f"{nguon}\t{ty_le:.2f}\t{gg:.2f}\t{gb:.2f}\t{giam:.2f}\t{ten}")
 
cur, best = None, None
for line in sys.stdin:
    f = line.rstrip('\n').split('\t', 5)
    if len(f) != 6:
        continue
    nguon = f[0]
    try:
        rec = (float(f[1]), float(f[2]), float(f[3]), float(f[4]), f[5])
    except ValueError:
        continue
    if nguon != cur:
        if cur is not None:
            emit(cur, best)
        cur, best = nguon, rec
    elif (rec[0], rec[3]) > (best[0], best[3]):
        best = rec
if cur is not None:
    emit(cur, best)
