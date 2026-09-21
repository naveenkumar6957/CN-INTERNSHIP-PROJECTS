# CN - INTERNSHIP PROJECTS

Repository containing all internship projects organized by month.

## Directory Structure

```text
CN - INTERNSHIP PROJECTS/
├── Month - 1/
│   ├── MovieRating.mini/          # IMDB Top 250 Movie Scraper & Rating Tracker
│   ├── SentimentAnalyzer.major/    # E-Commerce Product Sentiment Analyzer & Review Dashboard
│   └── cryptotracker.mini/         # Cryptocurrency Live Price Tracker & Historical Analyzer
├── Month - 2/                      # Month 2 Internship Projects
└── Month - 3/                      # Month 3 Internship Projects
```

## Month 1 Projects Overview

### 1. SentimentAnalyzer.major (Major Project)
A full-stack Flask web application and sentiment analysis dashboard for e-commerce product reviews using VADER Sentiment Analysis and SQLite database.
- **Frontend**: HTML5, CSS3, JavaScript (Chart.js dashboard)
- **Backend**: Python Flask REST API
- **NLP**: `vaderSentiment`
- **Database**: SQLite3

### 2. MovieRating.mini (Mini Project)
Python web scraper built using `requests` and `BeautifulSoup` to scrape top movie ratings and store them in CSV format.

### 3. cryptotracker.mini (Mini Project)
Cryptocurrency price tracking script that pulls crypto data and logs historical price data to CSV.

---

## How to Run SentimentAnalyzer.major

1. Navigate to the project directory:
   ```bash
   cd "Month - 1/SentimentAnalyzer.major"
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open your browser at `http://localhost:5000`
