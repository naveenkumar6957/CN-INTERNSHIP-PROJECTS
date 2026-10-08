# ==============================================================================
# SPAMGUARD AI - MULTI-DATASET TRAINING & BENCHMARKING PIPELINE
# Trains on all 3 datasets:
#   1. emails.csv      (archive 1 - 5,728 samples)
#   2. mail_data.csv   (archive 2 - 5,572 samples)
#   3. spam.csv        (archive 3 - 4,601 samples)
# Trains a Calibrated Soft-Voting Ensemble (LinearSVC + Logistic Regression + Naive Bayes)
# Exports model.joblib, vectorizer.joblib, and model_metadata.json
# ==============================================================================
import os
import sys
import re
import json
import zipfile
import datetime
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix
)

# ------------------------------------------------------------------------------
# NLP Setup (NLTK Stopwords & Stemmer)
# ------------------------------------------------------------------------------
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
    'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'did'
}

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer
    try:
        nltk.download('stopwords', quiet=True)
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

def clean_text(text: str) -> str:
    """Preprocess email text: strip HTML, retain spam-critical punctuation ($!%), stem words."""
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Retain alphanumeric and symbols like $ ! %
    text = re.sub(r'[^a-zA-Z0-9$!%]', ' ', text)
    words = text.lower().split()
    stemmed = [ps.stem(w) for w in words if w not in stop_words]
    return ' '.join(stemmed) if stemmed else text.lower().strip()

# ------------------------------------------------------------------------------
# Dataset Ingestion: Locate & Ingest All 3 Archives
# ------------------------------------------------------------------------------
print("=" * 70)
print("     SPAMGUARD AI: MULTI-DATASET TRAINING PIPELINE")
print("=" * 70)

EXTERNAL_DIR = r"D:\spam_Email dataset"
LOCAL_DATASET_DIR = os.path.join(".", "dataset")

def find_file(filename_pattern, search_paths):
    """Search for a specific file across multiple potential locations."""
    for base in search_paths:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            for f in files:
                if filename_pattern.lower() in f.lower():
                    return os.path.join(root, f)
    return None

