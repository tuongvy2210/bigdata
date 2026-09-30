chmod +x mapper_price_source.py reducer_price_source.py
sed -i 's/\r$//' mapper_price_source.py reducer_price_source.py

cd ~
hdfs dfs -rm -r -skipTrash /user/hadoopthanh/output_price_source 2>/dev/null
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -D mapreduce.job.reduces=1 \
  -files mapper_price_source.py,reducer_price_source.py \
  -input /user/hadoopthanh/books_hdfs \
  -output /user/hadoopthanh/output_price_source \
  -mapper mapper_price_source.py \
  -reducer reducer_price_source.py

hdfs dfs -cat /user/hadoopthanh/output_price_source/part-00000 | head -n 10

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "
DROP TABLE IF EXISTS price_by_source_scatter;
CREATE TABLE price_by_source_scatter (
  nguon VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  gia_ban DOUBLE NOT NULL,
  so_luong INT NOT NULL
);"

sqoop export \
  --connect "jdbc:mysql://techreview.ddns.net:3306/bigdata?useUnicode=true&characterEncoding=UTF-8" \
  --username bigdata \
  --password 'aP+xZ2FM}_' \
  --table price_by_source_scatter \
  --export-dir /user/hadoopthanh/output_price_source \
  --input-fields-terminated-by '\t' \
  --columns "nguon,gia_ban,so_luong" \
  --m 1

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "SELECT * FROM price_by_source_scatter LIMIT 10;"

## Giải thích Chi tiết Từng Dòng Code MapReduce

### 1. `mapper_price_source.py`

```python
1: #!/usr/bin/env python3
2: 
3: import sys
4: 
5: sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
6: sys.stdout.reconfigure(encoding='utf-8')
7: 
8: for line in sys.stdin:
9:     f = line.rstrip('\n').split('\t')
10:     if len(f) < 6:
11:         continue
12:         
13:     nguon = f[0].strip()
14:     gia_ban_raw = f[2].strip()
15: 
16:     if not nguon or nguon.lower() in ('', 'null', 'none'):
17:         nguon = 'Không rõ'
18:         
19:     try:
20:         gb = float(gia_ban_raw)
21:         if gb >= 0:
22:             print(f"{nguon}\t{gb:.2f}\t1")
23:     except ValueError:
24:         continue
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1-6**: Khai báo môi trường thực thi Python 3 và cấu hình UTF-8 cho luồng đọc/ghi `sys.stdin`/`sys.stdout`.
- **Dòng 8 (`for line in sys.stdin:`)**: Duyệt từng dòng dữ liệu từ HDFS.
- **Dòng 9 (`f = line.rstrip('\n').split('\t')`)**: Cắt ký tự xuống dòng và tách thành danh sách các trường theo dấu tab.
- **Dòng 10-11 (`if len(f) < 6: continue`)**: Bỏ qua dòng dữ liệu bị thiếu cột (ít hơn 6 cột).
- **Dòng 13 (`nguon = f[0].strip()`)**: Trích xuất cột thứ 1 (nguồn dữ liệu).
- **Dòng 14 (`gia_ban_raw = f[2].strip()`)**: Trích xuất cột thứ 3 (giá bán raw).
- **Dòng 16-17 (`if not nguon...`)**: Gán mặc định `'Không rõ'` nếu nguồn dữ liệu bị rỗng hoặc là `null/none`.
- **Dòng 19-24 (`try...except ValueError: continue`)**: Ép kiểu giá bán sang số thực `float` (`gb`). Nếu `gb >= 0`, xuất kết quả ra `stdout` theo dạng 3 thành phần: `nguon<TAB>gb<TAB>1`.

---

### 2. `reducer_price_source.py`

```python
1: #!/usr/bin/env python3
2: 
3: import sys
4: 
5: sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
6: sys.stdout.reconfigure(encoding='utf-8')
7: 
8: cur_key = None
9: total_count = 0
10: 
11: for line in sys.stdin:
12:     parts = line.rstrip('\n').split('\t')
13:     if len(parts) != 3:
14:         continue
15:     nguon, price_str, count_str = parts
16:     key = f"{nguon}\t{price_str}"
17: 
18:     try:
19:         c = int(count_str)
20:     except ValueError:
21:         continue
22: 
23:     if key == cur_key:
24:         total_count += c
25:     else:
26:         if cur_key is not None:
27:             print(f"{cur_key}\t{total_count}")
28:         cur_key = key
29:         total_count = c
30: 
31: if cur_key is not None:
32:     print(f"{cur_key}\t{total_count}")
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1-6**: Khai báo môi trường Python 3 và cấu hình UTF-8.
- **Dòng 8 (`cur_key = None`)**: Khởi tạo biến lưu khóa kết hợp `nguon + gia_ban` đang được xét tích lũy hiện tại.
- **Dòng 9 (`total_count = 0`)**: Khởi tạo biến đếm số lượng sách đạt mức giá đó tại nguồn đó.
- **Dòng 11 (`for line in sys.stdin:`)**: Đọc từng dòng dữ liệu đầu vào đã được Shuffle & Sort theo khóa.
- **Dòng 12-14 (`if len(parts) != 3: continue`)**: Bỏ qua dòng dữ liệu nếu không đúng 3 thành phần (`nguon`, `price_str`, `count_str`).
- **Dòng 15-16 (`key = f"{nguon}\t{price_str}"`)**: Tạo khóa tổng hợp `key` bao gồm nguồn và mức giá bán.
- **Dòng 18-21 (`try...except ValueError: continue`)**: Ép kiểu số đếm `count_str` thành số nguyên `int`.
- **Dòng 23-24 (`if key == cur_key: total_count += c`)**: Nếu dòng mới vẫn có cùng cặp `nguon + gia_ban`, cộng dồn số lượng sách vào `total_count`.
- **Dòng 25-29 (`else:`)**: Khi gặp cặp `nguon + gia_ban` mới: xuất kết quả `cur_key<TAB>total_count` ra `stdout`, sau đó cập nhật `cur_key = key` và `total_count = c`.
- **Dòng 31-32 (`if cur_key is not None: print(...)`)**: Xuất kết quả cho cặp `nguon + gia_ban` cuối cùng.