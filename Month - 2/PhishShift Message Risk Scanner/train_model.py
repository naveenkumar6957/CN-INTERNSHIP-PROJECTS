#!/usr/bin/env python3
"""
PhishShift - Message Risk Scanner
Production Training & Model Export Pipeline
=============================================================================
Architecture:
  - Text Normalization & Tokenization (lowercase, word regex matching)
  - TF-IDF Vectorizer (max_features=5000, sublinear_tf=False, norm='l2')
  - Multi-Layer Perceptron (MLPClassifier, hidden_layer_sizes=(100,), activation='relu', solver='adam')
  - Strict Train/Test Separation (no data leakage; TF-IDF fit only on training split)
  - Evaluation: Accuracy, Precision, Recall, F1-Score, Confusion Matrix
  - Serialization: Versioned JSON artifact for browser-side deterministic inference
=============================================================================
"""

import os
import sys
import re
import json
import time
import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# -----------------------------------------------------------------------------
# Configuration Constants
# -----------------------------------------------------------------------------
RANDOM_STATE = 42
MAX_FEATURES = 5000
HIDDEN_LAYER_SIZE = 100
MAX_ITER = 60
DECISION_THRESHOLD = 0.50
MODEL_VERSION = "1.0.0"
EXPORT_JSON_PATH = "model.json"

# Search paths for datasets across environments
SEARCH_PATHS = [
    Path("."),
    Path("./dataset"),
    Path("./data"),
    Path("../span Email prediction model/dataset"),
    Path("../span Email prediction model/dataset/archive_1"),
    Path("../span Email prediction model/dataset/archive_2"),
    Path("../dataset"),
]

# -----------------------------------------------------------------------------
# Dataset Adapters
# -----------------------------------------------------------------------------
class DatasetAdapter:
    """Base adapter class for disparate phishing and messaging datasets."""
    name: str

    def can_adapt(self, df: pd.DataFrame, file_path: Path) -> bool:
        raise NotImplementedError

    def adapt(self, df: pd.DataFrame, file_path: Path) -> pd.DataFrame:
        """
        Returns DataFrame with standardized schema:
          - text: str (raw message content)
          - label: int (1 = phishing/smishing/malicious spam; 0 = legitimate/ham)
          - source: str (dataset identifier)
        """
        raise NotImplementedError


class SmsMailDataAdapter(DatasetAdapter):
    """Adapter for UCI SMS Spam Collection / mail_data.csv."""
    name = "SMS Spam Collection (mail_data.csv)"

    def can_adapt(self, df: pd.DataFrame, file_path: Path) -> bool:
        cols = [c.lower() for c in df.columns]
        return "category" in cols and "message" in cols

    def adapt(self, df: pd.DataFrame, file_path: Path) -> pd.DataFrame:
        norm_cols = {c: c.lower() for c in df.columns}
        df = df.rename(columns=norm_cols)
        clean = pd.DataFrame()
        clean["text"] = df["message"].astype(str).str.strip()
        
        # Policy:
        # 'spam' -> 1 (smishing, scam, aggressive fraudulent broadcast)
        # 'ham'  -> 0 (legitimate personal/informational message)
        label_map = {"spam": 1, "ham": 0}
        clean["label"] = df["category"].astype(str).str.lower().str.strip().map(label_map)
        clean["source"] = "sms_spam_collection"
        return clean.dropna(subset=["text", "label"])


class EmailSpamDatasetAdapter(DatasetAdapter):
    """Adapter for Enron / SpamAssassin emails.csv."""
    name = "Email Phishing/Spam Dataset (emails.csv)"

    def can_adapt(self, df: pd.DataFrame, file_path: Path) -> bool:
        cols = [c.lower() for c in df.columns]
        return "text" in cols and "spam" in cols

    def adapt(self, df: pd.DataFrame, file_path: Path) -> pd.DataFrame:
        norm_cols = {c: c.lower() for c in df.columns}
        df = df.rename(columns=norm_cols)
        clean = pd.DataFrame()
        
        # Strip common email header artifacts like 'Subject: ' to focus on semantic content
        def sanitize_email_text(raw: str) -> str:
            if not isinstance(raw, str):
                return ""
            # Remove leading Subject: if present
            s = re.sub(r"^\s*subject:\s*", "", raw, flags=re.IGNORECASE)
            return s.strip()

        clean["text"] = df["text"].astype(str).apply(sanitize_email_text)
        clean["label"] = pd.to_numeric(df["spam"], errors="coerce")
        clean["source"] = "email_spam_dataset"
        return clean.dropna(subset=["text", "label"])


