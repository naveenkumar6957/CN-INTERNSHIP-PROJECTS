#!/usr/bin/env python3
"""
PhishShift - Static Deployment Build Script
=============================================================================
This script converts the development template (template.html) and trained
neural network weights (model.json) into a single, completely standalone,
zero-dependency production artifact: index.html.

The resulting index.html:
  1. Contains all HTML structure, responsive CSS styles, and inline SVGs.
  2. Embeds the full trained model parameters inside an application/json script block.
  3. Executes locally in the browser without network requests, APIs, or servers.
  4. Runs directly via file:// protocol or deployed as a static site on Vercel.
=============================================================================
"""

import os
import sys
import json
from pathlib import Path

MODEL_PATH = Path("model.json")
TEMPLATE_PATH = Path("template.html")
OUTPUT_PATH = Path("index.html")

def build_standalone_html():
    print("=" * 70)
    print("PHISHSHIFT — STANDALONE HTML PRODUCTION BUILD")
    print("=" * 70)

    if not MODEL_PATH.exists():
        print(f"[!] Error: Model file '{MODEL_PATH}' not found!")
        print("    Please run 'python train_model.py' first to train and export the model.")
        sys.exit(1)

    if not TEMPLATE_PATH.exists():
        print(f"[!] Error: Template file '{TEMPLATE_PATH}' not found!")
        sys.exit(1)

    print(f"[+] Loading model from: {MODEL_PATH.resolve()}")
    with open(MODEL_PATH, "r", encoding="utf-8") as f:
        model_json_str = f.read()

    # Validate JSON syntax
    try:
        model_obj = json.loads(model_json_str)
        vocab_size = len(model_obj.get("vocabulary", {}))
        hidden_dim = len(model_obj.get("weights", {}).get("b1", []))
        metrics = model_obj.get("metadata", {}).get("metrics", {})
        acc = metrics.get("accuracy", "N/A")
        print(f"    -> Validated model v{model_obj.get('version', '1.0.0')} | Vocab: {vocab_size} | Hidden: {hidden_dim} | Test Acc: {acc}")
    except Exception as e:
        print(f"[!] Error: model.json is invalid JSON: {e}")
        sys.exit(1)

    print(f"[+] Reading HTML template from: {TEMPLATE_PATH.resolve()}")
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    placeholder = "/* PHISHSHIFT_MODEL_JSON_PLACEHOLDER */"
    if placeholder not in html_content:
        print(f"[!] Error: Placeholder '{placeholder}' not found in {TEMPLATE_PATH}!")
        sys.exit(1)

    print("[+] Embedding model JSON into production HTML...")
    # Inject minified JSON directly into script tag
    standalone_html = html_content.replace(placeholder, model_json_str)

    print(f"[+] Writing production standalone artifact to: {OUTPUT_PATH.resolve()}")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(standalone_html)

    size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    print("\n" + "-" * 70)
    print(f"[OK] Build complete! Standalone file generated: {OUTPUT_PATH} ({size_mb:.2f} MB)")
    print("     - Opens directly in any browser (file://)")
    print("     - Ready for instant static deployment on Vercel")
    print("-" * 70)

if __name__ == "__main__":
    build_standalone_html()
