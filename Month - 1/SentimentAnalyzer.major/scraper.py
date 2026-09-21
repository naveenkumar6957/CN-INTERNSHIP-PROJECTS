"""
scraper.py
Collects product reviews.

IMPORTANT NOTE ON LIVE SCRAPING:
Amazon and Flipkart render reviews using JavaScript and actively block
automated requests (CAPTCHAs, IP blocking, changing HTML structure). A
lightweight requests + BeautifulSoup scraper cannot reliably pull reviews
from them, and doing so would also go against their Terms of Service.

This module provides two honest, working paths instead:

1. generic_url_scrape(url) - attempts to pull review-like text blocks from
   any product page you give it that renders plain HTML (many smaller
   e-commerce / review sites do this). It is a best-effort generic parser.

2. generate_demo_reviews(product_name) - produces realistic sample review
   data so the whole pipeline (storage, sentiment analysis, dashboard,
   charts) is fully demonstrable and testable without depending on a
   scraping target that may block you.

For a production system scraping real Amazon/Flipkart data, use their
official Product Advertising API / Affiliate APIs instead, which are
legal, stable, and do not require any scraping at all.
"""

import random
import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}


def generic_url_scrape(url, max_reviews=50):
    """
    Best-effort scrape of review-like text from a given URL.
    Looks for common review container patterns (class names containing
    'review') and returns a list of dicts: {review_text, rating, review_date}

    Returns an empty list if nothing usable is found or the request fails -
    callers should fall back to generate_demo_reviews in that case.
    """
    reviews = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return reviews

    soup = BeautifulSoup(resp.text, "html.parser")

    candidates = soup.find_all(
        lambda tag: tag.name in ("div", "p", "span", "li")
        and tag.get("class")
        and any("review" in c.lower() for c in tag.get("class"))
    )

    seen_text = set()
    for tag in candidates:
        text = tag.get_text(strip=True, separator=" ")
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 15 or len(text) > 1000:
            continue
        if text in seen_text:
            continue
        seen_text.add(text)

        reviews.append({
            "review_text": text,
            "rating": None,
            "review_date": datetime.utcnow().strftime("%Y-%m-%d"),
        })

        if len(reviews) >= max_reviews:
            break

    return reviews


# ---------------------------------------------------------------------------
# Demo data generation - used when live scraping is unavailable or blocked,
# so the dashboard remains fully functional for testing and demonstration.
# ---------------------------------------------------------------------------

_POSITIVE_TEMPLATES = [
    "This {product} exceeded my expectations, great build quality and fast delivery.",
    "Absolutely love this {product}! Works perfectly and the price is fair.",
    "Excellent {product}, would definitely recommend to friends and family.",
    "Very happy with this purchase. The {product} is durable and easy to use.",
    "Great value for money, the {product} performs better than I expected.",
    "Superb quality, the {product} looks and feels premium.",
    "Fast shipping and the {product} works exactly as described. Very satisfied.",
    "Five stars, this {product} is exactly what I needed.",
]

_NEGATIVE_TEMPLATES = [
    "Very disappointed with this {product}, it stopped working within a week.",
    "Poor quality {product}, not worth the money at all.",
    "The {product} arrived damaged and customer service was unhelpful.",
    "Would not recommend this {product}, build quality feels cheap.",
    "Terrible experience, the {product} does not match the description.",
    "Waste of money, the {product} broke on the second use.",
    "Not satisfied, the {product} is slower and noisier than advertised.",
    "Regret buying this {product}, quality control seems very poor.",
]

_NEUTRAL_TEMPLATES = [
    "The {product} is okay, does the job but nothing special.",
    "Average {product}, packaging could be better.",
    "It's a decent {product} for the price, though delivery took a while.",
    "The {product} works fine, though I expected slightly better battery life.",
    "Received the {product} on time, still testing it out.",
    "The {product} is fine so far, will update this review after a month.",
]


def generate_demo_reviews(product_name, count=60):
    """
    Generates a realistic-looking, randomized mix of positive, negative,
    and neutral reviews spread over the last 90 days, so the sentiment
    dashboard and trend charts have meaningful data to display.
    """
    reviews = []
    today = datetime.utcnow()

    for _ in range(count):
        bucket = random.choices(
            ["positive", "negative", "neutral"],
            weights=[0.55, 0.20, 0.25],
            k=1
        )[0]

        if bucket == "positive":
            template = random.choice(_POSITIVE_TEMPLATES)
            rating = random.choice([4, 5])
        elif bucket == "negative":
            template = random.choice(_NEGATIVE_TEMPLATES)
            rating = random.choice([1, 2])
        else:
            template = random.choice(_NEUTRAL_TEMPLATES)
            rating = 3

        text = template.format(product=product_name)
        days_ago = random.randint(0, 90)
        review_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        reviews.append({
            "review_text": text,
            "rating": rating,
            "review_date": review_date,
        })

    reviews.sort(key=lambda r: r["review_date"])
    return reviews


def collect_reviews(product_name, source="demo", url=None):
    """
    Main entry point used by the API layer.

    source == "url"  -> attempts generic_url_scrape(url), falls back to demo
    source == "demo" -> always returns generated demo data
    """
    if source == "url" and url:
        scraped = generic_url_scrape(url)
        if scraped:
            return scraped, "scraped"
        return generate_demo_reviews(product_name), "demo_fallback"

    return generate_demo_reviews(product_name), "demo"