class GenericTextLabelAdapter(DatasetAdapter):
    """Fallback adapter for generic CSVs with text/message and label/target columns."""
    name = "Generic Text/Label CSV"

    def can_adapt(self, df: pd.DataFrame, file_path: Path) -> bool:
        cols = [c.lower() for c in df.columns]
        has_text = any(t in cols for t in ["text", "message", "body", "sms", "email_text", "content"])
        has_label = any(l in cols for l in ["label", "target", "class", "is_spam", "is_phishing"])
        return has_text and has_label

    def adapt(self, df: pd.DataFrame, file_path: Path) -> pd.DataFrame:
        cols_lower = {c: c.lower() for c in df.columns}
        df = df.rename(columns=cols_lower)
        text_col = next(t for t in ["text", "message", "body", "sms", "email_text", "content"] if t in df.columns)
        label_col = next(l for l in ["label", "target", "class", "is_spam", "is_phishing"] if l in df.columns)

        clean = pd.DataFrame()
        clean["text"] = df[text_col].astype(str).str.strip()

        # Handle diverse label formats (numeric, string, boolean)
        def map_label(val: Any) -> Optional[int]:
            s = str(val).lower().strip()
            if s in ["1", "1.0", "spam", "phishing", "smishing", "scam", "malicious", "true", "yes"]:
                return 1
            if s in ["0", "0.0", "ham", "legitimate", "normal", "clean", "false", "no"]:
                return 0
            # Explicit promotional message policy:
            # Commercial advertisements without phishing intent are treated as 0 (not phishing)
            # or dropped if ambiguous.
            if s in ["promo", "advertisement", "marketing"]:
                return 0
            return None

        clean["label"] = df[label_col].apply(map_label)
        clean["source"] = file_path.stem
        return clean.dropna(subset=["text", "label"])


ADAPTERS: List[DatasetAdapter] = [
    SmsMailDataAdapter(),
    EmailSpamDatasetAdapter(),
    GenericTextLabelAdapter(),
]

# -----------------------------------------------------------------------------
# Curated Representative Domain Seed Data
# Ensures consistent baseline smishing and phishing detection coverage
# -----------------------------------------------------------------------------
SEED_MESSAGES = [
    # Smishing / Phishing examples (Label 1)
    ("ALERT: Your banking access is temporarily locked due to unauthorized activity. Verify your identity now at https://secure-bank-login.example/verify", 1, "seed_smishing"),
    ("Urgent notification: Your parcel delivery was suspended due to unpaid customs fee ($2.80). Resolve immediately: http://track-postal-parcel.example/pay", 1, "seed_smishing"),
    ("Notice: Your Netflix subscription has expired. Update your billing card within 12 hours to maintain service: https://netflix-update-billing.example/login", 1, "seed_smishing"),
    ("INTERNAL REVENUE: You have an outstanding tax refund of $840.00. Submit your direct deposit details immediately: http://irs-gov-refund.example/claim", 1, "seed_smishing"),
    ("SECURITY WARNING: A new device logged into your Apple ID. If this was not you, lock your account immediately: https://appleid-security-auth.example/reset", 1, "seed_smishing"),
    ("Final reminder: Your mobile plan will be terminated today. Settle your outstanding balance of $34.50 now: http://mobile-bill-payment.example", 1, "seed_smishing"),
    ("Congratulations! You won a $1,000 Walmart gift card in our monthly customer sweepstakes. Claim your prize here: http://giftcard-winners.example", 1, "seed_smishing"),
    ("WhatsApp security code: 492-183. If you did not request this code, send VERIFY to 88022 to prevent account takeover.", 1, "seed_smishing"),
    ("PayPal alert: We noticed suspicious transfers on your card. Log in to restore access: http://paypal-resolution-center.example/auth", 1, "seed_smishing"),
    ("URGENT: Your healthcare insurance policy is pending cancellation. Verify social security number and policy ID now: http://healthcare-renew.example", 1, "seed_smishing"),
    
    # Legitimate / Ham examples (Label 0)
    ("Hey mom, running a few minutes late from the office. Should I pick up bread or milk on my way home?", 0, "seed_ham"),
    ("Hi Alex, thanks for sending over the project slides. I reviewed section 3 and made a few minor comments in the shared doc.", 0, "seed_ham"),
    ("Reminder: Your dental appointment with Dr. Chen is scheduled for tomorrow at 2:00 PM. Reply 1 to confirm or call 555-0192 to reschedule.", 0, "seed_ham"),
    ("Your Uber ride is arriving now. Gray Toyota Camry with license plate 7XYZ89.", 0, "seed_ham"),
    ("Hey are we still on for squash this Thursday at 6pm? Let me know so I can reserve the court.", 0, "seed_ham"),
    ("Flash weekend sale: 20% off all winter apparel at OutdoorGear with code COZY20. Visit us in-store or online. Unsubscribe reply STOP.", 0, "seed_ham"),
    ("Your package has been delivered to your front porch. Signed by resident.", 0, "seed_ham"),
    ("Can you please send me Grandma's apple pie recipe when you get a chance? Hope you have a wonderful weekend!", 0, "seed_ham"),
    ("Meeting notes from today's sprint planning have been published to the engineering wiki. Please review action items before tomorrow.", 0, "seed_ham"),
    ("Dinner was amazing tonight! Thank you so much for hosting us. Let's do it again soon.", 0, "seed_ham"),
]

