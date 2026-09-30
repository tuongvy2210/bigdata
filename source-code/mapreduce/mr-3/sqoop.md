chmod +x mapper_tinhtrang.py reducer_tinhtrang.py
sed -i 's/\r$//' mapper_tinhtrang.py reducer_tinhtrang.py

cd ~
hdfs dfs -rm -r -skipTrash /user/hadoopthanh/output_tinhtrang 2>/dev/null
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -D mapreduce.job.reduces=1 \
  -files mapper_tinhtrang.py,reducer_tinhtrang.py \
  -input /user/hadoopthanh/books_hdfs \
  -output /user/hadoopthanh/output_tinhtrang \
  -mapper mapper_tinhtrang.py \
  -reducer reducer_tinhtrang.py

hdfs dfs -cat /user/hadoopthanh/output_tinhtrang/part-00000

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "
DROP TABLE IF EXISTS stat_books_by_status;
CREATE TABLE stat_books_by_status (
  tinh_trang VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin PRIMARY KEY,
  so_luong INT NOT NULL
);"

sqoop export \
  --connect "jdbc:mysql://techreview.ddns.net:3306/bigdata?useUnicode=true&characterEncoding=UTF-8" \
  --username bigdata \
  --password 'aP+xZ2FM}_' \
  --table stat_books_by_status \
  --export-dir /user/hadoopthanh/output_tinhtrang \
  --input-fields-terminated-by '\t' \
  --columns "tinh_trang,so_luong" \
  --m 1

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "SELECT * FROM stat_books_by_status;"

## Giải thích Chi tiết Từng Dòng Code MapReduce

### 1. `mapper_tinhtrang.py`

```python
1: #!/usr/bin/env python3
2: 
3: import sys
4: 
5: sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
6: sys.stdout.reconfigure(encoding='utf-8')
7: 
8: for line in sys.stdin:
9:     fields = line.rstrip('\n').split('\t')
10:     if len(fields) < 6:
11:         continue
12:     tinh_trang = fields[5].strip()
13:     if not tinh_trang or tinh_trang.lower() in ('none', 'null', ''):
14:         tinh_trang = 'Không rõ'
15:     print(f"{tinh_trang[:100]}\t1")
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1 (`#!/usr/bin/env python3`)**: Shebang khai báo trình thông dịch Python 3.
- **Dòng 3 (`import sys`)**: Import thư viện hệ thống `sys` để làm việc với các luồng nhập xuất chuẩn.
- **Dòng 5 (`sys.stdin.reconfigure(...)`)**: Cấu hình luồng đầu vào `sys.stdin` theo mã hóa UTF-8 và bỏ qua ký tự giải mã lỗi.
- **Dòng 6 (`sys.stdout.reconfigure(...)`)**: Cấu hình luồng đầu ra `sys.stdout` theo mã hóa UTF-8.
- **Dòng 8 (`for line in sys.stdin:`)**: Vòng lặp duyệt qua từng dòng bản ghi đầu vào từ HDFS.
- **Dòng 9 (`fields = line.rstrip('\n').split('\t')`)**: Cắt bỏ ký tự xuống dòng `\n` và tách chuỗi thành danh sách các trường (`fields`) theo dấu tab `\t`.
- **Dòng 10-11 (`if len(fields) < 6: continue`)**: Kiểm tra nếu dòng dữ liệu không đủ 6 cột chuẩn thì bỏ qua không xử lý.
- **Dòng 12 (`tinh_trang = fields[5].strip()`)**: Trích xuất cột thứ 6 (`fields[5]`, chứa tình trạng sách như Mới, Cũ, Đã qua sử dụng, v.v.) và xóa khoảng trắng ở 2 đầu.
- **Dòng 13-14 (`if not tinh_trang...`)**: Nếu thông tin tình trạng bị thiếu hoặc mang giá trị `none`/`null`/`''`, gán tên mặc định là `'Không rõ'`.
- **Dòng 15 (`print(f"{tinh_trang[:100]}\t1")`)**: Giới hạn độ dài chuỗi tình trạng tối đa 100 ký tự (để khớp với độ dài trường SQL) và xuất ra cặp Key-Value `tinh_trang<TAB>1`.

---

### 2. `reducer_tinhtrang.py`

```python
1: #!/usr/bin/env python3
2: 
3: import sys
4: 
5: sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
6: sys.stdout.reconfigure(encoding='utf-8')
7: 
8: current_key = None
9: current_count = 0
10: 
11: for line in sys.stdin:
12:     parts = line.rstrip('\n').split('\t', 1)
13:     if len(parts) != 2:
14:         continue
15:     key = parts[0].strip()
16:     try:
17:         count = int(parts[1].strip())
18:     except ValueError:
19:         continue
20: 
21:     if current_key == key:
22:         current_count += count
23:     else:
24:         if current_key is not None:
25:             print(f"{current_key}\t{current_count}")
26:         current_key = key
27:         current_count = count
28: 
29: if current_key is not None:
30:     print(f"{current_key}\t{current_count}")
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1-6**: Khai báo Shebang chỉ định môi trường thực thi và cấu hình UTF-8 cho luồng `sys.stdin`/`sys.stdout`.
- **Dòng 8 (`current_key = None`)**: Khởi tạo biến lưu giá trị tình trạng sách đang được xét tích lũy hiện tại.
- **Dòng 9 (`current_count = 0`)**: Khởi tạo biến đếm tổng số lượng sách thuộc tình trạng hiện tại.
- **Dòng 11 (`for line in sys.stdin:`)**: Đọc từng dòng từ dữ liệu đã được Hadoop nhóm và sắp xếp theo Key (`tinh_trang`).
- **Dòng 12 (`parts = line.rstrip('\n').split('\t', 1)`)**: Cắt ký tự xuống dòng và tách thành 2 phần (Key `tinh_trang` và Value `count`).
- **Dòng 13-14 (`if len(parts) != 2: continue`)**: Bỏ qua dòng nếu không đúng cấu trúc 2 thành phần Key-Value.
- **Dòng 15 (`key = parts[0].strip()`)**: Trích xuất tên tình trạng sách (`parts[0]`).
- **Dòng 16-19 (`try...except ValueError: continue`)**: Ép kiểu số đếm thành số nguyên `int`, nếu lỗi thì bỏ qua.
- **Dòng 21-22 (`if current_key == key: current_count += count`)**: Nếu dòng hiện tại vẫn có cùng tình trạng, cộng dồn giá trị đếm vào `current_count`.
- **Dòng 23-25 (`else: if current_key is not None: ...`)**: Khi gặp một tình trạng sách mới, xuất kết quả tổng số sách `current_key<TAB>current_count` của tình trạng trước đó ra `stdout`.
- **Dòng 26 (`current_key = key`)**: Cập nhật biến theo dõi sang giá trị tình trạng mới.
- **Dòng 27 (`current_count = count`)**: Gán biến đếm bằng số lượng ban đầu của tình trạng mới.
- **Dòng 29-30 (`if current_key is not None: print(...)`)**: Xử lý tình trạng cuối cùng sau khi kết thúc vòng lặp đọc dữ liệu.