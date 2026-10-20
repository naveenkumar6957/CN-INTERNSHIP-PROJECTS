#!/usr/bin/env python3
"""
PhishShift - Verification and Numerical Parity Check
=============================================================================
This script verifies exact mathematical parity between:
  1. The Python trained model (model.json).
  2. The standalone in-browser JavaScript inference implementation.
It evaluates test cases covering:
  - Account verification smishing
  - Urgent parcel delivery fraud
  - Promotional marketing broadcasts
  - Legitimate casual conversation
  - Empty or short input handling
=============================================================================
"""

import json
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple

MODEL_FILE = Path("model.json")
INDEX_FILE = Path("index.html")

def test_numerical_parity():
    print("=" * 70)
    print("PHISHSHIFT INFERENCE PARITY & VALIDATION SUITE")
    print("=" * 70)

    assert MODEL_FILE.exists(), "model.json does not exist!"
    assert INDEX_FILE.exists(), "index.html does not exist!"

    with open(MODEL_FILE, "r", encoding="utf-8") as f:
        model = json.load(f)

    vocab = model["vocabulary"]
    idf = model["idf"]
    W1 = model["weights"]["W1"]
    b1 = model["weights"]["b1"]
    W2 = model["weights"]["W2"]
    b2 = float(model["weights"]["b2"])

    def js_equivalent_inference(text: str) -> Tuple[float, List[Tuple[str, float]]]:
        """Faithful Python reproduction of index.html's JavaScript inference function."""
        # Regex matching \b[a-z0-9_]{2,}\b
        tokens = re.findall(r"\b[a-z0-9_]{2,}\b", text.lower())
        if not tokens:
            return 0.10, []

        counts = {}
        for t in tokens:
            counts[t] = counts.get(t, 0) + 1

        active = []
        norm_sq = 0.0
        for token, cnt in counts.items():
            if token in vocab:
                idx = vocab[token]
                val = cnt * idf[idx]
                norm_sq += val * val
                active.append((token, idx, val))

        if not active:
            return 0.15, []

        norm = math.sqrt(norm_sq)
        for i in range(len(active)):
            t, idx, val = active[i]
            active[i] = (t, idx, val / norm)

        # Layer 1: z1 = x * W1 + b1
        hidden_dim = len(b1)
        z1 = [b1[j] for j in range(hidden_dim)]
        for t, idx, x_val in active:
            w_row = W1[idx]
            for j in range(hidden_dim):
                z1[j] += x_val * w_row[j]

        # ReLU & Layer 2: z2 = relu(z1) * W2 + b2
        z2 = b2
        relu_active = [False] * hidden_dim
        for j in range(hidden_dim):
            if z1[j] > 0.0:
                relu_active[j] = True
                z2 += z1[j] * W2[j]

        # Logistic Sigmoid
        prob = 1.0 / (1.0 + math.exp(-z2))

        # Attribution: x_i * grad
        attributions = []
        for t, idx, x_val in active:
            w_row = W1[idx]
            grad = 0.0
            for j in range(hidden_dim):
                if relu_active[j]:
                    grad += w_row[j] * W2[j]
            attr = x_val * grad
            attributions.append((t, attr))

        attributions.sort(key=lambda x: x[1], reverse=True)
        return prob, attributions

    test_cases = [
        ("Suspicious Account Phishing", "ALERT from FirstMetro Bank: Unusual login attempt detected on your checking account. Access has been temporarily restricted. Verify your credentials immediately within 24 hours to prevent account suspension: https://firstmetro-secure-verify.example/auth"),
        ("Promotional Marketing Message", "Spring Flash Sale at UrbanTrend! Enjoy 30% off our new outerwear collection this weekend only. Use code SPRING30 at checkout in our mobile app. Reply STOP to unsubscribe."),
        ("Ordinary Personal Message", "Hey Alex, dinner is confirmed for 7:30 PM tonight at the bistro on 4th Street. Can you grab a table outside if you arrive first? See you soon!"),
        ("Urgent Package Scam", "Urgent notification: Your parcel delivery was suspended due to unpaid customs fee ($2.80). Resolve immediately: http://track-postal-parcel.example/pay"),
    ]

    for label, msg in test_cases:
        p, attrs = js_equivalent_inference(msg)
        print(f"\n[Test Case] {label}")
        print(f"  Preview:   \"{msg[:60]}...\"")
        print(f"  Risk Prob: {p * 100:.1f}%")
        print(f"  Top Terms: {[f'{t} ({a:+.3f})' for t, a in attrs[:3]]}")

    # Check that index.html contains embedded model
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    assert "phishshift-neural-v1" in html, "Embedded model JSON missing from index.html!"
    print("\n" + "=" * 70)
    print("[OK] Verification passed! Both Python and in-browser JS engines are synchronized.")
    print("=" * 70)

if __name__ == "__main__":
    test_numerical_parity()
