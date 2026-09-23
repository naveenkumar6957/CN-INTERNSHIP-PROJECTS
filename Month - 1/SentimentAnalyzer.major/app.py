"""
app.py
Flask Web Application & REST API Server for E-Commerce Product Sentiment Dashboard.
Integrates live Amazon & Flipkart scraper, VADER sentiment analyzer, and SQLite database.
"""

from flask import Flask, request, jsonify, send_from_directory, Response
import os
import io
import csv

import database
from scraper import collect_reviews
from sentiment_analysis import analyze_reviews_batch, get_word_frequency, extract_pros_cons

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")

# Initialize Database
database.init_db()


# ---------------------------------------------------------------------------
# Static & Utility Routes
# ---------------------------------------------------------------------------

@app.route("/")
def serve_index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/favicon.ico")
def favicon():
    return Response(status=204)


@app.route("/manifest.json")
@app.route("/static/manifest.json")
def manifest():
    return jsonify({
        "short_name": "SentimentDesk",
        "name": "Product Review Sentiment Analyzer",
        "start_url": "/",
        "display": "standalone",
        "theme_color": "#0F172A",
        "background_color": "#0F172A"
    })


@app.route("/service-worker.js")
def service_worker():
    return Response("// Service worker disabled", mimetype="application/javascript", status=200)


# ---------------------------------------------------------------------------
# REST API Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "service": "Product Sentiment Analyzer"})


@app.route("/api/search", methods=["POST"])
@app.route("/api/scrape", methods=["POST"])
def search_or_scrape_product():
    """
    POST Body:
    {
        "query": "Sony WH-1000XM5",     // or "product_name": "..."
        "platform": "both"              // "amazon", "flipkart", "both"
    }
    """
    data = request.get_json(silent=True) or {}
    raw_query = (data.get("query") or data.get("product_name") or data.get("url") or "").strip()
    platform_choice = (data.get("platform") or data.get("source") or "both").lower()

    if not raw_query:
        return jsonify({"error": "Please provide a Product Name or Amazon/Flipkart URL."}), 400

    # Derive clean display name
    product_name = raw_query
    if raw_query.startswith("http://") or raw_query.startswith("https://"):
        product_name = raw_query.split("/")[3].replace("-", " ").title() if len(raw_query.split("/")) > 3 else "Scraped Product"

    # Check database cache for recent duplicate
    existing = database.find_product(product_name)
    if existing:
        product_id = existing["id"]
        reviews = database.get_reviews_for_product(product_id)
        if reviews:
            return jsonify({
                "product_id": product_id,
                "product_name": existing["name"],
                "review_count": len(reviews),
                "cached": True,
                "message": "Loaded cached product review analysis."
            })

    # Collect live reviews from Amazon & Flipkart
    raw_reviews, method = collect_reviews(raw_query, platform_choice=platform_choice)

    if not raw_reviews:
        return jsonify({"error": "No reviews could be found for this product query."}), 404

    # Run VADER & Domain Sentiment Engine
    analyzed_reviews = analyze_reviews_batch(raw_reviews, product_name=product_name)

    # Store in Database
    product_id = database.insert_product(product_name, source=platform_choice, url=raw_query if raw_query.startswith("http") else None)
    database.insert_reviews(product_id, analyzed_reviews)

    return jsonify({
        "product_id": product_id,
        "product_name": product_name,
        "review_count": len(analyzed_reviews),
        "collection_method": method,
        "cached": False,
        "message": f"Successfully analyzed {len(analyzed_reviews)} reviews across Amazon & Flipkart."
    })


@app.route("/api/products", methods=["GET"])
def list_products():
    products = database.list_products()
    return jsonify(products)


@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    database.delete_product(product_id)
    return jsonify({"success": True, "message": "Product deleted successfully."})


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
@app.route("/api/analytics/<int:product_id>", methods=["GET"])
def sentiment_summary(product_id):
    product = database.get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    reviews = database.get_reviews_for_product(product_id)
    if not reviews:
        return jsonify({"error": "No reviews found for this product"}), 404

    total_reviews = len(reviews)
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    ratings_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    platform_stats = {
        "Amazon": {"count": 0, "ratings": []},
        "Flipkart": {"count": 0, "ratings": []}
    }
    all_ratings = []
    trend = {}

    for r in reviews:
        label = r.get("sentiment_label") or "neutral"
        counts[label] = counts.get(label, 0) + 1

        rating = r.get("rating")
        if rating is not None:
            r_int = min(5, max(1, int(round(float(rating)))))
            ratings_dist[r_int] += 1
            all_ratings.append(float(rating))

        platform = r.get("platform") or "Amazon"
        if platform not in platform_stats:
            platform_stats[platform] = {"count": 0, "ratings": []}
        platform_stats[platform]["count"] += 1
        if rating is not None:
            platform_stats[platform]["ratings"].append(float(rating))

        date = r.get("review_date") or "unknown"
        if date not in trend:
            trend[date] = {"positive": 0, "negative": 0, "neutral": 0}
        trend[date][label] += 1

    avg_rating = round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else None
    satisfaction_score = round((counts["positive"] / total_reviews) * 100, 1) if total_reviews else 0

    platform_summary = {}
    for plt, stats in platform_stats.items():
        plt_avg = round(sum(stats["ratings"]) / len(stats["ratings"]), 2) if stats["ratings"] else None
        platform_summary[plt] = {
            "count": stats["count"],
            "average_rating": plt_avg
        }

    trend_sorted = [
        {"date": d, **counts_for_day}
        for d, counts_for_day in sorted(trend.items())
        if d != "unknown"
    ]

    word_freq = get_word_frequency(reviews, top_n=12)
    pros_cons = extract_pros_cons(reviews)

    return jsonify({
        "product": product,
        "total_reviews": total_reviews,
        "satisfaction_score": satisfaction_score,
        "sentiment_counts": counts,
        "average_rating": avg_rating,
        "rating_distribution": ratings_dist,
        "platform_breakdown": platform_summary,
        "pros_and_cons": pros_cons,
        "sentiment_trend": trend_sorted,
        "word_frequency": [{"word": w, "count": c} for w, c in word_freq]
    })


@app.route("/api/export/<int:product_id>", methods=["GET"])
def export_reviews_csv(product_id):
    product = database.get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    reviews = database.get_reviews_for_product(product_id)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Platform", "Rating", "Sentiment Label", "Sentiment Score", "Date", "Title", "Review Text"])

    for r in reviews:
        writer.writerow([
            r.get("id"),
            r.get("platform", "Amazon"),
            r.get("rating"),
            r.get("sentiment_label"),
            r.get("sentiment_score"),
            r.get("review_date"),
            r.get("review_title"),
            r.get("review_text")
        ])

    csv_data = output.getvalue()
    filename = f"sentiment_reviews_{product['name'].replace(' ', '_')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 SentimentAnalyzer running at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
