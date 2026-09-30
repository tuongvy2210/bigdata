import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

base_url = "https://nhasachphuongnam.com"
all_links = []

# Lấy link sách từ 57 trang
for page in range(1, 58):
    url = f"{base_url}/collections/van-hoc?page={page}"

    try:
        response = requests.get(url, timeout=20)
        soup = BeautifulSoup(response.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]

            if "/products/" in href:
                full_url = base_url + href

                if full_url not in all_links:
                    all_links.append(full_url)

        print(f"Trang {page}/57 - Tổng link: {len(all_links)}")
        time.sleep(1)

    except Exception as e:
        print(f"Lỗi trang {page}:", e)

print("Tổng số sản phẩm không trùng:", len(all_links))

data = []

# Cào chi tiết từng cuốn sách
for i, url in enumerate(all_links, start=1):
    try:
        response = requests.get(url, timeout=20)
        soup = BeautifulSoup(response.text, "html.parser")

        name = soup.select_one("h1.title-product")
        brand = soup.select_one(".first_status .status_name")
        status = soup.select_one(".availabel")
        price = soup.select_one(".special-price")
        old_price = soup.select_one(".old-price")

        data.append({
            "ten_sach": name.get_text(strip=True) if name else "",
            "thuong_hieu": brand.get_text(strip=True) if brand else "",
            "tinh_trang": status.get_text(strip=True) if status else "",
            "gia_ban": price.get_text(strip=True) if price else "",
            "gia_goc": old_price.get_text(strip=True) if old_price else "",
            "link": url,
            "nguon": "Phuong Nam"
        })

        print(f"Đã cào {i}/{len(all_links)}")

        # Lưu tạm mỗi 100 sản phẩm
        if i % 100 == 0:
            pd.DataFrame(data).to_csv(
                "phuongnam_raw.csv",
                index=False,
                encoding="utf-8-sig"
            )
            print("Đã lưu tạm.")

        time.sleep(1)

    except Exception as e:
        print("Lỗi sản phẩm:", url, e)

# Lưu kết quả cuối
df = pd.DataFrame(data)

df.to_csv(
    "phuongnam_raw.csv",
    index=False,
    encoding="utf-8-sig"
)

print("HOÀN THÀNH")
print("Tổng số sản phẩm đã lưu:", len(df))
