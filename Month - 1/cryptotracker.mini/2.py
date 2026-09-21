import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from pathlib import Path
import requests
CSV = Path("crypto_history.csv")
URL = "https://www.coingecko.com/"
def scrape_crypto():
    data = []
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        driver = webdriver.Chrome(options=options)
        try:
            driver.get(URL)
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "table tbody tr")
                )
            )
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")[:10]
            for i, row in enumerate(rows, 1):
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 6:
                    continue
                raw_price = cells[3].text.replace("$", "").replace(",", "").strip()
                raw_change = cells[5].text.replace("%", "").replace("+", "").strip()
                try:
                    price = float(raw_price)
                except ValueError:
                    price = 0.0
                try:
                    change_24h = float(raw_change)
                except ValueError:
                    change_24h = 0.0
                data.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "rank": i,
                    "name": cells[2].text.split("\n")[0],
                    "symbol": cells[2].text.split("\n")[-1],
                    "price": price,
                    "change_24h": change_24h
                })
        finally:
            driver.quit()
    except Exception as e:
        print(f"Selenium scrape notice: {e}. Falling back to live API scraper...")
    if len(data) < 5:
        try:
            api_url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 10,
                "page": 1,
                "sparkline": "false"
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            res = requests.get(api_url, params=params, headers=headers, timeout=10)
            if res.status_code == 200 and isinstance(res.json(), list):
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data = []
                for i, c in enumerate(res.json(), 1):
                    data.append({
                        "timestamp": now_str,
                        "rank": i,
                        "name": c.get("name", "Unknown"),
                        "symbol": str(c.get("symbol", "")).upper(),
                        "price": float(c.get("current_price") or 0.0),
                        "change_24h": float(c.get("price_change_percentage_24h") or 0.0)
                    })
        except Exception as api_err:
            print(f"API fallback error: {api_err}")
    df = pd.DataFrame(data)
    if not df.empty:
        need_header = not (CSV.exists() and CSV.stat().st_size > 0)
        try:
            df.to_csv(
                CSV,
                mode="a",
                header=need_header,
                index=False
            )
            print(f"Successfully scraped, cleaned, and saved {len(df)} records to {CSV}.")
        except PermissionError:
            print(f"PermissionError: Could not write to {CSV}. Please close any application using this file and try again.")
    else:
        print("No data collected.")
    return df
if __name__ == "__main__":
    scrape_crypto()