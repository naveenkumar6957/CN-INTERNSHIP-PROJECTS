"""
app.py
Flask backend for the Product Sentiment Analyzer and Review Dashboard.

Serves:
- REST API endpoints under /api/*
- The static frontend (index.html, style.css, script.js) from /static

Run locally with:
    python app.py
Then open http://localhost:5000 in a browser.
"""

from flask import Flask, request, jsonify, send_from_directory
import os

import database
from scraper import collect_reviews
from sentiment_analysis import analyze_reviews_batch, get_word_frequency

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")

database.init_db()


# ---------------------------------------------------------------------------
# Frontend routes
# ---------------------------------------------------------------------------

@app.route("/")
def serve_index():
    return send_from_directory(STATIC_DIR, "index.html")


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.route("/api/search", methods=["POST"])
def search_product():
    """
    Body JSON:
        {
            "product_name": "Wireless Earbuds X200",
            "source": "demo"   // "demo" or "url"
            "url": "https://..."   // required if source == "url"
        }

    Collects reviews (scraped or demo), runs sentiment analysis on each,
    stores everything, and returns the product_id plus a summary.
    """
    data = request.get_json(silent=True) or {}
    product_name = (data.get("product_name") or "").strip()
    source = data.get("source", "demo")
    url = data.get("url")

    if not product_name:
        return jsonify({"error": "product_name is required"}), 400

    existing = database.find_product(product_name, source)
    if existing:
        product_id = existing["id"]
        reviews = database.get_reviews_for_product(product_id)
        if reviews:
            return jsonify({
                "product_id": product_id,
                "product_name": product_name,
                "review_count": len(reviews),
                "cached": True
            })

    raw_reviews, method = collect_reviews(product_name, source=source, url=url)

    if not raw_reviews:
        return jsonify({"error": "No reviews could be found for this product."}), 404

    analyzed_reviews = analyze_reviews_batch(raw_reviews)

    product_id = database.insert_product(product_name, source, url)
    database.insert_reviews(product_id, analyzed_reviews)

    return jsonify({
        "product_id": product_id,
        "product_name": product_name,
        "review_count": len(analyzed_reviews),
        "collection_method": method,
        "cached": False
    })


@app.route("/api/products", methods=["GET"])
def list_products():
    products = database.list_products()
    return jsonify(products)


@app.route("/api/reviews/<int:product_id>", methods=["GET"])
def get_reviews(product_id):
    product = database.get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    reviews = database.get_reviews_for_product(product_id)
    return jsonify({
        "product": product,
        "reviews": reviews
    })


@app.route("/api/sentiment-summary/<int:product_id>", methods=["GET"])
def sentiment_summary(product_id):
    product = database.get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    reviews = database.get_reviews_for_product(product_id)
    if not reviews:
        return jsonify({"error": "No reviews found for this product"}), 404

    counts = {"positive": 0, "negative": 0, "neutral": 0}
    ratings = []
    trend = {}  # date -> {"positive": n, "negative": n, "neutral": n}

    for r in reviews:
        label = r.get("sentiment_label") or "neutral"
        counts[label] = counts.get(label, 0) + 1

        if r.get("rating") is not None:
            ratings.append(r["rating"])

        date = r.get("review_date") or "unknown"
        if date not in trend:
            trend[date] = {"positive": 0, "negative": 0, "neutral": 0}
        trend[date][label] += 1

    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

    trend_sorted = [
        {"date": d, **counts_for_day}
        for d, counts_for_day in sorted(trend.items())
        if d != "unknown"
    ]

    word_freq = get_word_frequency(reviews, top_n=15)

    return jsonify({
        "product": product,
        "total_reviews": len(reviews),
        "sentiment_counts": counts,
        "average_rating": avg_rating,
        "sentiment_trend": trend_sorted,
        "word_frequency": [{"word": w, "count": c} for w, c in word_freq]
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