# -----------------------------------------------------------------------------
# Data Ingestion & Sanitization
# -----------------------------------------------------------------------------
def discover_and_load_datasets() -> pd.DataFrame:
    """Discovers and parses all compatible datasets across known search locations."""
    print("=" * 70)
    print("PHISHSHIFT ML TRAINING PIPELINE — DATASET DISCOVERY")
    print("=" * 70)

    found_frames: List[pd.DataFrame] = []
    scanned_files = set()

    for base_path in SEARCH_PATHS:
        if not base_path.exists():
            continue

        # Look for CSV files in current and nested directories
        for root, _, files in os.walk(base_path):
            for file_name in files:
                if not file_name.lower().endswith(".csv"):
                    continue

                full_path = Path(root) / file_name
                resolved = full_path.resolve()
                if resolved in scanned_files:
                    continue
                scanned_files.add(resolved)

                # Skip Spambase statistical table archive (crl.tot, dollar, bang, etc.)
                # Documented incompatibility: Spambase contains pre-calculated numerical features,
                # not raw natural language text messages required for NLP TF-IDF vectorization.
                if file_name.lower() == "spam.csv":
                    print(f"[-] Inspecting {full_path}:")
                    print("    -> Note: Skipped archive_3/spam.csv (Spambase numerical statistical features, not raw text).")
                    continue

                try:
                    # Attempt reading with various encodings
                    df_raw = None
                    for enc in ["utf-8", "latin-1", "cp1252"]:
                        try:
                            df_raw = pd.read_csv(full_path, encoding=enc)
                            break
                        except Exception:
                            continue

                    if df_raw is None or df_raw.empty:
                        continue

                    # Find matching adapter
                    adapted_df = None
                    for adapter in ADAPTERS:
                        if adapter.can_adapt(df_raw, full_path):
                            print(f"[+] Found {adapter.name} at: {full_path}")
                            adapted_df = adapter.adapt(df_raw, full_path)
                            break

                    if adapted_df is not None and not adapted_df.empty:
                        print(f"    -> Parsed {len(adapted_df)} records (Spam/Phishing: {sum(adapted_df['label'] == 1)}, Ham: {sum(adapted_df['label'] == 0)})")
                        found_frames.append(adapted_df)

                except Exception as ex:
                    print(f"[!] Warning: Could not process {full_path}: {ex}")

    # Append seed messages to strengthen smishing/phishing signals
    seed_df = pd.DataFrame(SEED_MESSAGES, columns=["text", "label", "source"])
    found_frames.append(seed_df)
    print(f"[+] Appended {len(seed_df)} curated smishing & legitimate baseline seed samples.")

    if not found_frames:
        raise RuntimeError("No compatible datasets found! Please ensure datasets are in ./dataset or ../dataset.")

    combined = pd.concat(found_frames, ignore_index=True)
    initial_count = len(combined)

    # Clean missing / invalid records
    combined["text"] = combined["text"].astype(str).str.strip()
    combined = combined[combined["text"].str.len() >= 3]  # Minimum text length
    combined["label"] = combined["label"].astype(int)

    # Deduplicate based on normalized text to prevent data leakage and memorization
    combined["norm_key"] = combined["text"].str.lower().str.replace(r"\s+", " ", regex=True)
    deduped = combined.drop_duplicates(subset=["norm_key"]).drop(columns=["norm_key"]).reset_index(drop=True)
    deduped_count = len(deduped)

    print(f"\n[+] Total records loaded: {initial_count}")
    print(f"[+] Unique records after deduplication: {deduped_count}")
    print(f"[+] Class distribution: Legitimate (0) = {sum(deduped['label'] == 0)}, Malicious/Phishing (1) = {sum(deduped['label'] == 1)}")
    print(f"[+] Malicious class ratio: {deduped['label'].mean():.4f}")

    return deduped

