import os
import glob
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def clean_wdm_locks():
    wdm_dir = os.path.join(os.path.expanduser("~"), ".wdm")
    if os.path.exists(wdm_dir):
        for lock_file in glob.glob(os.path.join(wdm_dir, "**", "*lock*"), recursive=True):
            try:
                os.remove(lock_file)
            except Exception:
                pass


def get_driver():
    clean_wdm_locks()
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    options.add_argument("--lang=en-US")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception:
        driver = webdriver.Chrome(options=options)

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
    )
    return driver


def scrape_imdb_top_250():
    url = "https://www.imdb.com/chart/top/"
    driver = get_driver()
    movies = []

    try:
        print("Navigating to IMDb Top 250...")
        driver.get(url)

        wait = WebDriverWait(driver, 20)
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item"))
        )

        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

        items = driver.find_elements(By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item")
        print(f"Total movie items found: {len(items)}")

        for i, item in enumerate(items, 1):
            try:
                title_el = item.find_element(
                    By.CSS_SELECTOR, "h3.ipc-title__text, h4.ipc-title__text"
                )
                title_text = title_el.text.strip()

                if ". " in title_text:
                    rank, title = title_text.split(". ", 1)
                else:
                    try:
                        rank = item.find_element(
                            By.CSS_SELECTOR,
                            "div.ipc-signpost__text, div[data-testid='title-list-item-ranking']"
                        ).text.strip().replace("#", "")
                    except Exception:
                        rank = str(i)
                    title = title_text

                meta_els = item.find_elements(
                    By.CSS_SELECTOR, "div.cli-title-metadata li, span.cli-title-metadata-item"
                )
                year = meta_els[0].text.strip() if meta_els else "N/A"

                rating_el = item.find_element(By.CSS_SELECTOR, "span.ipc-rating-star--rating")
                rating = rating_el.text.strip() if rating_el else "N/A"

                movies.append({
                    "Rank": rank,
                    "Movie Title": title,
                    "Release Year": year,
                    "IMDb Rating": rating
                })
            except Exception:
                continue

        df = pd.DataFrame(movies)
        output_file = "imdb_top_250_movies.csv"
        df.to_csv(output_file, index=False)

        print("Scraping completed successfully.")
        print(f"Movies collected: {len(df)}")
        print(f"Saved to: {output_file}")
        print("\nFirst 10 Movies:")
        print(df.head(10))

    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_imdb_top_250()