import pandas as pd

# Đọc dữ liệu thô từ Phương Nam
df = pd.read_csv("phuongnam_raw.csv")

# Loại bỏ khoảng trắng thừa trong các cột văn bản
for col in ["ten_sach", "thuong_hieu", "tinh_trang", "link", "nguon"]:
    df[col] = df[col].str.strip()

# Làm sạch và chuyển giá bán sang kiểu số
df["gia_ban"] = (
    df["gia_ban"]
    .str.replace(",", "", regex=False)
    .str.replace("₫", "", regex=False)
    .str.strip()
)

df["gia_ban"] = pd.to_numeric(df["gia_ban"], errors="coerce")

# Làm sạch và chuyển giá gốc sang kiểu số
df["gia_goc"] = (
    df["gia_goc"]
    .str.replace(",", "", regex=False)
    .str.replace("₫", "", regex=False)
    .str.strip()
)

df["gia_goc"] = pd.to_numeric(df["gia_goc"], errors="coerce")

# Nếu thiếu giá gốc thì sử dụng giá bán
df["gia_goc"] = df["gia_goc"].fillna(df["gia_ban"])
df["gia_goc"] = df["gia_goc"].astype("int64")

# Loại bỏ các sản phẩm trùng dựa trên link
df = df.drop_duplicates(subset=["link"])

# Lưu dữ liệu sau khi làm sạch
df.to_csv("phuongnam_clean.csv", index=False, encoding="utf-8-sig")

# Kiểm tra kết quả sau khi làm sạch
print("Số bản ghi sau làm sạch:", len(df))

print("\nKiểu dữ liệu:")
print(df.dtypes)

print("\nSố giá trị thiếu:")
print(df.isnull().sum())