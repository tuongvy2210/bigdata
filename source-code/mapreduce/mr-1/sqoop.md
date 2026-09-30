Job 1: Giá bán trung bình theo Nhà xuất bản (thuong_hieu)


hdfs dfs -rm -r /user/hadoopthanh/output_publisher 2>/dev/null
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -D mapreduce.job.reduces=1 \
  -files mapper_publisher.py,reducer_publisher.py \
  -input /user/hadoopthanh/books_hdfs \
  -output /user/hadoopthanh/output_publisher \
  -mapper mapper_publisher.py \
  -reducer reducer_publisher.py

hdfs dfs -cat /user/hadoopthanh/output_publisher/part-00000 | head -n 10

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "
DROP TABLE IF EXISTS stat_avg_price_by_publisher;
CREATE TABLE stat_avg_price_by_publisher (
  thuong_hieu VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin PRIMARY KEY,
  gia_trung_binh DOUBLE NOT NULL
);"
 
mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "TRUNCATE TABLE stat_avg_price_by_publisher;"

hdfs dfs -cat /user/hadoopthanh/output_publisher/part-00000 | head -n 10

sqoop export \
  --connect jdbc:mysql://techreview.ddns.net:3306/bigdata \
  --username bigdata \
  --password 'aP+xZ2FM}_' \
  --table stat_avg_price_by_publisher \
  --export-dir /user/hadoopthanh/output_publisher \
  --columns "thuong_hieu,gia_trung_binh" \
  --input-fields-terminated-by '\t' \
  --m 1

mysql -h techreview.ddns.net -P 3306 -u bigdata -p'aP+xZ2FM}_' bigdata -e "SELECT * FROM stat_avg_price_by_publisher LIMIT 10;"

## Giải thích Chi tiết Từng Dòng Code MapReduce

### 1. `mapper_publisher.py`

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
10: 
11:     if len(f) < 6:
12:         continue
13: 
14:     thuong_hieu = f[1].strip()
15:     gia_ban_raw = f[2].strip()
16: 
17:     if not thuong_hieu or thuong_hieu.lower() in ('none', 'null', ''):
18:         thuong_hieu = 'Không rõ'
19: 
20:     if not gia_ban_raw or gia_ban_raw.lower() in ('none', 'null', ''):
21:         continue
22: 
23:     try:
24:         gia_ban = float(gia_ban_raw)
25: 
26:         if gia_ban > 0:
27:             print(f"{thuong_hieu}\t{gia_ban}")
28: 
29:     except ValueError:
30:         continue
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1 (`#!/usr/bin/env python3`)**: Dòng Shebang chỉ định môi trường thực thi script là Python 3 trên hệ điều hành Linux/Hadoop Cluster.
- **Dòng 3 (`import sys`)**: Import thư viện chuẩn `sys` để làm việc với các luồng nhập xuất chuẩn `sys.stdin` và `sys.stdout`.
- **Dòng 5 (`sys.stdin.reconfigure(...)`)**: Đặt cấu hình luồng đọc dữ liệu `stdin` sang mã hóa UTF-8 và bỏ qua (`errors='ignore'`) các lỗi giải mã ký tự lạ nếu có.
- **Dòng 6 (`sys.stdout.reconfigure(...)`)**: Đặt cấu hình luồng xuất dữ liệu `stdout` sang mã hóa UTF-8 để đảm bảo tiếng Việt không bị lỗi font khi xuất dữ liệu.
- **Dòng 8 (`for line in sys.stdin:`)**: Vòng lặp duyệt qua từng dòng dữ liệu bản ghi được truyền từ HDFS vào luồng đầu vào chuẩn.
- **Dòng 9 (`f = line.rstrip('\n').split('\t')`)**: Cắt bỏ ký tự xuống dòng `\n` ở cuối dòng và tách chuỗi thành danh sách các cột (`f`) dựa trên ký tự ngăn cách Tab (`\t`).
- **Dòng 11-12 (`if len(f) < 6: continue`)**: Kiểm tra cấu trúc bản ghi, nếu danh sách `f` có ít hơn 6 cột (không đủ định dạng chuẩn dữ liệu sách) thì bỏ qua bản ghi này.
- **Dòng 14 (`thuong_hieu = f[1].strip()`)**: Trích xuất cột thứ 2 (`f[1]`, chứa tên thương hiệu/nhà xuất bản) và xóa khoảng trắng thừa ở 2 đầu chuỗi.
- **Dòng 15 (`gia_ban_raw = f[2].strip()`)**: Trích xuất cột thứ 3 (`f[2]`, chứa giá bán dạng chuỗi raw) và loại bỏ khoảng trắng thừa.
- **Dòng 17-18 (`if not thuong_hieu...`)**: Kiểm tra nếu tên thương hiệu bị rỗng hoặc chứa các giá trị nạp lỗi (`'none'`, `'null'`, `''`) thì gán tên mặc định là `'Không rõ'`.
- **Dòng 20-21 (`if not gia_ban_raw...`)**: Kiểm tra nếu giá bán bị rỗng hoặc là nạp lỗi `null/none` thì bỏ qua dòng dữ liệu này.
- **Dòng 23 (`try:`)**: Mở khối lệnh kiểm soát ngoại lệ khi ép kiểu dữ liệu giá bán.
- **Dòng 24 (`gia_ban = float(gia_ban_raw)`)**: Chuyển đổi giá bán từ dạng chuỗi ký tự sang dạng số thực (`float`).
- **Dòng 26 (`if gia_ban > 0:`)**: Kiểm tra điều kiện giá bán phải lớn hơn 0 (loại bỏ các sản phẩm có giá 0 hoặc âm).
- **Dòng 27 (`print(f"{thuong_hieu}\t{gia_ban}")`)**: In ra luồng `stdout` cặp Key-Value định dạng `thuong_hieu<TAB>gia_ban` làm đầu ra cho Mapper.
- **Dòng 29-30 (`except ValueError: continue`)**: Bắt lỗi `ValueError` nếu giá bán không thể ép kiểu số thực (ví dụ chứa chữ cái) và bỏ qua bản ghi lỗi đó.

