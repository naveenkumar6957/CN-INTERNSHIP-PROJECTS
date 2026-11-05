# =====================================================
# Simple prediction API for your website (Flask)
#
# Setup:
#   pip install flask flask-cors scikit-learn pandas joblib
# Put model_early.pkl, meta_early.json (and/or the _full files) next to this file.
# Run:  python app.py
# =====================================================
import os
import json
import joblib
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def find_file(filename):
    candidates = [
        os.path.join(BASE_DIR, filename),
        os.path.join(BASE_DIR, "ml", filename),
        os.path.join(os.path.dirname(BASE_DIR), "ml", filename),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return os.path.join(BASE_DIR, filename)

MODE = os.environ.get("ML_MODE", "early")   # "early" = no exam-result columns (recommended), "full" = all columns

model_path = find_file(f"model_{MODE}.pkl")
meta_path = find_file(f"meta_{MODE}.json")

model = None
meta = {}

if os.path.exists(model_path) and os.path.exists(meta_path):
    model = joblib.load(model_path)
    with open(meta_path) as f:
        meta = json.load(f)
    print(f"Loaded {MODE} model successfully from {model_path}")
else:
    print(f"Warning: Model file {model_path} or {meta_path} not found.")

app = Flask(__name__)
CORS(app)  # lets your website's JavaScript call this API


@app.get("/")
def home():
    return jsonify({
        "status": "ok" if model is not None else "model_missing",
        "service": "Kalvikkan AI Machine Learning Prediction Engine",
        "mode": MODE,
        "model": meta.get("model", "None"),
        "test_accuracy": meta.get("test_accuracy", None),
        "test_f1": meta.get("test_f1", None),
        "classes": meta.get("classes", []),
    })


@app.get("/schema")
def schema():
    # your website can use this to build the input form (fields, ranges, dropdown options)
    return jsonify(meta)


@app.post("/predict")
def predict():
    if model is None:
        return jsonify({"error": "Model is not loaded."}), 503

    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    mapped_data = dict(data)
    # Map common alternative field names from frontend if needed
    if "attendance" in mapped_data and "attendance_percentage" not in mapped_data:
        mapped_data["attendance_percentage"] = mapped_data["attendance"]
    if "previousScore" in mapped_data and "previous_semester_percentage" not in mapped_data:
        mapped_data["previous_semester_percentage"] = mapped_data["previousScore"]
    if "assessmentScore" in mapped_data and "internal_exam_1" not in mapped_data:
        mapped_data["internal_exam_1"] = mapped_data["assessmentScore"]
    if "quizScore" in mapped_data and "internal_exam_2" not in mapped_data:
        mapped_data["internal_exam_2"] = mapped_data["quizScore"]

    features = meta.get("features", [])
    row_dict = {}
    for feat in features:
        if feat in mapped_data and mapped_data[feat] is not None:
            row_dict[feat] = mapped_data[feat]
        elif feat in meta.get("numeric", {}):
            min_v, max_v = meta["numeric"][feat]
            row_dict[feat] = (min_v + max_v) / 2.0
        elif feat in meta.get("categorical", {}):
            row_dict[feat] = meta["categorical"][feat][0] if meta["categorical"][feat] else "CSE"
        else:
            row_dict[feat] = None

    # keep only the expected columns, in the right order; missing ones become median (auto-filled)
    row = pd.DataFrame([row_dict]).reindex(columns=features)
    proba = model.predict_proba(row)[0]
    pred = model.classes_[proba.argmax()]

    return jsonify({
        "prediction": str(pred),
        "riskLevel": "HIGH" if str(pred).lower() == "low" else "MEDIUM" if str(pred).lower() == "average" else "LOW",
        "confidence": round(float(proba.max()), 4),
        "probabilities": {str(c): round(float(p), 4) for c, p in zip(model.classes_, proba)},
        "modelUsed": meta.get("model", "RandomForest"),
        "mode": MODE,
        "featuresCount": len(features),
    })


@app.post("/batch-predict")
def batch_predict():
    if model is None:
        return jsonify({"error": "Model is not loaded."}), 503

    items = request.get_json(force=True)
    if not isinstance(items, list):
        items = [items]

    features = meta.get("features", [])
    rows = []
    for item in items:
        mapped = dict(item)
        if "attendance" in mapped and "attendance_percentage" not in mapped:
            mapped["attendance_percentage"] = mapped["attendance"]
        if "previousScore" in mapped and "previous_semester_percentage" not in mapped:
            mapped["previous_semester_percentage"] = mapped["previousScore"]
        if "assessmentScore" in mapped and "internal_exam_1" not in mapped:
            mapped["internal_exam_1"] = mapped["assessmentScore"]
        if "quizScore" in mapped and "internal_exam_2" not in mapped:
            mapped["internal_exam_2"] = mapped["quizScore"]

        row_dict = {}
        for feat in features:
            if feat in mapped and mapped[feat] is not None:
                row_dict[feat] = mapped[feat]
            elif feat in meta.get("numeric", {}):
                min_v, max_v = meta["numeric"][feat]
                row_dict[feat] = (min_v + max_v) / 2.0
            elif feat in meta.get("categorical", {}):
                row_dict[feat] = meta["categorical"][feat][0] if meta["categorical"][feat] else "CSE"
            else:
                row_dict[feat] = None
        rows.append(row_dict)

    df_batch = pd.DataFrame(rows).reindex(columns=features)
    probas = model.predict_proba(df_batch)

    results = []
    for i, proba in enumerate(probas):
        pred = model.classes_[proba.argmax()]
        results.append({
            "prediction": str(pred),
            "riskLevel": "HIGH" if str(pred).lower() == "low" else "MEDIUM" if str(pred).lower() == "average" else "LOW",
            "confidence": round(float(proba.max()), 4),
            "probabilities": {str(c): round(float(p), 4) for c, p in zip(model.classes_, proba)},
        })

    return jsonify({"count": len(results), "results": results})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Kalvikkan ML API running on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