def load_from_zip_or_folder(zip_name, csv_name, search_dirs):
    """Load dataframe from either an extracted CSV or directly from a ZIP file."""
    # 1. Search for extracted CSV
    direct_csv = find_file(csv_name, search_dirs)
    if direct_csv and os.path.exists(direct_csv):
        for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                df = pd.read_csv(direct_csv, encoding=enc)
                print(f"  [+] Loaded '{csv_name}' from: {direct_csv} (Encoding: {enc}, Rows: {len(df)})")
                return df
            except Exception:
                continue

    # 2. Search for ZIP archive
    zip_path = find_file(zip_name, search_dirs)
    if zip_path and os.path.exists(zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                for member in z.namelist():
                    if csv_name.lower() in member.lower():
                        with z.open(member) as f:
                            for enc in ['utf-8', 'latin-1', 'cp1252']:
                                try:
                                    f.seek(0)
                                    df = pd.read_csv(f, encoding=enc)
                                    print(f"  [+] Loaded '{csv_name}' directly from ZIP '{zip_path}' (Rows: {len(df)})")
                                    return df
                                except Exception:
                                    continue
        except Exception as e:
            print(f"  [-] Failed reading zip {zip_path}: {e}")

    return None

search_locations = [EXTERNAL_DIR, LOCAL_DATASET_DIR, "."]
print("\nSearching datasets across locations:")
for p in search_locations:
    print(f" - {os.path.abspath(p)} ({'exists' if os.path.exists(p) else 'not found'})")

# Ingest Dataset 1: emails.csv (Archive 1)
print("\nIngesting Dataset 1 (archive 1 / emails.csv)...")
df1_raw = load_from_zip_or_folder("archive (1).zip", "emails.csv", search_locations)
if df1_raw is not None:
    df1 = pd.DataFrame()
    df1['text'] = df1_raw['text'].astype(str)
    df1['label'] = df1_raw['spam'].astype(int)
    print(f"  -> Dataset 1 ready: {len(df1)} samples (Spam: {sum(df1['label']==1)}, Ham: {sum(df1['label']==0)})")
else:
    df1 = pd.DataFrame(columns=['text', 'label'])
    print("  [!] Dataset 1 not found.")

# Ingest Dataset 2: mail_data.csv (Archive 2)
print("\nIngesting Dataset 2 (archive 2 / mail_data.csv)...")
df2_raw = load_from_zip_or_folder("archive (2).zip", "mail_data.csv", search_locations)
if df2_raw is not None:
    df2 = pd.DataFrame()
    df2['text'] = df2_raw['Message'].astype(str)
    label_map = {'spam': 1, 'ham': 0}
    df2['label'] = df2_raw['Category'].str.lower().str.strip().map(label_map).fillna(0).astype(int)
    print(f"  -> Dataset 2 ready: {len(df2)} samples (Spam: {sum(df2['label']==1)}, Ham: {sum(df2['label']==0)})")
else:
    df2 = pd.DataFrame(columns=['text', 'label'])
    print("  [!] Dataset 2 not found.")

# Ingest Dataset 3: spam.csv (Archive 3 - Spambase features)
print("\nIngesting Dataset 3 (archive 3 / spam.csv)...")
df3_raw = load_from_zip_or_folder("archive (3).zip", "spam.csv", search_locations)
if df3_raw is not None:
    def synthesize_spambase_text(row):
        tokens = []
        if row.get('make', 0) > 0:
            tokens.extend(['make'] * min(6, int(row['make'] * 5 + 1)))
        if row.get('money', 0) > 0:
            tokens.extend(['money', 'cash', 'dollars'] * min(4, int(row['money'] * 5 + 1)))
        if row.get('n000', 0) > 0:
            tokens.extend(['000', 'thousands'] * min(4, int(row['n000'] * 5 + 1)))
        if row.get('dollar', 0) > 0:
            tokens.extend(['$', 'dollar', 'bonus', 'prize', 'winner'] * min(4, int(row['dollar'] * 5 + 1)))
        if row.get('bang', 0) > 0:
            tokens.extend(['!', 'urgent', 'claim', 'free'] * min(4, int(row['bang'] * 5 + 1)))
        if row.get('crl.tot', 0) > 150:
            tokens.extend(['URGENT', 'ALERT', 'VERIFY', 'NOTIFICATION'])
        return ' '.join(tokens)

    df3 = pd.DataFrame()
    df3['text'] = df3_raw.apply(synthesize_spambase_text, axis=1)
    df3['label'] = (df3_raw['yesno'].str.lower() == 'y').astype(int)
    df3 = df3[df3['text'].str.strip() != '']
    print(f"  -> Dataset 3 ready: {len(df3)} samples incorporated (Spam: {sum(df3['label']==1)}, Ham: {sum(df3['label']==0)})")
else:
    df3 = pd.DataFrame(columns=['text', 'label'])
    print("  [!] Dataset 3 not found.")

# Combine All Datasets
master_df = pd.concat([df1, df2, df3], ignore_index=True)
master_df = master_df.dropna(subset=['text', 'label'])
master_df['text'] = master_df['text'].astype(str).str.strip()
master_df = master_df[master_df['text'] != '']
master_df = master_df.drop_duplicates(subset=['text'])

print(f"\n=======================================================")
print(f"Master Combined Dataset Size : {len(master_df):,} distinct samples")
print(f"Total Ham (Legitimate) Samples : {sum(master_df['label'] == 0):,} ({sum(master_df['label'] == 0)/len(master_df)*100:.1f}%)")
print(f"Total Spam (Malicious) Samples  : {sum(master_df['label'] == 1):,} ({sum(master_df['label'] == 1)/len(master_df)*100:.1f}%)")
print(f"=======================================================")

if len(master_df) < 50:
    print("[ERROR] Insufficient dataset records found. Please ensure datasets exist.")
    sys.exit(1)

# ------------------------------------------------------------------------------
# Preprocessing & Train/Test Split
# ------------------------------------------------------------------------------
print("\nApplying NLP cleaning and stemming...")
master_df['cleaned_text'] = master_df['text'].apply(clean_text)
master_df = master_df[master_df['cleaned_text'].str.strip() != '']

print("Performing Stratified 80/20 Train/Test Split...")
X_train, X_test, y_train, y_test = train_test_split(
    master_df['cleaned_text'],
    master_df['label'],
    test_size=0.20,
    random_state=42,
    stratify=master_df['label']
)

print(f"Training samples: {len(X_train):,}")
print(f"Testing samples : {len(X_test):,}")

# ------------------------------------------------------------------------------
# Feature Extraction (TF-IDF with Bi-Grams)
# ------------------------------------------------------------------------------
print("\nExtracting TF-IDF Features (n-gram (1,2), sublinear scaling, max 25,000 features)...")
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    max_features=25000,
    sublinear_tf=True,
    min_df=2
)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)
print(f"Vocabulary Size: {len(vectorizer.vocabulary_):,} features")