---

### 2. `reducer_publisher.py`

```python
1: #!/usr/bin/env python3
2: 
3: import sys
4: 
5: sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
6: sys.stdout.reconfigure(encoding='utf-8')
7: 
8: current_publisher = None
9: total_price = 0.0
10: count = 0
11: 
12: for line in sys.stdin:
13:     parts = line.rstrip('\n').split('\t', 1)
14: 
15:     if len(parts) != 2:
16:         continue
17: 
18:     publisher = parts[0].strip()
19:     price_str = parts[1].strip()
20: 
21:     try:
22:         price = float(price_str)
23:     except ValueError:
24:         continue
25: 
26:     if current_publisher == publisher:
27:         total_price += price
28:         count += 1
29:     else:
30:         if current_publisher is not None and count > 0:
31:             avg_price = total_price / count
32:             print(f"{current_publisher}\t{avg_price:.2f}")
33: 
34:         current_publisher = publisher
35:         total_price = price
36:         count = 1
37: 
38: if current_publisher is not None and count > 0:
39:     avg_price = total_price / count
40:     print(f"{current_publisher}\t{avg_price:.2f}")
```

**Giải thích ý nghĩa từng dòng:**
- **Dòng 1-6**: Khai báo Shebang chỉ định môi trường Python 3 và cấu hình luồng đọc/ghi `sys.stdin`/`sys.stdout` theo mã hóa UTF-8.
- **Dòng 8 (`current_publisher = None`)**: Khởi tạo biến lưu trữ tên nhà xuất bản đang được xét hiện tại, ban đầu là `None`.
- **Dòng 9 (`total_price = 0.0`)**: Khởi tạo biến tích lũy tổng giá bán cho nhà xuất bản hiện tại.
- **Dòng 10 (`count = 0`)**: Khởi tạo biến đếm tổng số cuốn sách thuộc nhà xuất bản hiện tại.
- **Dòng 12 (`for line in sys.stdin:`)**: Vòng lặp đọc từng dòng dữ liệu đã được Hadoop Shuffle & Sort sắp xếp nhóm theo Key (`publisher`).
- **Dòng 13 (`parts = line.rstrip('\n').split('\t', 1)`)**: Cắt ký tự xuống dòng và tách dòng thành tối đa 2 phần (Key và Value) qua dấu tab.
- **Dòng 15-16 (`if len(parts) != 2: continue`)**: Bỏ qua các dòng không đủ 2 thành phần Key và Value.
- **Dòng 18 (`publisher = parts[0].strip()`)**: Lấy tên nhà xuất bản từ phần thứ nhất (`parts[0]`).
- **Dòng 19 (`price_str = parts[1].strip()`)**: Lấy chuỗi giá bán từ phần thứ hai (`parts[1]`).
- **Dòng 21-24 (`try...except ValueError: continue`)**: Ép kiểu `price_str` thành số thực `float`, nếu lỗi thì bỏ qua.
- **Dòng 26 (`if current_publisher == publisher:`)**: Kiểm tra nếu dòng dữ liệu mới vẫn thuộc cùng một nhà xuất bản đang xét.
- **Dòng 27 (`total_price += price`)**: Cộng giá bán cuốn sách hiện tại vào biến tích lũy `total_price`.
- **Dòng 28 (`count += 1`)**: Tăng số lượng cuốn sách đếm được thêm 1.
- **Dòng 29 (`else:`)**: Trường hợp chuyển sang một nhà xuất bản mới (hoặc dòng đầu tiên của dữ liệu).
- **Dòng 30-32 (`if current_publisher is not None...`)**: Nếu trước đó đã tích lũy dữ liệu cho một nhà xuất bản, tính giá bán trung bình `avg_price = total_price / count` và xuất ra `stdout` theo định dạng `current_publisher<TAB>avg_price` làm tròn 2 số thập phân.
- **Dòng 34 (`current_publisher = publisher`)**: Chuyển biến theo dõi sang nhà xuất bản mới vừa xuất hiện.
- **Dòng 35 (`total_price = price`)**: Đặt lại tổng giá bán bằng giá cuốn sách đầu tiên của nhà xuất bản mới.
- **Dòng 36 (`count = 1`)**: Đặt lại biến đếm số lượng sách thành 1.
- **Dòng 38-40 (`if current_publisher is not None and count > 0:`)**: Khối xử lý dòng cuối cùng sau khi kết thúc vòng lặp `sys.stdin`, tính toán giá trung bình và xuất ra kết quả cho nhà xuất bản cuối cùng.

