chmod +x mapper_overview.py reducer_overview.py
sed -i 's/\r$//' mapper_overview.py reducer_overview.py

hdfs dfs -cat /user/hadoopthanh/books_hdfs/part-m-00000 | ./mapper_overview.py | sort | ./reducer_overview.py

cd ~
hdfs dfs -rm -r -skipTrash /user/hadoopthanh/output_overview 2>/dev/null
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -D mapreduce.job.reduces=1 \
  -files mapper_overview.py,reducer_overview.py \
  -input /user/hadoopthanh/books_hdfs \
  -output /user/hadoopthanh/output_overview \
  -mapper mapper_overview.py \
  -reducer reducer_overview.py

hdfs dfs -cat /user/hadoopthanh/output_overview/part-00000

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "
DROP TABLE IF EXISTS stat_overview;
CREATE TABLE stat_overview (
  chi_so VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin PRIMARY KEY,
  gia_tri DOUBLE NOT NULL
);"

sqoop export \
  --connect "jdbc:mysql://techreview.ddns.net:3306/bigdata?useUnicode=true&characterEncoding=UTF-8" \
  --username bigdata \
  --password 'aP+xZ2FM}_' \
  --table stat_overview \
  --export-dir /user/hadoopthanh/output_overview \
  --input-fields-terminated-by '\t' \
  --columns "chi_so,gia_tri" \
  --m 1

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "SELECT * FROM stat_overview;"

## Giải thích Chi tiết Từng Dòng Code MapReduce

### 1. `mapper_overview.py`

