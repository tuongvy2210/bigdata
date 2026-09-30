import requests
from bs4 import BeautifulSoup
import re

url = "https://bookbuy.vn/sach/viet/p1"

response = requests.get(url, timeout=20)
soup = BeautifulSoup(response.text, "html.parser")

links = []

for a in soup.find_all("a", href=True):
    href = a["href"]

    # Link sản phẩm BookBuy có dạng ...-p135654.html
    if re.search(r"-p\d+\.html$", href):
        if href.startswith("/"):
            href = "https://bookbuy.vn" + href

        if href not in links:
            links.append(href)

print("Số sản phẩm tìm thấy:", len(links))

for link in links[:10]:
    print(link)