# -----------------------------------------------------------------------------
# Model Training & Evaluation
# -----------------------------------------------------------------------------
def train_and_evaluate(df: pd.DataFrame) -> Tuple[TfidfVectorizer, MLPClassifier, Dict[str, Any]]:
    """
    Executes reproducible train/test split, fits TF-IDF and MLPClassifier,
    and computes precision, recall, F1, and confusion matrix.
    """
    print("\n" + "=" * 70)
    print("MODEL TRAINING & EVALUATION (TF-IDF + MLPClassifier)")
    print("=" * 70)

    # Stratified Train/Test Split (80% train, 20% test)
    # Convert explicitly to numpy arrays to ensure compatibility with PyArrow/pandas 3.0+
    X = np.array(df["text"].tolist(), dtype=object)
    y = np.array(df["label"].tolist(), dtype=int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y
    )

    print(f"Training split: {len(X_train)} samples | Testing split: {len(X_test)} samples")

    # Fit TF-IDF Vectorizer ONLY on the training split to prevent data leakage
    print(f"\nFitting TfidfVectorizer (max_features={MAX_FEATURES}, lowercase=True, norm='l2')...")
    t0 = time.time()
    vectorizer = TfidfVectorizer(
        max_features=MAX_FEATURES,
        lowercase=True,
        token_pattern=r"(?u)\b\w\w+\b",
        norm="l2",
        use_idf=True,
        smooth_idf=True,
        sublinear_tf=False
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    print(f"TF-IDF fitted in {time.time() - t0:.2f}s. Vocabulary size: {len(vectorizer.vocabulary_)}")

    # Train MLPClassifier
    print(f"\nTraining MLPClassifier (hidden_layer_sizes=({HIDDEN_LAYER_SIZE},), activation='relu', solver='adam')...")
    t0 = time.time()
    mlp = MLPClassifier(
        hidden_layer_sizes=(HIDDEN_LAYER_SIZE,),
        activation="relu",
        solver="adam",
        max_iter=MAX_ITER,
        early_stopping=True,
        random_state=RANDOM_STATE
    )
    mlp.fit(X_train_vec, y_train)
    train_time = time.time() - t0
    print(f"MLP trained in {train_time:.2f}s. Iterations: {mlp.n_iter_}")

    # Evaluate on held-out test split
    y_pred_proba = mlp.predict_proba(X_test_vec)[:, 1]
    y_pred = (y_pred_proba >= DECISION_THRESHOLD).astype(int)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)

    print("\n" + "-" * 50)
    print("HELD-OUT EVALUATION METRICS:")
    print("-" * 50)
    print(f"  Accuracy:         {acc * 100:.2f}%")
    print(f"  Precision:        {prec * 100:.2f}%")
    print(f"  Recall:           {rec * 100:.2f}%")
    print(f"  F1-Score:         {f1 * 100:.2f}%")
    print(f"  Confusion Matrix: TN={cm[0, 0]}, FP={cm[0, 1]}, FN={cm[1, 0]}, TP={cm[1, 1]}")
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Legitimate", "Malicious/Phishing"], digits=4))

    metadata = {
        "model_version": MODEL_VERSION,
        "trained_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "random_state": RANDOM_STATE,
        "total_dataset_size": len(df),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "metrics": {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "confusion_matrix": {
                "true_negative": int(cm[0, 0]),
                "false_positive": int(cm[0, 1]),
                "false_negative": int(cm[1, 0]),
                "true_positive": int(cm[1, 1]),
            }
        },
        "training_time_seconds": round(train_time, 2)
    }

    return vectorizer, mlp, metadata

