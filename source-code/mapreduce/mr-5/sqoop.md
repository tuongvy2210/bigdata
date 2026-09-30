chmod +x mapper_top_discount_by_source.py reducer_top_discount_by_source.py
sed -i 's/\r$//' mapper_top_discount_by_source.py reducer_top_discount_by_source.py

hdfs dfs -cat /user/hadoopthanh/books_hdfs/part-m-00000 | python3 mapper_top_discount_by_source.py | sort -t $'\t' -k1,1 | python3 reducer_top_discount_by_source.py

cd ~
hdfs dfs -rm -r -skipTrash /user/hadoopthanh/output_mapreduce_discount 2>/dev/null
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -D mapreduce.job.reduces=1 \
  -files mapper_top_discount_by_source.py,reducer_top_discount_by_source.py \
  -input /user/hadoopthanh/books_hdfs \
  -output /user/hadoopthanh/output_mapreduce_discount \
  -mapper mapper_top_discount_by_source.py \
  -reducer reducer_top_discount_by_source.py

hdfs dfs -cat /user/hadoopthanh/output_mapreduce_discount/part-00000

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "
DROP TABLE IF EXISTS top_discount_by_source;
CREATE TABLE top_discount_by_source (
  nguon VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin PRIMARY KEY,
  ty_le_giam DOUBLE NOT NULL,
  gia_goc DOUBLE NOT NULL,
  gia_ban DOUBLE NOT NULL,
  so_tien_giam DOUBLE NOT NULL,
  ten_sach TEXT
);"

sqoop export \
  --connect "jdbc:mysql://techreview.ddns.net:3306/bigdata?useUnicode=true&characterEncoding=UTF-8" \
  --username bigdata \
  --password 'aP+xZ2FM}_' \
  --table top_discount_by_source \
  --export-dir /user/hadoopthanh/output_mapreduce_discount \
  --input-fields-terminated-by '\t' \
  --columns "nguon,ty_le_giam,gia_goc,gia_ban,so_tien_giam,ten_sach" \
  --m 1

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "SELECT * FROM top_discount_by_source;"

## Giải thích Chi tiết Từng Dòng Code MapReduce

### 1. `mapper_top_discount_by_source.py`

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
10:     if len(f) >= 6:
11:         # books_hdfs format (0: nguon, 1: thuong_hieu, 2: gia_ban, 3: gia_goc, 4: ten_sach, 5: tinh_trang)
12:         nguon = f[0].strip()
13:         gia_ban_raw = f[2].strip()
14:         gia_goc_raw = f[3].strip()
15:         ten_sach = f[4].strip().replace('\t', ' ').replace('\n', ' ')
16:     elif len(f) == 4:
17:         # mapreduce_discount_hdfs format (0: nguon, 1: gia_goc, 2: gia_ban, 3: ten_sach)
18:         nguon = f[0].strip()
19:         gia_goc_raw = f[1].strip()
20:         gia_ban_raw = f[2].strip()
21:         ten_sach = f[3].strip().replace('\t', ' ').replace('\n', ' ')
22:     else:
23:         continue
24: 
25:     if not nguon or nguon.lower() in ('', 'null', 'none'):
26:         nguon = 'Không rõ'
27:         
28:     try:
29:         gb = float(gia_ban_raw)
30:         gg = float(gia_goc_raw)
31:     except ValueError:
32:         continue
33: 
34:     if gg <= 0 or gb <= 0 or gg <= gb:
35:         continue
36: 
37:     so_tien_giam = gg - gb
38:     ty_le_giam = (so_tien_giam / gg) * 100.0
39:     print(f"{nguon}\t{ty_le_giam:.4f}\t{gg:.2f}\t{gb:.2f}\t{so_tien_giam:.2f}\t{ten_sach}")
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1-6**: Khai báo Shebang môi trường Python 3 và cấu hình UTF-8 cho luồng nhập xuất chuẩn.
- **Dòng 8 (`for line in sys.stdin:`)**: Đọc từng dòng dữ liệu bản ghi từ luồng đầu vào HDFS.
- **Dòng 9 (`f = line.rstrip('\n').split('\t')`)**: Xóa ký tự xuống dòng và tách các trường bằng dấu tab.
- **Dòng 10-15 (`if len(f) >= 6:`)**: Đọc định dạng 6 cột (`books_hdfs`): trích xuất nguồn `f[0]`, giá bán `f[2]`, giá gốc `f[3]`, và làm sạch tên sách `f[4]` (thay tab và xuống dòng bằng khoảng trắng).
- **Dòng 16-21 (`elif len(f) == 4:`)**: Đọc định dạng 4 cột (`mapreduce_discount_hdfs`): trích xuất nguồn `f[0]`, giá gốc `f[1]`, giá bán `f[2]`, và tên sách `f[3]`.
- **Dòng 22-23 (`else: continue`)**: Bỏ qua các bản ghi không khớp với 2 định dạng trên.
- **Dòng 25-26 (`if not nguon...`)**: Chuẩn hóa tên nguồn rỗng/null/none thành `'Không rõ'`.
- **Dòng 28-32 (`try...except ValueError: continue`)**: Ép kiểu giá bán (`gb`) và giá gốc (`gg`) sang số thực `float`, nếu có lỗi dữ liệu thì bỏ qua.
- **Dòng 34-35 (`if gg <= 0 or gb <= 0 or gg <= gb: continue`)**: Lọc điều kiện: chỉ xét các cuốn sách hợp lệ có giảm giá (`gia_goc > gia_ban > 0`).
- **Dòng 37 (`so_tien_giam = gg - gb`)**: Tính số tiền giảm tuyệt đối (`so_tien_giam`).
- **Dòng 38 (`ty_le_giam = (so_tien_giam / gg) * 100.0`)**: Tính tỷ lệ giảm giá theo phần trăm (`ty_le_giam`).
- **Dòng 39 (`print(f"{nguon}\t{ty_le_giam:.4f}\t...")`)**: Xuất thông tin ra `stdout`: `nguon<TAB>ty_le_giam<TAB>gia_goc<TAB>gia_ban<TAB>so_tien_giam<TAB>ten_sach`.

