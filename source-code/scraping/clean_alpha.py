import pandas as pd

# Đọc dữ liệu thô từ Alpha Books
df = pd.read_csv("alpha_raw.csv")

# Loại bỏ khoảng trắng thừa trong dữ liệu
for col in ["ten_sach", "gia_ban", "gia_goc", "link", "nguon"]:
    df[col] = df[col].astype("string").str.strip()

# Làm sạch và chuyển giá bán sang kiểu số
df["gia_ban"] = (
    df["gia_ban"]
    .str.replace(".", "", regex=False)
    .str.replace("đ", "", regex=False)
    .str.strip()
)
df["gia_ban"] = pd.to_numeric(df["gia_ban"], errors="coerce")

# Làm sạch và chuyển giá gốc sang kiểu số
df["gia_goc"] = (
    df["gia_goc"]
    .str.replace(".", "", regex=False)
    .str.replace("đ", "", regex=False)
    .str.strip()
)
df["gia_goc"] = pd.to_numeric(df["gia_goc"], errors="coerce")

# Nếu thiếu giá gốc thì sử dụng giá bán
df["gia_goc"] = df["gia_goc"].fillna(df["gia_ban"])

# Loại bỏ các sản phẩm trùng dựa trên link
df = df.drop_duplicates(subset=["link"])

# Chuyển giá bán và giá gốc sang kiểu số nguyên
df["gia_ban"] = df["gia_ban"].astype("int64")
df["gia_goc"] = df["gia_goc"].astype("int64")

# Lưu dữ liệu sau khi làm sạch
df.to_csv("alpha_clean.csv", index=False, encoding="utf-8-sig")

# Kiểm tra kết quả sau khi làm sạch
print("Số bản ghi:", len(df))

print("\nKiểu dữ liệu:")
print(df.dtypes)

print("\nGiá trị thiếu:")
print(df.isnull().sum())