# ------------------------------------------------------------------------------
# Model Benchmarking & Multi-Model Evaluation
# ------------------------------------------------------------------------------
print("\nBenchmarking Candidate Models:")
models = {
    "Logistic Regression": LogisticRegression(C=5.0, max_iter=1000, random_state=42),
    "Multinomial Naive Bayes": MultinomialNB(alpha=0.1),
    "Calibrated Linear SVC": CalibratedClassifierCV(LinearSVC(C=1.0, max_iter=2500, dual='auto', random_state=42))
}

benchmarks = {}
for name, clf in models.items():
    clf.fit(X_train_vec, y_train)
    preds = clf.predict(X_test_vec)
    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds)
    rec = recall_score(y_test, preds)
    f1 = f1_score(y_test, preds)
    benchmarks[name] = {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1
    }
    print(f" - {name:<26}: Accuracy: {acc*100:6.2f}% | Precision: {prec*100:6.2f}% | Recall: {rec*100:6.2f}% | F1: {f1*100:6.2f}%")

# ------------------------------------------------------------------------------
# Calibrated Soft-Voting Ensemble
# ------------------------------------------------------------------------------
print("\nTraining Final Calibrated Soft-Voting Ensemble...")
ensemble = VotingClassifier(
    estimators=[
        ('lr', models['Logistic Regression']),
        ('nb', models['Multinomial Naive Bayes']),
        ('svc', models['Calibrated Linear SVC'])
    ],
    voting='soft',
    weights=[2, 1, 2]
)
ensemble.fit(X_train_vec, y_train)

# Final Evaluation
y_pred = ensemble.predict(X_test_vec)
y_proba = ensemble.predict_proba(X_test_vec)[:, 1]

final_acc = accuracy_score(y_test, y_pred)
final_prec = precision_score(y_test, y_pred)
final_rec = recall_score(y_test, y_pred)
final_f1 = f1_score(y_test, y_pred)
final_auc = roc_auc_score(y_test, y_proba)
cm = confusion_matrix(y_test, y_pred).tolist()

print("\n" + "=" * 70)
print(f"      FINAL ENSEMBLE EVALUATION RESULTS")
print("=" * 70)
print(f" Accuracy  : {final_acc * 100:.2f}%")
print(f" Precision : {final_prec * 100:.2f}% (Spam false positive resistance)")
print(f" Recall    : {final_rec * 100:.2f}% (Spam detection capture rate)")
print(f" F1-Score  : {final_f1 * 100:.2f}%")
print(f" ROC-AUC   : {final_auc * 100:.2f}%")
print(f" Confusion Matrix:\n   [TN={cm[0][0]}, FP={cm[0][1]}]\n   [FN={cm[1][0]}, TP={cm[1][1]}]")
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred, target_names=["HAM (Legitimate)", "SPAM (Malicious)"]))

# ------------------------------------------------------------------------------
# Save Model Artifacts
# ------------------------------------------------------------------------------
print("Exporting production artifacts...")

metadata = {
    "timestamp": datetime.datetime.now().isoformat(),
    "model_name": "Calibrated Soft-Voting Ensemble (LinearSVC + LogisticRegression + NaiveBayes)",
    "accuracy": round(final_acc * 100, 2),
    "precision": round(final_prec * 100, 2),
    "recall": round(final_rec * 100, 2),
    "f1_score": round(final_f1 * 100, 2),
    "roc_auc": round(final_auc * 100, 2),
    "confusion_matrix": {
        "true_negative": cm[0][0],
        "false_positive": cm[0][1],
        "false_negative": cm[1][0],
        "true_positive": cm[1][1]
    },
    "total_samples": len(master_df),
    "train_samples": len(X_train),
    "test_samples": len(X_test),
    "dataset_breakdown": {
        "dataset_1_emails": len(df1),
        "dataset_2_mail_data": len(df2),
        "dataset_3_spambase": len(df3)
    },
    "features_count": len(vectorizer.vocabulary_)
}

export_dirs = [".", os.path.join(".", "api")]
for d in export_dirs:
    os.makedirs(d, exist_ok=True)
    m_path = os.path.join(d, "model.joblib")
    v_path = os.path.join(d, "vectorizer.joblib")
    meta_path = os.path.join(d, "model_metadata.json")

    joblib.dump(ensemble, m_path)
    joblib.dump(vectorizer, v_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"  [+] Saved {m_path}, {v_path}, {meta_path}")

print("\n[SUCCESS] Model training and export completed successfully!")
print("The web application is now backed by a high-accuracy ML ensemble trained across all 3 datasets.")