```python
1: #!/usr/bin/env python3
2: 
3: import sys
4: 
5: sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
6: sys.stdout.reconfigure(encoding='utf-8')
7: 
8: def clean(s):
9:     s = s.strip()
10:     return '' if s.lower() in ('null', 'none', '') else s
11: 
12: for line in sys.stdin:
13:     f = line.rstrip('\n').split('\t')
14:     if len(f) >= 6:
15:         # books_hdfs format (0: nguon, 1: thuong_hieu, 2: gia_ban, 3: gia_goc, 4: ten_sach, 5: tinh_trang)
16:         nguon = clean(f[0])
17:         thuong_hieu = clean(f[1])
18:         gia_ban_str = f[2].strip()
19:     elif len(f) == 4:
20:         # overview_hdfs format (0: _id, 1: thuong_hieu, 2: gia_ban, 3: nguon)
21:         thuong_hieu = clean(f[1])
22:         gia_ban_str = f[2].strip()
23:         nguon = clean(f[3])
24:     else:
25:         continue
26: 
27:     print("book\t1")
28: 
29:     try:
30:         price = float(gia_ban_str)
31:         if price > 0:
32:             print(f"price\t{price}")
33:     except ValueError:
34:         pass
35: 
36:     if thuong_hieu:
37:         print(f"pub\t{thuong_hieu}")
38:     if nguon:
39:         print(f"src\t{nguon}")
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1-6**: Khai báo môi trường Python 3 và cấu hình UTF-8 cho luồng đọc/ghi `sys.stdin`/`sys.stdout`.
- **Dòng 8-10 (`def clean(s): ...`)**: Định nghĩa hàm làm sạch chuỗi: loại bỏ khoảng trắng thừa hai đầu và gán thành chuỗi rỗng `''` nếu chuỗi ban đầu chứa các từ khóa nạp lỗi như `'null'`, `'none'`, `''`.
- **Dòng 12 (`for line in sys.stdin:`)**: Đọc từng dòng bản ghi đầu vào.
- **Dòng 13 (`f = line.rstrip('\n').split('\t')`)**: Loại bỏ ký tự xuống dòng và tách các trường bằng dấu tab.
- **Dòng 14-18 (`if len(f) >= 6:`)**: Xử lý định dạng dữ liệu 6 cột (`books_hdfs`): trích xuất nguồn `f[0]`, thương hiệu `f[1]` và giá bán raw `f[2]`.
- **Dòng 19-23 (`elif len(f) == 4:`)**: Xử lý định dạng dữ liệu 4 cột (`overview_hdfs`): trích xuất thương hiệu `f[1]`, giá bán raw `f[2]` và nguồn `f[3]`.
- **Dòng 24-25 (`else: continue`)**: Bỏ qua dòng nếu số cột không khớp với một trong hai cấu hình dữ liệu trên.
- **Dòng 27 (`print("book\t1")`)**: Phát ra cặp Key-Value `book<TAB>1` để phục vụ đếm tổng số cuốn sách.
- **Dòng 29-34 (`try...except ValueError: pass`)**: Ép kiểu giá bán sang số thực `float`, nếu `price > 0` thì phát ra `price<TAB><price>` để Reducer tính trung bình giá.
- **Dòng 36-37 (`if thuong_hieu: print(...)`)**: Nếu có thông tin nhà xuất bản/thương hiệu, phát ra `pub<TAB><thuong_hieu>` để tính số lượng NXB duy nhất.
- **Dòng 38-39 (`if nguon: print(...)`)**: Nếu có thông tin nguồn dữ liệu, phát ra `src<TAB><nguon>` để tính số lượng nguồn duy nhất.

---

### 2. `reducer_overview.py`

```python
1: #!/usr/bin/env python3
2: 
3: import sys
4: 
5: sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
6: sys.stdout.reconfigure(encoding='utf-8')
7: 
8: so_sach = 0
9: gia_sum, gia_cnt = 0.0, 0
10: pubs, srcs = set(), set()
11: 
12: for line in sys.stdin:
13:     parts = line.rstrip('\n').split('\t', 1)
14:     if len(parts) != 2:
15:         continue
16:     k, v = parts
17:     if k == 'book':
18:         so_sach += 1
19:     elif k == 'price':
20:         try:
21:             gia_sum += float(v)
22:             gia_cnt += 1
23:         except ValueError:
24:             pass
25:     elif k == 'pub':
26:         pubs.add(v)
27:     elif k == 'src':
28:         srcs.add(v)
29: 
30: print(f"so_sach\t{so_sach}")
31: print(f"gia_ban_trung_binh\t{(gia_sum / gia_cnt) if gia_cnt else 0:.2f}")
32: print(f"so_nha_xuat_ban\t{len(pubs)}")
33: print(f"so_nguon\t{len(srcs)}")
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1-6**: Khai báo Shebang chỉ định môi trường thực thi và cấu hình UTF-8 cho luồng dữ liệu.
- **Dòng 8 (`so_sach = 0`)**: Khởi tạo biến đếm tổng số cuốn sách.
- **Dòng 9 (`gia_sum, gia_cnt = 0.0, 0`)**: Khởi tạo tổng giá bán (`gia_sum`) và số lượng sách có giá bán (`gia_cnt`) để tính trung bình.
- **Dòng 10 (`pubs, srcs = set(), set()`)**: Khởi tạo 2 tập hợp (`set`) để lưu danh sách các nhà xuất bản duy nhất (`pubs`) và nguồn duy nhất (`srcs`).
- **Dòng 12 (`for line in sys.stdin:`)**: Đọc từng cặp Key-Value được chuyển sang Reducer.
- **Dòng 13-15 (`parts = line.rstrip('\n').split('\t', 1)...`)**: Tách dòng thành Key `k` và Value `v`.
- **Dòng 17-18 (`if k == 'book': so_sach += 1`)**: Nếu Key là `'book'`, tăng biến tổng số sách thêm 1.
- **Dòng 19-24 (`elif k == 'price': ...`)**: Nếu Key là `'price'`, cộng dồn giá trị vào `gia_sum` và tăng `gia_cnt` lên 1.
- **Dòng 25-26 (`elif k == 'pub': pubs.add(v)`)**: Nếu Key là `'pub'`, thêm tên nhà xuất bản vào tập hợp `pubs` (tự động loại bỏ trùng lặp).
- **Dòng 27-28 (`elif k == 'src': srcs.add(v)`)**: Nếu Key là `'src'`, thêm tên nguồn vào tập hợp `srcs` (tự động loại bỏ trùng lặp).
- **Dòng 30 (`print(f"so_sach\t{so_sach}")`)**: In ra chỉ số tổng số sách (`so_sach`).
- **Dòng 31 (`print(f"gia_ban_trung_binh\t...")`)**: In ra giá bán trung bình toàn bộ hệ thống (`gia_sum / gia_cnt`), làm tròn 2 số thập phân.
- **Dòng 32 (`print(f"so_nha_xuat_ban\t{len(pubs)}")`)**: In ra tổng số nhà xuất bản khác nhau (kích thước của tập hợp `pubs`).
- **Dòng 33 (`print(f"so_nguon\t{len(srcs)}")`)**: In ra tổng số nguồn dữ liệu khác nhau (kích thước của tập hợp `srcs`).

