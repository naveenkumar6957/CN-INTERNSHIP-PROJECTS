"""
sentiment_analysis.py
Enhanced sentiment analysis module using VADER, domain-specific e-commerce heuristics,
product-name sanitization, rating calibration, and pros/cons extraction.
"""

import re
from collections import Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

STRONG_NEGATIVE_PHRASES = [
    "terrible", "worst", "broken", "useless", "cheap quality", "waste of money",
    "defective", "damaged", "poor quality", "not working", "disappointed",
    "regret buying", "stopped working", "doesn't work", "don't buy", "horrible",
    "bad product", "waste of time", "faulty", "fake product"
]

STRONG_POSITIVE_PHRASES = [
    "excellent", "amazing", "love it", "superb", "best product", "perfect",
    "worth every penny", "great quality", "awesome", "exceeded expectations",
    "highly recommend", "value for money", "outstanding", "must buy"
]


def sanitize_text_for_vader(text, product_name=None):
    """
    Strips product name keywords from review text before VADER analysis
    so product branding (e.g. 'Smart', 'Ultra', 'Super', 'Pro', 'Best')
    does not skew a negative review into positive sentiment.
    """
    if not product_name or not text:
        return text

    # Extract words from product name that might carry artificial sentiment
    prod_words = set(re.findall(r"[a-zA-Z0-9]+", product_name.lower()))
    
    # Filter out common stop words from product title so we only target brand/model modifiers
    stopwords = {"the", "a", "an", "and", "or", "for", "with", "of", "in", "to", "by"}
    target_words = prod_words - stopwords

    cleaned_words = []
    for word in text.split():
        clean_w = re.sub(r"[^\w]", "", word.lower())
        if clean_w in target_words and clean_w in {"smart", "ultra", "pro", "max", "super", "best", "plus", "prime", "hero"}:
            continue
        cleaned_words.append(word)

    return " ".join(cleaned_words)


def analyze_sentiment(text, product_name=None, rating=None):
    """
    Returns a tuple: (label, compound_score)
    label is one of: "positive", "negative", "neutral"
    compound_score is a float between -1.0 and 1.0
    """
    if not text or not text.strip():
        return "neutral", 0.0

    lower_text = text.lower()

    # 1. Sanitize text for VADER by neutralizing product title terms
    sanitized_text = sanitize_text_for_vader(text, product_name)
    vader_scores = _analyzer.polarity_scores(sanitized_text)
    compound = vader_scores["compound"]

    # 2. Check for strong domain phrases
    neg_matches = sum(1 for phrase in STRONG_NEGATIVE_PHRASES if phrase in lower_text)
    pos_matches = sum(1 for phrase in STRONG_POSITIVE_PHRASES if phrase in lower_text)

    if neg_matches > pos_matches and neg_matches >= 1:
        compound = min(compound, -0.25 * neg_matches)
    elif pos_matches > neg_matches and pos_matches >= 1:
        compound = max(compound, 0.25 * pos_matches)

    # 3. Calibrate using Star Rating if present
    if rating is not None:
        try:
            r = float(rating)
            if r <= 2.0:
                # 1-2 stars: Force negative unless compound is overwhelmingly positive
                if compound > 0.4:
                    compound = -0.1
                else:
                    compound = min(compound, -0.3)
            elif r >= 4.0:
                # 4-5 stars: Force positive unless compound is overwhelmingly negative
                if compound < -0.4:
                    compound = 0.1
                else:
                    compound = max(compound, 0.3)
            elif r == 3.0:
                # 3 stars: Dampen score towards neutral
                compound = compound * 0.5
        except (ValueError, TypeError):
            pass

    # 4. Final classification threshold
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return label, round(float(compound), 4)


def analyze_reviews_batch(reviews, product_name=None):
    """
    Modifies reviews in place, adding sentiment_label and sentiment_score.
    """
    for review in reviews:
        label, score = analyze_sentiment(
            text=review.get("review_text", ""),
            product_name=product_name,
            rating=review.get("rating")
        )
        review["sentiment_label"] = label
        review["sentiment_score"] = score
    return reviews


STOPWORDS = set("""
a an the this that these those is are was were be been being have has had
do does did will would shall should may might must can could of in on at
to for with without from by as it its it's i you he she we they them his
her our your their and or but if not no so very just really product item
buy bought get got using used
""".split())


def get_word_frequency(reviews, top_n=15):
    """
    Builds word frequency count excluding stopwords.
    """
    counter = Counter()
    for review in reviews:
        text = review.get("review_text", "") or ""
        words = re.findall(r"[a-zA-Z']+", text.lower())
        for w in words:
            if len(w) > 2 and w not in STOPWORDS:
                counter[w] += 1
    return counter.most_common(top_n)


PROS_KEYWORDS = [
    ("Great Sound Quality", ["sound", "audio", "bass", "clarity", "music"]),
    ("Excellent Battery Life", ["battery", "backup", "charging", "charge"]),
    ("High Build Quality", ["build", "durable", "sturdy", "premium", "quality", "material"]),
    ("Comfortable Fit", ["comfortable", "fit", "lightweight", "soft", "ear"]),
    ("Fast Shipping / Delivery", ["delivery", "shipping", "fast", "packaged", "packaging"]),
    ("Value for Money", ["value", "money", "worth", "price", "affordable"]),
    ("Great Display", ["display", "screen", "bright", "colors"]),
    ("Easy to Use", ["easy", "setup", "simple", "user friendly"])
]

CONS_KEYWORDS = [
    ("Poor Battery Backup", ["drains", "battery life", "poor battery", "slow charging"]),
    ("Cheap Build / Plastic", ["cheap", "plastic", "fragile", "broke", "damaged"]),
    ("Heating Issues", ["heating", "heats up", "hot", "warm"]),
    ("Connectivity Drops", ["bluetooth", "disconnects", "lag", "pairing", "connection"]),
    ("Bad Sound / Mic", ["mic", "noise", "distortion", "muffled"]),
    ("Overpriced", ["expensive", "costly", "overpriced", "not worth"]),
    ("Slow Delivery / Damaged Box", ["delay", "late", "damaged box", "poor packaging"])
]


def extract_pros_cons(reviews):
    """
    Extracts top positive highlights (Pros) and top negative complaints (Cons)
    from customer reviews.
    """
    pos_reviews = [r for r in reviews if r.get("sentiment_label") == "positive"]
    neg_reviews = [r for r in reviews if r.get("sentiment_label") == "negative"]

    pos_text = " ".join([r.get("review_text", "").lower() for r in pos_reviews])
    neg_text = " ".join([r.get("review_text", "").lower() for r in neg_reviews])

    pros_found = []
    for label, keywords in PROS_KEYWORDS:
        if any(kw in pos_text for kw in keywords):
            pros_found.append(label)

    cons_found = []
    for label, keywords in CONS_KEYWORDS:
        if any(kw in neg_text for kw in keywords):
            cons_found.append(label)

    if not pros_found:
        pros_found = ["Good Overall Performance", "Satisfactory Quality", "Delivered as Described"]
    if not cons_found:
        cons_found = ["Minor Packaging Imperfections", "Average Delivery Time"]

    return {
        "pros": pros_found[:5],
        "cons": cons_found[:5]
    }
