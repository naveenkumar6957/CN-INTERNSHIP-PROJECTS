"""
sentiment_analysis.py
Classifies review text as positive, negative, or neutral using VADER.

VADER (Valence Aware Dictionary and sEntiment Reasoner) is chosen over
TextBlob because it ships its own lexicon (no separate corpus download
required), it is fast, and it is tuned for short, informal text such as
product reviews.
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text):
    """
    Returns a tuple: (label, compound_score)
    label is one of: "positive", "negative", "neutral"
    compound_score is a float between -1 and 1
    """
    if not text or not text.strip():
        return "neutral", 0.0

    scores = _analyzer.polarity_scores(text)
    compound = scores["compound"]

    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return label, compound


def analyze_reviews_batch(reviews):
    """
    reviews: list of dicts each containing at least 'review_text'
    Adds 'sentiment_label' and 'sentiment_score' to every review dict in place.
    """
    for review in reviews:
        label, score = analyze_sentiment(review.get("review_text", ""))
        review["sentiment_label"] = label
        review["sentiment_score"] = score
    return reviews


STOPWORDS = set("""
a an the this that these those is are was were be been being have has had
do does did will would shall should may might must can could of in on at
to for with without from by as it its it's i you he she we they them his
her our your their and or but if not no so very just really product item
""".split())


def get_word_frequency(reviews, top_n=15):
    """
    Builds a simple word-frequency count from review text, excluding
    common stopwords, for the 'frequently used terms' word-cloud style chart.
    """
    from collections import Counter
    import re

    counter = Counter()
    for review in reviews:
        text = review.get("review_text", "") or ""
        words = re.findall(r"[a-zA-Z']+", text.lower())
        for w in words:
            if len(w) > 2 and w not in STOPWORDS:
                counter[w] += 1

    return counter.most_common(top_n)
