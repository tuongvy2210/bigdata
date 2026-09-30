import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

base_url = "https://nhasachphuongnam.com"
all_links = []

# Duyệt 57 trang để thu thập link sản phẩm
for page in range(1, 58):
    url = f"{base_url}/collections/van-hoc?page={page}"

    try:
        # Gửi request đến từng trang danh mục
        response = requests.get(url, timeout=20)

        # Phân tích nội dung HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Tìm các link sản phẩm và loại bỏ link trùng
        for a in soup.find_all("a", href=True):
            href = a["href"]

            if "/products/" in href:
                full_url = base_url + href

                if full_url not in all_links:
                    all_links.append(full_url)

        # Hiển thị tiến độ lấy link
        print(f"Trang {page}/57 - Tổng link: {len(all_links)}")
        time.sleep(1)

    except Exception as e:
        print(f"Lỗi trang {page}:", e)

print("Tổng số sản phẩm không trùng:", len(all_links))

data = []

# Duyệt từng link để thu thập thông tin chi tiết sản phẩm
for i, url in enumerate(all_links, start=1):
    try:
        # Gửi request đến trang chi tiết sản phẩm
        response = requests.get(url, timeout=20)

        # Phân tích nội dung HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Lấy thông tin sản phẩm bằng CSS Selector
        name = soup.select_one("h1.title-product")
        brand = soup.select_one(".first_status .status_name")
        status = soup.select_one(".availabel")
        price = soup.select_one(".special-price")
        old_price = soup.select_one(".old-price")

        # Lấy nội dung văn bản và đưa vào danh sách dữ liệu
        data.append({
            "ten_sach": name.get_text(strip=True) if name else "",
            "thuong_hieu": brand.get_text(strip=True) if brand else "",
            "tinh_trang": status.get_text(strip=True) if status else "",
            "gia_ban": price.get_text(strip=True) if price else "",
            "gia_goc": old_price.get_text(strip=True) if old_price else "",
            "link": url,
            "nguon": "Phuong Nam"
        })

        # Hiển thị tiến độ thu thập sản phẩm
        print(f"Đã cào {i}/{len(all_links)}")

        # Lưu tạm dữ liệu sau mỗi 100 sản phẩm
        if i % 100 == 0:
            pd.DataFrame(data).to_csv(
                "phuongnam_raw.csv",
                index=False,
                encoding="utf-8-sig"
            )
            print("Đã lưu tạm.")

        # Nghỉ 1 giây giữa các request
        time.sleep(1)

    # Nếu sản phẩm bị lỗi thì báo lỗi và tiếp tục sản phẩm khác
    except Exception as e:
        print("Lỗi sản phẩm:", url, e)

# Chuyển danh sách dữ liệu thành DataFrame
df = pd.DataFrame(data)

# Lưu toàn bộ dữ liệu thô vào file CSV
df.to_csv(
    "phuongnam_raw.csv",
    index=False,
    encoding="utf-8-sig"
)

print("HOÀN THÀNH")
print("Tổng số sản phẩm đã lưu:", len(df))