# -----------------------------------------------------------------------------
# Model Serialization
# -----------------------------------------------------------------------------
def export_model_json(vectorizer: TfidfVectorizer, mlp: MLPClassifier, metadata: Dict[str, Any], output_path: str = EXPORT_JSON_PATH):
    """
    Exports a clean, deterministic, versioned JSON object containing:
      - vocabulary and token indices
      - IDF weights
      - First-layer weights (W1) and biases (b1)
      - Second-layer weights (W2) and biases (b2)
      - Activation functions & decision threshold
      - Metadata and metrics
    """
    print("\n" + "=" * 70)
    print(f"EXPORTING LOCAL INFERENCE MODEL TO {output_path}")
    print("=" * 70)

    # Sort vocabulary by token index (0 to N-1)
    vocab_items = sorted(vectorizer.vocabulary_.items(), key=lambda item: item[1])
    vocabulary_map = {word: int(idx) for word, idx in vocab_items}

    # Extract weights and biases (round to 4 decimal places for size optimization)
    # W1: (vocab_size, hidden_layer_size)
    W1 = mlp.coefs_[0].round(4).tolist()
    # b1: (hidden_layer_size,)
    b1 = mlp.intercepts_[0].round(4).tolist()
    # W2: (hidden_layer_size, 1) -> flatten to list of 100 floats
    W2 = mlp.coefs_[1].flatten().round(4).tolist()
    # b2: (1,) -> scalar float
    b2 = round(float(mlp.intercepts_[1][0]), 4)
    # idf: (vocab_size,)
    idf = vectorizer.idf_.round(4).tolist()

    export_data = {
        "format": "phishshift-neural-v1",
        "version": metadata["model_version"],
        "metadata": metadata,
        "preprocessing": {
            "lowercase": True,
            "token_pattern": r"\b[a-z0-9_]{2,}\b",
            "norm": "l2",
            "vocab_size": len(vocabulary_map),
        },
        "architecture": {
            "type": "MLPClassifier",
            "input_dim": len(vocabulary_map),
            "hidden_dim": len(b1),
            "hidden_activation": "relu",
            "output_activation": "logistic",
            "decision_threshold": DECISION_THRESHOLD,
        },
        "vocabulary": vocabulary_map,
        "idf": idf,
        "weights": {
            "W1": W1,
            "b1": b1,
            "W2": W2,
            "b2": b2,
        }
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, separators=(",", ":"))

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"[OK] Model exported successfully to {output_path} ({size_mb:.2f} MB)")
    return export_data

# -----------------------------------------------------------------------------
# Verification on Fixed Test Cases
# -----------------------------------------------------------------------------
def verify_test_cases(vectorizer: TfidfVectorizer, mlp: MLPClassifier):
    """Runs fixed benchmark messages through Python model to verify expected risk levels."""
    print("\n" + "=" * 70)
    print("VERIFICATION ON FIXED TEST CASES")
    print("=" * 70)

    test_cases = [
        ("ALERT: FirstMetro checking account locked. Verify identity at https://secure-bank.example/auth", "Expected: Suspicious / Phishing"),
        ("Hey Alex, dinner is confirmed for 7:30 PM tonight at the bistro on 4th Street.", "Expected: Likely Legitimate"),
        ("Flash sale: 30% off all apparel this weekend only. Use code SPRING30 at checkout. Reply STOP to opt out.", "Expected: Promotional / Low Risk"),
    ]

    for msg, expected in test_cases:
        vec = vectorizer.transform([msg])
        prob = float(mlp.predict_proba(vec)[0, 1])
        pred = "Potential Phishing" if prob >= 0.70 else ("Suspicious" if prob >= 0.40 else "Likely Legitimate")
        print(f"Message:  \"{msg[:65]}...\"")
        print(f"  Result:   {pred} (Risk score: {prob * 100:.1f}%) | {expected}\n")

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    df = discover_and_load_datasets()
    vectorizer, mlp, metadata = train_and_evaluate(df)
    export_model_json(vectorizer, mlp, metadata, EXPORT_JSON_PATH)
    verify_test_cases(vectorizer, mlp)
