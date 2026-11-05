# =====================================================
# Train the best model on all 3 datasets + save for website
# Creates: model_full.pkl, model_early.pkl, meta_full.json, meta_early.json
# =====================================================
import os
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def find_file(filename):
    candidates = [
        os.path.join(BASE_DIR, filename),
        os.path.join(BASE_DIR, "data", filename),
        os.path.join(BASE_DIR, "ml", "data", filename),
        os.path.join(os.path.dirname(BASE_DIR), "ml", "data", filename),
        os.path.expanduser(os.path.join("~", "Downloads", filename)),
        f"/content/{filename}",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    raise FileNotFoundError(f"Cannot find dataset file: {filename}")

PATHS = [
    find_file("engineering_student_performance.csv"),
    find_file("engineering_student_performance_large.csv"),
    find_file("engineering_student_performance_new.csv"),
]
print("Loaded datasets from:", PATHS)

TARGET = "performance_category"
ID_COLS = ["student_id"]
# Columns that are exam RESULTS - usually NOT known when you want to predict
EXAM_RESULT_COLS = ["final_exam_score", "midterm_score"]

# ---------- load + combine ----------
df = pd.concat([pd.read_csv(p) for p in PATHS], ignore_index=True)
df.columns = [c.strip() for c in df.columns]
df = df.drop_duplicates().dropna(subset=[TARGET]).reset_index(drop=True)
print("Total rows:", len(df))
print(df[TARGET].value_counts(), "\n")


def make_preprocess(X):
    num = X.select_dtypes(include=np.number).columns.tolist()
    cat = [c for c in X.columns if c not in num]
    return ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler())]), num),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                          ("oh", OneHotEncoder(handle_unknown="ignore",
                                               sparse_output=False))]), cat),
    ])


def candidates():
    return {
        "LogisticRegression": LogisticRegression(max_iter=3000, class_weight="balanced"),
        "RandomForest": RandomForestClassifier(n_estimators=400, class_weight="balanced",
                                               random_state=42, n_jobs=-1),
        "HistGradientBoosting": HistGradientBoostingClassifier(random_state=42),
    }


def run(mode, drop_cols):
    print("=" * 60)
    print(f"MODE: {mode}   (dropped: {drop_cols})")
    print("=" * 60)
    X = df.drop(columns=[TARGET] + ID_COLS + drop_cols)
    y = df[TARGET]

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    best_name, best_score = None, -1
    for name, clf in candidates().items():
        pipe = Pipeline([("prep", make_preprocess(X)), ("model", clf)])
        score = cross_val_score(pipe, X_tr, y_tr, cv=cv, scoring="f1_macro", n_jobs=-1).mean()
        print(f"  {name:22s} CV macro-F1 = {score:.4f}")
        if score > best_score:
            best_name, best_score = name, score
    print(f"\n  Best model: {best_name}")

    # evaluate on untouched test set
    pipe = Pipeline([("prep", make_preprocess(X)), ("model", candidates()[best_name])])
    pipe.fit(X_tr, y_tr)
    pred = pipe.predict(X_te)
    test_acc = accuracy_score(y_te, pred)
    test_f1 = f1_score(y_te, pred, average='macro')
    print(f"  Test accuracy : {test_acc:.4f}")
    print(f"  Test macro-F1 : {test_f1:.4f}")
    print(classification_report(y_te, pred))

    # final model: retrain on ALL data, then save
    pipe.fit(X, y)
    
    out_dir = BASE_DIR
    model_path = os.path.join(out_dir, f"model_{mode}.pkl")
    meta_path = os.path.join(out_dir, f"meta_{mode}.json")
    joblib.dump(pipe, model_path, compress=3)

    meta = {
        "mode": mode,
        "model": best_name,
        "target": TARGET,
        "classes": [str(c) for c in pipe.classes_],
        "features": list(X.columns),
        "numeric": {c: [float(X[c].min()), float(X[c].max())]
                    for c in X.select_dtypes(include=np.number).columns},
        "categorical": {c: sorted(X[c].dropna().unique().tolist())
                        for c in X.select_dtypes(exclude=np.number).columns},
        "test_accuracy": round(float(test_acc), 4),
        "test_f1": round(float(test_f1), 4),
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  Saved {model_path} and {meta_path}\n")

if __name__ == "__main__":
    run("full", [])                    # uses everything (includes exam scores)
    run("early", EXAM_RESULT_COLS)     # realistic: predicts before exam results exist
