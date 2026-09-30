import pandas as pd

# Đọc dữ liệu đã làm sạch của hai website
pn = pd.read_csv("phuongnam_clean.csv")
alpha = pd.read_csv("alpha_clean.csv")

# Bổ sung các cột Alpha Books không có
alpha["thuong_hieu"] = pd.NA
alpha["tinh_trang"] = pd.NA

# Chuẩn hóa hai nguồn về cùng cấu trúc cột
columns = [
    "ten_sach",
    "thuong_hieu",
    "tinh_trang",
    "gia_ban",
    "gia_goc",
    "link",
    "nguon"
]

pn = pn[columns]
alpha = alpha[columns]

# Gộp dữ liệu từ hai nguồn
df = pd.concat([pn, alpha], ignore_index=True)

# Lưu dữ liệu tổng hợp vào file CSV
df.to_csv("books_merged.csv", index=False, encoding="utf-8-sig")

# Kiểm tra số lượng bản ghi sau khi gộp
print("Phương Nam:", len(pn))
print("Alpha Books:", len(alpha))
print("Tổng dữ liệu:", len(df))