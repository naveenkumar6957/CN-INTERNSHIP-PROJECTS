# =====================================================
# Train the best model on all 3 datasets + save for website
# Creates: model_full.pkl, model_early.pkl, meta_full.json, meta_early.json
# =====================================================
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ml_dir = os.path.join(BASE_DIR, "ml")
sys.path.insert(0, ml_dir)

from train_model import run, EXAM_RESULT_COLS

if __name__ == "__main__":
    print("Training ML Models for Kalvikkan...")
    run("full", [])
    run("early", EXAM_RESULT_COLS)
    print("Training complete!")
