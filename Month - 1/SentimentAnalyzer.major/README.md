# Product Sentiment Analyzer and Review Dashboard

A lightweight, fully free web application that collects product reviews,
classifies each one as positive, negative, or neutral, and displays the
results on an interactive dashboard.

## What is inside

| Part | File | What it does |
|---|---|---|
| Backend + API | `app.py` | Flask app serving both the REST API and the dashboard |
| Database | `database.py` | SQLite storage for products and reviews |
| Review collection | `scraper.py` | Generic page scraper, plus a demo data generator |
| Sentiment engine | `sentiment_analysis.py` | VADER-based classification and word-frequency counting |
| Dashboard | `static/index.html`, `static/style.css`, `static/script.js` | The interface: search box, sentiment charts, review list |

## Why this stack (the lightweight, free choices)

- **Flask** instead of Django - a single small file is enough for this API, no heavy framework needed.
- **SQLite** instead of MongoDB/PostgreSQL - zero setup, zero cost, one file (`sentiment_data.db`), perfect for a small-to-medium review dataset.
- **VADER** instead of TextBlob - no separate corpus download, fast, and tuned for short review-style text.
- **Plain HTML/CSS/JS + Chart.js (CDN)** instead of React - no build step, no `npm install`, works by just opening the page.
- **requests + BeautifulSoup** instead of Selenium - no browser driver to install, much lighter to run and host.

## A note on scraping Amazon and Flipkart

Amazon and Flipkart render their review sections with JavaScript and
actively block automated tools with CAPTCHAs and IP blocking, and scraping
them goes against their Terms of Service. A lightweight tool like this one
cannot reliably or legally pull live reviews from them.

To keep the project genuinely useful and fully working, it ships with two
review-collection modes you choose from the dashboard:

1. **Sample data mode** - instantly generates a realistic, randomized set
   of reviews for whatever product name you type, so you can fully explore
   search, sentiment scoring, and every chart right away.
2. **URL scrape mode** - give it the link to any product/review page that
   renders its reviews as plain HTML (many smaller e-commerce and review
   sites do), and it will attempt to extract and analyze real review text
   from that page. If nothing usable is found, it automatically falls back
   to sample data so the dashboard never breaks.

If you need real Amazon or Flipkart data for a production use case, the
correct and legal route is their official Product Advertising API /
Affiliate APIs rather than scraping.

## Running it

You will need Python 3.9 or newer installed.

1. Install the dependencies listed in `requirements.txt`.
2. Start the app by running the `app.py` file with Python.
3. Open `http://localhost:5000` in your browser.

The database file `sentiment_data.db` is created automatically the first
time you run the app - no extra setup needed.

## Using the dashboard

1. Type a product name in the search box.
2. Choose "Sample data" for an instant demo, or "Scrape a product page URL"
   and paste a link.
3. Click "Analyze reviews."
4. The dashboard shows:
   - A headline positive-sentiment percentage
   - Total reviews analyzed and average rating
   - A sentiment distribution chart (positive / neutral / negative)
   - A sentiment trend chart over time
   - The most frequently used words across all reviews
   - The individual reviews, filterable by sentiment
5. Previously analyzed products appear in the sidebar so you can revisit
   them without re-running the analysis.

## API reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/search` | POST | Collect and analyze reviews for a product |
| `/api/products` | GET | List all previously analyzed products |
| `/api/reviews/<product_id>` | GET | Get all stored reviews for a product |
| `/api/sentiment-summary/<product_id>` | GET | Get sentiment counts, trend, and word frequency |
| `/api/health` | GET | Simple health check |

Example request body for `/api/search`:

```json
{
  "product_name": "Wireless Earbuds X200",
  "source": "demo"
}
```

or, to attempt a real scrape:

```json
{
  "product_name": "Wireless Earbuds X200",
  "source": "url",
  "url": "https://example.com/product/wireless-earbuds-x200/reviews"
}
```

## Free deployment (Render)

This whole app - API and dashboard together - can be deployed as a single
free web service on Render, since it is one Flask app serving everything.

1. Push this project to a GitHub repository.
2. Create a free account at render.com and connect that repository.
3. Render will detect the included `render.yaml` file and set everything
   up automatically: it installs `requirements.txt` and starts the app
   with `gunicorn app:app` on Render's free tier.
4. Once deployed, Render gives you a public URL - the dashboard and the
   API are both available at that same address.

No separate frontend hosting (Vercel/Netlify) is needed, since the
dashboard is served directly by the same Flask app - this keeps the whole
project on a single free service instead of three.

## Notes on the free SQLite database on Render's free tier

Render's free web services use an ephemeral filesystem, so the SQLite
file resets on redeploys or restarts. For a personal project or portfolio
demo this is fine. If you need the data to persist permanently for free,
the lightest options are:
- Render's free PostgreSQL tier (90-day free database, replace `database.py`'s
  connection with a PostgreSQL driver such as `psycopg2`)
- Supabase's free PostgreSQL tier
- MongoDB Atlas's free shared cluster

The database layer is isolated in `database.py`, so switching later only
means changing that one file.
