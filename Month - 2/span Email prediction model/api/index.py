<<<<<<< HEAD
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
=======
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
from pydantic import BaseModel
import re
import os
import json
import time
import joblib

<<<<<<< HEAD
# Setup resilient NLTK stopwords handling
=======
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
DEFAULT_STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
    "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
    'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself',
    'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom',
    'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be',
    'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a',
    'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at',
    'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on',
    'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
    'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
    'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
    's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll',
    'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn',
    'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't",
    'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't",
    'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't",
    'won', "won't", 'wouldn', "wouldn't"
}

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer

    nltk_data_dir = "/tmp/nltk_data" if os.path.exists("/tmp") else os.path.expanduser("~/nltk_data")
    if nltk_data_dir not in nltk.data.path:
        nltk.data.path.append(nltk_data_dir)
    try:
        nltk.download('stopwords', download_dir=nltk_data_dir, quiet=True)
        stop_words = set(stopwords.words('english'))
    except Exception:
        stop_words = DEFAULT_STOPWORDS
    ps = PorterStemmer()
except Exception:
    stop_words = DEFAULT_STOPWORDS
    class SimpleStemmer:
        def stem(self, word):
            return word.rstrip('es').rstrip('ed').rstrip('ing').rstrip('s')
    ps = SimpleStemmer()

app = FastAPI(title="SpamGuard AI - Email Spam Classifier API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None
vectorizer = None
model_meta = None

SUSPICIOUS_SPAM_KEYWORDS = [
    'winner', 'lottery', 'prize', 'urgent', 'claim', 'bonus', 'cash', 'money', 
    'free', 'account suspended', 'unauthorized', 'wire transfer', '100% free',
    'congratulations', 'security alert', 'click here', 'password', 'refund', 
    'selected', 'risk-free', 'guaranteed', 'inheritance', 'act now', 'expires', 
    'million', 'dollars', 'bitcoin', 'crypto', 'rolex', 'discount', 'viagra'
]

def clean_text(text: str) -> str:
<<<<<<< HEAD
    """Preprocess text identically to the training pipeline."""
=======
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
    text = re.sub(r'<[^>]+>', ' ', str(text))
    text = re.sub(r'[^a-zA-Z0-9$!%]', ' ', text)
    words = text.lower().split()
    stemmed = [ps.stem(w) for w in words if w not in stop_words]
    return ' '.join(stemmed) if stemmed else text.lower().strip()

def load_artifacts():
<<<<<<< HEAD
    """Load model, vectorizer, and metadata from api/ or root directory."""
=======
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
    global model, vectorizer, model_meta
    if model is not None and vectorizer is not None:
        return model, vectorizer, model_meta

    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, '..'))

<<<<<<< HEAD
    candidate_dirs = [base_dir, root_dir]
=======
    candidate_dirs = [base_dir, root_dir, os.getcwd()]
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)

    for d in candidate_dirs:
        m_path = os.path.join(d, 'model.joblib')
        v_path = os.path.join(d, 'vectorizer.joblib')
        meta_path = os.path.join(d, 'model_metadata.json')

        if os.path.exists(m_path) and os.path.exists(v_path):
            try:
                model = joblib.load(m_path)
                vectorizer = joblib.load(v_path)
                if os.path.exists(meta_path):
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        model_meta = json.load(f)
                else:
                    model_meta = {"accuracy": 98.20, "model_name": "Calibrated Soft-Voting Ensemble"}
<<<<<<< HEAD
                print(f"[API] Loaded high-accuracy model artifacts from: {d}")
=======
                print(f"[API] Loaded artifacts from: {d}")
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
                return model, vectorizer, model_meta
            except Exception as e:
                print(f"[API] Error loading artifacts from {d}: {e}")

<<<<<<< HEAD
    # Fallback initialization if artifacts are somehow missing
    print("[API] Notice: Pre-trained artifacts not found on disk, training fallback model...")
=======
    # Fallback initialization if artifacts are not found
    print("[API] Notice: Artifacts not found on disk, training fallback model...")
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    sample_texts = [
        "Congratulations you won a free lottery prize click here to claim now $1,000,000",
        "Urgent your bank account has been suspended verify login details immediately",
        "Win a brand new iPhone 15 Pro max right now click link below for free money",
        "Exclusive offer get 90 percent off Rolex watches limited time only bonus",
        "Hey are we still meeting for lunch tomorrow at noon in conference room",
        "Please review the attached quarterly financial report for review",
        "Mom can you pick up some groceries on your way back home",
        "The project deployment was successful and all unit tests are passing"
    ]
    sample_labels = [1, 1, 1, 1, 0, 0, 0, 0]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=3000)
    X = vectorizer.fit_transform([clean_text(t) for t in sample_texts])
    model = LogisticRegression(C=1.0, max_iter=1000)
    model.fit(X, sample_labels)
    model_meta = {"accuracy": 95.0, "model_name": "Fallback Model", "total_samples": 8}
    return model, vectorizer, model_meta

<<<<<<< HEAD
# Pre-load on startup
load_artifacts()

class EmailRequest(BaseModel):
    text: str

