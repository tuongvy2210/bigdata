cd ~
hdfs dfs -rm -r -skipTrash /user/hadoopthanh/output_nguon 2>/dev/null
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -D mapreduce.job.reduces=1 \
  -files mapper_nguon.py,reducer_nguon.py \
  -input /user/hadoopthanh/books_hdfs \
  -output /user/hadoopthanh/output_nguon \
  -mapper mapper_nguon.py \
  -reducer reducer_nguon.py

hdfs dfs -cat /user/hadoopthanh/output_nguon/part-00000

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "
DROP TABLE IF EXISTS stat_books_by_source;
CREATE TABLE stat_books_by_source (
  nguon VARCHAR(100) NOT NULL PRIMARY KEY,
  so_luong INT NOT NULL
);"



sqoop export \
  --connect jdbc:mysql://techreview.ddns.net:3306/bigdata \
  --username bigdata \
  --password 'aP+xZ2FM}_' \
  --table stat_books_by_source \
  --export-dir /user/hadoopthanh/output_nguon \
  --input-fields-terminated-by '\t' \
  --columns "nguon,so_luong" \
  --m 1

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "SELECT * FROM stat_books_by_source LIMIT 10;"

## Giải thích Chi tiết Từng Dòng Code MapReduce

### 1. `mapper_nguon.py`

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
10:     if len(fields) < 1:
11:         continue
12:     nguon = fields[0].strip()
13:     if nguon and nguon.lower() not in ('none', 'null', ''):
14:         print(f"{nguon}\t1")
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1 (`#!/usr/bin/env python3`)**: Shebang chỉ định môi trường thực thi script là Python 3.
- **Dòng 3 (`import sys`)**: Import thư viện `sys` làm việc với luồng `sys.stdin` và `sys.stdout`.
- **Dòng 5 (`sys.stdin.reconfigure(...)`)**: Thiết lập luồng đọc UTF-8 và bỏ qua ký tự giải mã lỗi.
- **Dòng 6 (`sys.stdout.reconfigure(...)`)**: Thiết lập luồng xuất dữ liệu chuẩn UTF-8.
- **Dòng 8 (`for line in sys.stdin:`)**: Vòng lặp đọc từng dòng dữ liệu từ HDFS vào Mapper.
- **Dòng 9 (`fields = line.rstrip('\n').split('\t')`)**: Loại bỏ ký tự xuống dòng `\n` và tách bản ghi thành các trường qua dấu tab.
- **Dòng 10-11 (`if len(fields) < 1: continue`)**: Bỏ qua dòng dữ liệu nếu không trích xuất được bất kỳ trường nào.
- **Dòng 12 (`nguon = fields[0].strip()`)**: Lấy giá trị tên nguồn ở cột đầu tiên (`fields[0]`) và xóa khoảng trắng thừa.
- **Dòng 13 (`if nguon and nguon.lower() not in ('none', 'null', ''):`)**: Lọc bỏ các tên nguồn rỗng hoặc mang giá trị không hợp lệ (`null`, `none`, `''`).
- **Dòng 14 (`print(f"{nguon}\t1")`)**: Xuất cặp Key-Value `nguon<TAB>1` ra luồng `stdout` đại diện cho 1 cuốn sách thu thuộc nguồn này.

---

### 2. `reducer_nguon.py`

```python
1: #!/usr/bin/env python3
2: 
3: import sys
4: 
5: sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
6: sys.stdout.reconfigure(encoding='utf-8')
7: 
8: current_nguon = None
9: current_count = 0
10: 
11: for line in sys.stdin:
12:     parts = line.rstrip('\n').split('\t', 1)
13:     if len(parts) != 2:
14:         continue
15:     nguon = parts[0].strip()
16:     try:
17:         count = int(parts[1].strip())
18:     except ValueError:
19:         continue
20: 
21:     if current_nguon == nguon:
22:         current_count += count
23:     else:
24:         if current_nguon is not None:
25:             print(f"{current_nguon}\t{current_count}")
26:         current_nguon = nguon
27:         current_count = count
28: 
29: if current_nguon is not None:
30:     print(f"{current_nguon}\t{current_count}")
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1-6**: Khai báo môi trường Python 3 và thiết lập mã hóa luồng UTF-8.
- **Dòng 8 (`current_nguon = None`)**: Khởi tạo biến lưu tên nguồn đang xét hiện tại.
- **Dòng 9 (`current_count = 0`)**: Khởi tạo biến đếm tổng số cuốn sách thu thuộc nguồn hiện tại.
- **Dòng 11 (`for line in sys.stdin:`)**: Đọc từng dòng dữ liệu từ kết quả Shuffle/Sort của Hadoop Streaming.
- **Dòng 12 (`parts = line.rstrip('\n').split('\t', 1)`)**: Cắt ký tự xuống dòng và tách thành 2 phần (Key `nguon` và Value `count`).
- **Dòng 13-14 (`if len(parts) != 2: continue`)**: Bỏ qua dòng nếu không đúng 2 phần Key-Value.
- **Dòng 15 (`nguon = parts[0].strip()`)**: Trích xuất tên nguồn.
- **Dòng 16-19 (`try...except ValueError: continue`)**: Ép kiểu số lượng `parts[1]` thành số nguyên `int`, nếu lỗi thì bỏ qua.
- **Dòng 21-22 (`if current_nguon == nguon: current_count += count`)**: Nếu cùng một nguồn thì cộng dồn số lượng sách vào `current_count`.
- **Dòng 23-25 (`else: if current_nguon is not None: ...`)**: Khi gặp nguồn mới, xuất ra kết quả tổng số sách `current_nguon<TAB>current_count` của nguồn trước đó.
- **Dòng 26 (`current_nguon = nguon`)**: Cập nhật biến theo dõi sang nguồn mới.
- **Dòng 27 (`current_count = count`)**: Gán biến đếm số sách bằng giá trị số lượng ban đầu của nguồn mới.
- **Dòng 29-30 (`if current_nguon is not None: print(...)`)**: Sau khi duyệt hết dữ liệu, xuất tổng số sách cho nguồn cuối cùng.