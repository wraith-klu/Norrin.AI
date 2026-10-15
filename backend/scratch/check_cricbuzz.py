import requests
from bs4 import BeautifulSoup

url = "https://www.cricbuzz.com/profiles/1413/virat-kohli"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
resp = requests.get(url, headers=headers, timeout=12)
html = resp.text

soup = BeautifulSoup(html, "html.parser")
tables = soup.find_all("table")
print(f"Total tables found: {len(tables)}")

for i, table in enumerate(tables):
    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    print(f"\nTable {i} headers: {headers}")
    rows = []
    for tr in table.find_all("tr")[1:]:
        row = [td.get_text(strip=True) for td in tr.find_all("td")]
        if row:
            rows.append(row)
    print(f"Table {i} rows (first 3): {rows[:3]}")
