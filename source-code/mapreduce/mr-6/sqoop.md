chmod +x mapper_max_price.py reducer_max_price.py
sed -i 's/\r$//' mapper_max_price.py reducer_max_price.py

cd ~
hdfs dfs -rm -r -skipTrash /user/hadoopthanh/output_max_price 2>/dev/null
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -D mapreduce.job.reduces=1 \
  -files mapper_max_price.py,reducer_max_price.py \
  -input /user/hadoopthanh/books_hdfs \
  -output /user/hadoopthanh/output_max_price \
  -mapper mapper_max_price.py \
  -reducer reducer_max_price.py

hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -D mapreduce.job.reduces=1 \
  -files mapper_top_discount_by_source.py,reducer_top_discount_by_source.py \
  -input /user/hadoopthanh/books_hdfs \
  -output /user/hadoopthanh/output_mapreduce_discount \
  -mapper mapper_top_discount_by_source.py \
  -reducer reducer_top_discount_by_source.py
  
hdfs dfs -cat /user/hadoopthanh/output_max_price/part-00000

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "
DROP TABLE IF EXISTS max_price_by_source;
CREATE TABLE max_price_by_source (
  nguon VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin PRIMARY KEY,
  gia_cao_nhat DOUBLE NOT NULL,
  ten_san_pham TEXT
);"

sqoop export \
  --connect "jdbc:mysql://techreview.ddns.net:3306/bigdata?useUnicode=true&characterEncoding=UTF-8" \
  --username bigdata \
  --password 'aP+xZ2FM}_' \
  --table max_price_by_source \
  --export-dir /user/hadoopthanh/output_max_price \
  --input-fields-terminated-by '\t' \
  --columns "nguon,gia_cao_nhat,ten_san_pham" \
  --m 1

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "SELECT * FROM max_price_by_source;"

## Giải thích Chi tiết Từng Dòng Code MapReduce

### 1. `mapper_max_price.py`

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
15:     ten_sach = f[4].strip().replace('\t', ' ').replace('\n', ' ')
16: 
17:     if not nguon or nguon.lower() in ('', 'null', 'none'):
18:         nguon = 'Không rõ'
19: 
20:     try:
21:         gb = float(gia_ban_raw)
22:         if gb > 0:
23:             print(f"{nguon}\t{gb:.2f}\t{ten_sach}")
24:     except ValueError:
25:         continue
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1-6**: Khai báo Shebang chỉ định môi trường thực thi Python 3 và cấu hình luồng UTF-8 cho `sys.stdin`/`sys.stdout`.
- **Dòng 8 (`for line in sys.stdin:`)**: Lặp qua từng dòng dữ liệu bản ghi đầu vào từ HDFS.
- **Dòng 9 (`f = line.rstrip('\n').split('\t')`)**: Cắt bỏ ký tự xuống dòng `\n` và tách bản ghi thành danh sách các trường (`f`) qua ký tự tab.
- **Dòng 10-11 (`if len(f) < 6: continue`)**: Bỏ qua các dòng không đủ 6 cột dữ liệu chuẩn.
- **Dòng 13 (`nguon = f[0].strip()`)**: Trích xuất cột nguồn dữ liệu (`f[0]`).
- **Dòng 14 (`gia_ban_raw = f[2].strip()`)**: Trích xuất cột giá bán (`f[2]`).
- **Dòng 15 (`ten_sach = f[4].strip().replace('\t', ' ').replace('\n', ' ')`)**: Trích xuất tên sách (`f[4]`), xóa tab và ký tự xuống dòng thừa trong tên sách.
- **Dòng 17-18 (`if not nguon...`)**: Gán nhãn `'Không rõ'` nếu nguồn dữ liệu bị rỗng hoặc lỗi `null/none`.
- **Dòng 20-25 (`try...except ValueError: continue`)**: Chuyển đổi giá bán `gia_ban_raw` thành số thực `float` (`gb`). Nếu `gb > 0`, in ra cặp Key-Value định dạng `nguon<TAB>gb<TAB>ten_sach` để phát sang Reducer.

---

### 2. `reducer_max_price.py`

```python
1: #!/usr/bin/env python3
2: 
3: import sys
4: 
5: sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
6: sys.stdout.reconfigure(encoding='utf-8')
7: 
8: cur_nguon = None
9: max_price = -1.0
10: max_name = ""
11: 
12: for line in sys.stdin:
13:     parts = line.rstrip('\n').split('\t', 2)
14:     if len(parts) != 3:
15:         continue
16: 
17:     nguon, price_str, ten_sach = parts
18:     try:
19:         price = float(price_str)
20:     except ValueError:
21:         continue
22: 
23:     if nguon == cur_nguon:
24:         if price > max_price:
25:             max_price = price
26:             max_name = ten_sach
27:     else:
28:         if cur_nguon is not None:
29:             print(f"{cur_nguon}\t{max_price:.2f}\t{max_name}")
30:         cur_nguon = nguon
31:         max_price = price
32:         max_name = ten_sach
33: 
34: if cur_nguon is not None:
35:     print(f"{cur_nguon}\t{max_price:.2f}\t{max_name}")
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1-6**: Khai báo môi trường Python 3 và cấu hình UTF-8.
- **Dòng 8 (`cur_nguon = None`)**: Khởi tạo biến theo dõi nguồn hiện tại.
- **Dòng 9 (`max_price = -1.0`)**: Biến lưu giá trị bán cao nhất của nguồn hiện tại, khởi tạo giá trị âm ban đầu.
- **Dòng 10 (`max_name = ""`)**: Biến lưu tên cuốn sách có giá đắt nhất tương ứng.
- **Dòng 12 (`for line in sys.stdin:`)**: Lặp qua từng dòng dữ liệu đã được Hadoop nhóm theo Key (`nguon`).
- **Dòng 13 (`parts = line.rstrip('\n').split('\t', 2)`)**: Tách dòng thành tối đa 3 phần (`nguon`, `price_str`, `ten_sach`).
- **Dòng 14-15 (`if len(parts) != 3: continue`)**: Bỏ qua bản ghi nếu thiếu trường.
- **Dòng 17-21 (`nguon, price_str, ten_sach = parts...`)**: Ép kiểu `price_str` thành số thực `float`.
- **Dòng 23-26 (`if nguon == cur_nguon:`)**: Nếu sản phẩm mới thuộc cùng một nguồn đang xét: kiểm tra nếu `price > max_price` thì cập nhật `max_price = price` và `max_name = ten_sach`.
- **Dòng 27-32 (`else:`)**: Khi gặp một nguồn mới: xuất kết quả cuốn sách đắt nhất `cur_nguon<TAB>max_price<TAB>max_name` của nguồn vừa duyệt xong ra `stdout`. Cập nhật `cur_nguon`, `max_price`, và `max_name` bằng thông tin cuốn sách đầu tiên của nguồn mới.
- **Dòng 34-35 (`if cur_nguon is not None: print(...)`)**: Xuất kết quả sản phẩm đắt nhất cho nguồn cuối cùng.