---

### 2. `reducer_top_discount_by_source.py`

```python
1: #!/usr/bin/env python3
2: import sys
3: sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
4: sys.stdout.reconfigure(encoding='utf-8')
5:  
6: def emit(nguon, b):
7:     ty_le, gg, gb, giam, ten = b
8:     print(f"{nguon}\t{ty_le:.2f}\t{gg:.2f}\t{gb:.2f}\t{giam:.2f}\t{ten}")
9:  
10: cur, best = None, None
11: for line in sys.stdin:
12:     f = line.rstrip('\n').split('\t', 5)
13:     if len(f) != 6:
14:         continue
15:     nguon = f[0]
16:     try:
17:         rec = (float(f[1]), float(f[2]), float(f[3]), float(f[4]), f[5])
18:     except ValueError:
19:         continue
20:     if nguon != cur:
21:         if cur is not None:
22:             emit(cur, best)
23:         cur, best = nguon, rec
24:     elif (rec[0], rec[3]) > (best[0], best[3]):
25:         best = rec
26: if cur is not None:
27:     emit(cur, best)
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1-4**: Khai báo môi trường thực thi và cấu hình UTF-8 cho các luồng I/O.
- **Dòng 6-8 (`def emit(nguon, b):`)**: Định nghĩa hàm trợ giúp `emit` để xuất kết quả của cuốn sách giảm giá nhiều nhất theo định dạng tab: `nguon<TAB>ty_le<TAB>gia_goc<TAB>gia_ban<TAB>so_tien_giam<TAB>ten_sach`.
- **Dòng 10 (`cur, best = None, None`)**: Biến `cur` lưu tên nguồn đang xét hiện tại; `best` lưu tuple chứa thông tin cuốn sách giảm giá nhất của nguồn đó.
- **Dòng 11 (`for line in sys.stdin:`)**: Duyệt dữ liệu đầu vào từ Shuffle & Sort.
- **Dòng 12 (`f = line.rstrip('\n').split('\t', 5)`)**: Tách tối đa 6 phần từ dòng nhập.
- **Dòng 13-14 (`if len(f) != 6: continue`)**: Bỏ qua dòng không đúng 6 cột.
- **Dòng 15 (`nguon = f[0]`)**: Trích xuất tên nguồn.
- **Dòng 16-19 (`try...except ValueError: continue`)**: Ép kiểu `ty_le_giam`, `gia_goc`, `gia_ban`, `so_tien_giam` thành số thực `float` và gói thành tuple `rec`.
- **Dòng 20-23 (`if nguon != cur:`)**: Khi chuyển sang một nguồn mới, gọi `emit(cur, best)` để in ra sản phẩm giảm giá mạnh nhất của nguồn cũ trước đó, sau đó cập nhật `cur` và `best` bằng nguồn mới.
- **Dòng 24-25 (`elif (rec[0], rec[3]) > (best[0], best[3]): best = rec`)**: Nếu dòng mới thuộc cùng một nguồn, so sánh theo tuple `(ty_le_giam, so_tien_giam)`: ưu tiên tỷ lệ giảm giá cao hơn, nếu tỷ lệ bằng nhau thì ưu tiên số tiền giảm giá nhiều hơn. Nếu lớn hơn thì cập nhật `best = rec`.
- **Dòng 26-27 (`if cur is not None: emit(cur, best)`)**: Xuất kết quả cho nguồn cuối cùng khi duyệt xong toàn bộ dữ liệu.