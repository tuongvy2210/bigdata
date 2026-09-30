chmod +x mapper_price_range.py reducer_price_range.py
sed -i 's/\r$//' mapper_price_range.py reducer_price_range.py

cd ~
hdfs dfs -rm -r -skipTrash /user/hadoopthanh/output_price_range 2>/dev/null
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -D mapreduce.job.reduces=1 \
  -files mapper_price_range.py,reducer_price_range.py \
  -input /user/hadoopthanh/books_hdfs \
  -output /user/hadoopthanh/output_price_range \
  -mapper mapper_price_range.py \
  -reducer reducer_price_range.py

hdfs dfs -cat /user/hadoopthanh/output_price_range/part-00000

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "
DROP TABLE IF EXISTS price_range_distribution;
CREATE TABLE price_range_distribution (
  khoang_gia VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin PRIMARY KEY,
  so_luong INT NOT NULL
);"

sqoop export \
  --connect "jdbc:mysql://techreview.ddns.net:3306/bigdata?useUnicode=true&characterEncoding=UTF-8" \
  --username bigdata \
  --password 'aP+xZ2FM}_' \
  --table price_range_distribution \
  --export-dir /user/hadoopthanh/output_price_range \
  --input-fields-terminated-by '\t' \
  --columns "khoang_gia,so_luong" \
  --m 1

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "SELECT * FROM price_range_distribution;"

## Giải thích Chi tiết Từng Dòng Code MapReduce

### 1. `mapper_price_range.py`

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
13:     gia_ban_raw = f[2].strip()
14: 
15:     try:
16:         gb = float(gia_ban_raw)
17:         if gb < 100000:
18:             kg = "0 - 100.000 VNĐ"
19:         elif gb < 200000:
20:             kg = "100.000 - 200.000 VNĐ"
21:         elif gb < 300000:
22:             kg = "200.000 - 300.000 VNĐ"
23:         elif gb < 500000:
24:             kg = "300.000 - 500.000 VNĐ"
25:         else:
26:             kg = "Trên 500.000 VNĐ"
27:         print(f"{kg}\t1")
28:     except ValueError:
29:         continue
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1-6**: Khai báo Shebang chỉ định Python 3 và cấu hình bộ mã hóa UTF-8 cho luồng nhập xuất chuẩn.
- **Dòng 8 (`for line in sys.stdin:`)**: Vòng lặp duyệt qua từng dòng bản ghi dữ liệu HDFS.
- **Dòng 9 (`f = line.rstrip('\n').split('\t')`)**: Cắt ký tự xuống dòng và tách thành các cột theo dấu tab.
- **Dòng 10-11 (`if len(f) < 6: continue`)**: Bỏ qua các dòng không đủ 6 cột dữ liệu.
- **Dòng 13 (`gia_ban_raw = f[2].strip()`)**: Trích xuất cột giá bán (`f[2]`).
- **Dòng 15-16 (`try...gb = float(gia_ban_raw)`)**: Ép kiểu giá bán sang số thực `float`.
- **Dòng 17-26 (`if gb < 100000: ... else: ...`)**: Phân loại mức giá bán `gb` vào 5 khoảng giá tương ứng:
  - `< 100.000 VNĐ`: `"0 - 100.000 VNĐ"`
  - `< 200.000 VNĐ`: `"100.000 - 200.000 VNĐ"`
  - `< 300.000 VNĐ`: `"200.000 - 300.000 VNĐ"`
  - `< 500.000 VNĐ`: `"300.000 - 500.000 VNĐ"`
  - Từ 500.000 VNĐ trở lên: `"Trên 500.000 VNĐ"`
- **Dòng 27 (`print(f"{kg}\t1")`)**: Xuất cặp Key-Value `khoang_gia<TAB>1` ra `stdout`.
- **Dòng 28-29 (`except ValueError: continue`)**: Bỏ qua nếu có lỗi ép kiểu giá bán.

---

### 2. `reducer_price_range.py`

```python
1: #!/usr/bin/env python3
2: 
3: import sys
4: 
5: sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
6: sys.stdout.reconfigure(encoding='utf-8')
7: 
8: cur_kg = None
9: total_count = 0
10: 
11: for line in sys.stdin:
12:     parts = line.rstrip('\n').split('\t')
13:     if len(parts) != 2:
14:         continue
15: 
16:     kg, count_str = parts
17:     try:
18:         c = int(count_str.strip())
19:     except ValueError:
20:         continue
21: 
22:     if kg == cur_kg:
23:         total_count += c
24:     else:
25:         if cur_kg is not None:
26:             print(f"{cur_kg}\t{total_count}")
27:         cur_kg = kg
28:         total_count = c
29: 
30: if cur_kg is not None:
31:     print(f"{cur_kg}\t{total_count}")
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1-6**: Khai báo môi trường Python 3 và cấu hình mã hóa luồng UTF-8.
- **Dòng 8 (`cur_kg = None`)**: Khởi tạo biến lưu khoảng giá đang được xét tích lũy hiện tại.
- **Dòng 9 (`total_count = 0`)**: Khởi tạo biến đếm tổng số cuốn sách thuộc khoảng giá hiện tại.
- **Dòng 11 (`for line in sys.stdin:`)**: Đọc từng dòng dữ liệu từ Hadoop Shuffle & Sort.
- **Dòng 12-14 (`if len(parts) != 2: continue`)**: Bỏ qua dòng nếu không đủ 2 thành phần (Key `kg` và Value `count_str`).
- **Dòng 16-20 (`kg, count_str = parts...`)**: Trích xuất khoảng giá `kg` và ép kiểu `count_str` thành số nguyên `int` (`c`).
- **Dòng 22-23 (`if kg == cur_kg: total_count += c`)**: Nếu dòng mới cùng khoảng giá đang xét, cộng dồn số lượng sách vào `total_count`.
- **Dòng 24-28 (`else:`)**: Khi chuyển sang khoảng giá mới: xuất kết quả `cur_kg<TAB>total_count` ra `stdout`, sau đó cập nhật `cur_kg = kg` và `total_count = c`.
- **Dòng 30-31 (`if cur_kg is not None: print(...)`)**: Xuất tổng số lượng sách cho khoảng giá cuối cùng.