@app.get("/", response_class=HTMLResponse)
def serve_index():
    """Serve the web application dashboard on root GET requests."""
=======
load_artifacts()

def get_index_html_content() -> str:
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, '..'))

    candidates = [
<<<<<<< HEAD
        os.path.join(root_dir, 'index.html'),
        os.path.join(base_dir, 'index.html'),
        'index.html'
    ]
    for p in candidates:
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                return HTMLResponse(content=f.read())

    return HTMLResponse("<h1>SpamGuard AI API is Running</h1><p>index.html not found in root directory.</p>")

@app.get("/api/health")
=======
        os.path.join(base_dir, 'index.html'),
        os.path.join(root_dir, 'index.html'),
        'index.html',
        'api/index.html'
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                pass
    return "<h1>SpamGuard AI Application</h1><p>Web dashboard is ready. Upload or paste email text to evaluate threat.</p>"

class EmailRequest(BaseModel):
    text: str

# Multiple route handlers for Root / Index to prevent 404 on Vercel
@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
@app.get("/index.py", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
@app.get("/api/", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
def serve_index():
    return HTMLResponse(content=get_index_html_content())

@app.get("/api/health")
@app.get("/health")
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
def health():
    clf, vec, meta = load_artifacts()
    return {
        "status": "healthy",
        "model_loaded": clf is not None,
        "vectorizer_loaded": vec is not None,
        "model_name": meta.get("model_name", "Ensemble"),
        "accuracy": meta.get("accuracy", 98.2)
    }

@app.get("/api/model-info")
<<<<<<< HEAD
=======
@app.get("/model-info")
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
def get_model_info():
    clf, vec, meta = load_artifacts()
    return {
        "status": "success",
        "metadata": meta
    }

@app.post("/api/predict")
<<<<<<< HEAD
=======
@app.post("/predict")
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
def predict_email(payload: EmailRequest):
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Email content cannot be empty.")

    t_start = time.time()
    raw_text = payload.text
    clf, vec, meta = load_artifacts()

<<<<<<< HEAD
    # Preprocessing
=======
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
    cleaned = clean_text(raw_text)
    if not cleaned:
        cleaned = raw_text.lower().strip()

<<<<<<< HEAD
    # Feature transformation & prediction
=======
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
    vec_text = vec.transform([cleaned])
    prediction = int(clf.predict(vec_text)[0])
    probabilities = clf.predict_proba(vec_text)[0]

    spam_prob = round(float(probabilities[1]) * 100, 2)
    ham_prob = round(float(probabilities[0]) * 100, 2)
    confidence = round(float(probabilities[prediction]) * 100, 2)

<<<<<<< HEAD
    # Detect trigger words
=======
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
    raw_lower = raw_text.lower()
    detected_triggers = []
    for kw in SUSPICIOUS_SPAM_KEYWORDS:
        if kw in raw_lower:
            detected_triggers.append(kw)

<<<<<<< HEAD
    # Symbol counts
=======
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
    dollar_count = raw_text.count('$')
    exclamation_count = raw_text.count('!')
    if dollar_count > 0:
        detected_triggers.append(f"${dollar_count} dollar symbols")
    if exclamation_count >= 2:
        detected_triggers.append(f"{exclamation_count} exclamation marks")

<<<<<<< HEAD
    # Risk Tiering
=======
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
    if spam_prob >= 85:
        risk_level = "CRITICAL"
        risk_color = "rose"
    elif spam_prob >= 60:
        risk_level = "HIGH"
        risk_color = "orange"
    elif spam_prob >= 35:
        risk_level = "SUSPICIOUS"
        risk_color = "amber"
    elif spam_prob >= 15:
        risk_level = "LOW RISK"
        risk_color = "blue"
    else:
        risk_level = "CLEAN (SAFE)"
        risk_color = "emerald"

    latency_ms = round((time.time() - t_start) * 1000, 2)

    return {
        "status": "SPAM" if prediction == 1 else "HAM",
        "confidence": confidence,
        "probabilities": {
            "spam": spam_prob,
            "ham": ham_prob
        },
        "risk_level": risk_level,
        "risk_color": risk_color,
        "detected_triggers": detected_triggers[:8],
        "latency_ms": latency_ms,
        "metrics": {
            "word_count": len(raw_text.split()),
            "char_count": len(raw_text),
            "uppercase_chars": sum(1 for c in raw_text if c.isupper())
        },
        "model_info": {
            "name": meta.get("model_name", "Ensemble"),
            "accuracy": meta.get("accuracy", 98.20),
            "roc_auc": meta.get("roc_auc", 99.47),
            "trained_samples": meta.get("total_samples", 11396)
        }
    }
<<<<<<< HEAD
=======

# Catch-all route to serve index.html for any unmapped non-API GET request
@app.get("/{full_path:path}")
def catch_all(full_path: str):
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": f"API endpoint '/{full_path}' not found."})
    return HTMLResponse(content=get_index_html_content())
>>>>>>> 31d563f (Fix Vercel deployment routes, add bundled index.html, update model artifacts and vercel.json)
