# PhishShift — Message Risk Scanner

> **"Pause. Inspect. Stay protected."**  
> An educational, privacy-first cybersecurity prototype for analyzing suspicious SMS, WhatsApp, and text messages using local in-browser machine learning.

---

## 1. Executive Product Overview

**PhishShift** is an educational, production-quality prototype designed to empower everyday users to inspect suspicious communications without risking their security or compromising their privacy.

### Key Capabilities
- **Real-Time Message Risk Assessment:** Categorizes messages into *Potential Phishing*, *Suspicious Message*, or *Likely Legitimate*.
- **Calibrated Risk Gauge:** Displays an honest probability estimate computed directly by an in-browser neural network.
- **Explainable Model Attribution:** Calculates mathematically rigorous local gradient attribution ($\text{Input} \times \text{Gradient}$) for every token, highlighting the top 3 words that influenced the classification.
- **Pattern-Based Threat Cues:** Detects subtle urgency, suspension threats, OTP/credential harvesting requests, unusual financial demands, and deceptive URL patterns.
- **Actionable Guidance:** Provides clear, tailored next steps based on the risk level.
- **100% Privacy by Design:** All machine learning inference and heuristic evaluations run strictly within local browser memory. **No text is ever transmitted to an external server or API.**
- **Zero URL Execution:** Extracted links are treated strictly as inert text strings and are never fetched, pinged, or navigated.

---

## 2. Architecture & Technical Constraints

```
PhishShift/
├── train_model.py         # Multi-dataset ingestion, sanitization, TF-IDF + MLP training & JSON export
├── build.py               # Deterministic build script embedding model.json into template.html
├── template.html          # Development HTML/CSS/JS template with placeholder for model weights
├── index.html             # Standalone production artifact (contains embedded model JSON)
├── model.json             # Serialized trained model weights, biases, IDF, and metadata
├── vercel.json            # Vercel static deployment & single-page application route rewrite
├── requirements.txt       # Python dependencies with compatible version bounds
├── verify_parity.py       # Python test suite verifying mathematical parity with scikit-learn
├── test_node_inference.js # V8 JavaScript runtime verification script
└── README.md              # Complete project documentation and operation manual
```

### Technical Specifications
- **Frontend Stack:** Vanilla HTML5, modern CSS3 (Custom Properties, Flexbox, CSS Grid, Fluid Typography), and Vanilla ES2020 JavaScript.
- **Zero Framework Overhead:** No React, Vue, Angular, Node.js backend, database, or external analytics scripts.
- **Self-Contained Deployment:** The production artifact `index.html` embeds the trained neural network parameters directly in an `<script type="application/json">` block. It runs standalone via the `file://` protocol or when hosted statically on Vercel.

---

## 3. Machine-Learning Pipeline

### Architecture
- **Text Normalization:** Lowercased token extraction adhering strictly to scikit-learn's token pattern: `r"(?u)\b\w\w+\b"`.
- **Feature Extraction:** `TfidfVectorizer(max_features=5000, lowercase=True, norm='l2', use_idf=True, smooth_idf=True)`.
- **Classification Model:** `MLPClassifier(hidden_layer_sizes=(100,), activation='relu', solver='adam', max_iter=60, early_stopping=True)`.
- **Activation Functions:**
  - Hidden Layer: Rectified Linear Unit ($\text{ReLU}(z) = \max(0, z)$).
  - Output Layer: Logistic Sigmoid ($\sigma(z) = \frac{1}{1 + e^{-z}}$).

### Data Ingestion & Leakage Prevention
`train_model.py` incorporates an extensible adapter pattern:
- **`SmsMailDataAdapter`:** Ingests the UCI SMS Spam Collection (`mail_data.csv`).
- **`EmailSpamDatasetAdapter`:** Ingests Enron/SpamAssassin records (`emails.csv`), stripping email header artifacts (`Subject: ...`) to focus on semantic content.
- **Incompatible Dataset Handling:** Explicitly inspects `spam.csv` (Archive 3) and documents that tabular continuous statistical metrics (e.g., `crl.tot`, `dollar`, `bang`) cannot be vectorized by text NLP pipelines and are safely excluded.
- **Leakage Prevention:** Dataset is deduplicated before splitting. A stratified 80/20 train/test split is applied. The TF-IDF vectorizer is fitted **strictly on the training split**, ensuring held-out test data remains unobserved during feature selection.

### Held-Out Evaluation Metrics
Evaluated on **2,142 held-out test samples**:

| Metric | Result |
| :--- | :--- |
| **Accuracy** | **97.71%** |
| **Precision** | **95.63%** |
| **Recall** | **92.08%** |
| **F1-Score** | **93.82%** |
| **True Negatives (TN)** | 1,721 |
| **False Positives (FP)** | 17 |
| **False Negatives (FN)** | 32 |
| **True Positives (TP)** | 372 |

---

## 4. Explainable AI & In-Browser Inference

### Exact Mathematical Forward Pass
In `index.html`, incoming message text is converted into a sparse TF-IDF vector $x$ matching scikit-learn:
$$z_{1, j} = \sum_{i \in \text{sparse}} x_i W_{1, i, j} + b_{1, j}$$
$$a_{1, j} = \max(0, z_{1, j})$$
$$z_2 = \sum_{j=0}^{99} a_{1, j} W_{2, j} + b_2$$
$$P(\text{Malicious}) = \frac{1}{1 + e^{-z_2}}$$

Because SMS messages typically contain only 5 to 40 tokens, the sparse dot product requires fewer than 4,000 floating-point operations, executing in under **0.05 milliseconds** in browser JavaScript.

### Explainability: Local Gradient Attribution (Input × Gradient)
To provide transparent feature attribution without fabricating scores, the browser calculates the gradient of the output logit $z_2$ with respect to each active input token $x_i$:
$$\frac{\partial z_2}{\partial x_i} = \sum_{j: z_{1, j} > 0} W_{1, i, j} \cdot W_{2, j}$$
$$\text{Attribution}_i = x_i \cdot \frac{\partial z_2}{\partial x_i}$$

- $\text{Attribution}_i > 0$: The word actively pushed the neural network toward a phishing classification.
- $\text{Attribution}_i < 0$: The word pushed the decision toward a legitimate classification.

---

## 5. Threat Cues & Heuristic Detection

In addition to the neural network, PhishShift evaluates seven pattern-based threat cues using defensive regex matching:
1. **Urgency & Pressure:** Matches synthetic urgency (e.g., *"immediately"*, *"within 24 hours"*, *"act now"*).
2. **Account Verification:** Identifies credential verification requests (e.g., *"verify your account"*, *"confirm identity"*).
3. **Suspension Threats:** Detects coercion (e.g., *"service interruption"*, *"account locked"*, *"terminated"*).
4. **Credential & OTP Harvesting:** Flags requests for authentication tokens (e.g., *"OTP"*, *"passcode"*, *"security code"*).
5. **Unusual Payment Demands:** Flags high-risk payment mechanisms (e.g., *"wire transfer"*, *"crypto"*, *"gift card"*, *"overdue invoice"*).
6. **Sensitive Info Requests:** Flags high-value data requests (e.g., *"social security"*, *"CVV"*, *"bank account number"*).
7. **Suspicious Link Patterns:** Analyzes inert link strings for suspicious TLDs, URL shorteners (`bit.ly`, `tinyurl`), raw IP addresses, and misleading hyphenated bank domains (`bank-verify.example`).

---

## 6. Local Setup & Usage

### 1. Prerequisites
- Python 3.9+ (Python 3.10+ recommended)
- Node.js 18+ (optional, for running JS test suites)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Retrain the Model (Optional)
To retrain the neural network on local datasets:
```bash
python train_model.py
```
This produces `model.json` with updated weights, biases, IDF values, and evaluation metrics.

### 4. Build the Standalone HTML
Embed `model.json` into `index.html`:
```bash
python build.py
```

### 5. Run Verification Suites
Verify that Python and JavaScript mathematical inference remain synchronized:
```bash
python verify_parity.py
node test_node_inference.js
```

### 6. Run the Application Locally
Open `index.html` directly in any web browser, or launch a lightweight local server:
```bash
python -m http.server 8080
```
Then visit: `http://localhost:8080`

---

## 7. Vercel Static Deployment

PhishShift is configured for static single-page application hosting on Vercel.

### Vercel Configuration (`vercel.json`)
```json
{
  "version": 2,
  "cleanUrls": true,
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

### Deploy via Vercel CLI
```bash
npm i -g vercel
vercel --prod
```

### Deploy via GitHub / GitLab / Bitbucket
1. Push this directory to your Git repository.
2. Import the project in your Vercel Dashboard.
3. Framework Preset: **Other**.
4. Root Directory: `./` (or project subfolder).
5. Build Command: Leave blank (or set to `python build.py` if retraining).
6. Output Directory: Leave blank.
7. Click **Deploy**.

---

## 8. Defensive Security & Ethical Design Principles

- **No Link Navigation:** PhishShift never issues `fetch()`, `XMLHttpRequest`, or `iframe` navigations to URLs found inside analyzed messages.
- **Safe DOM APIs:** Untrusted message text and extracted matching snippets are rendered strictly through `textContent` and `document.createElement()`. No `innerHTML` interpolation of user content is permitted.
- **Defensive Input Handling:** The scanner rejects empty input, enforces a 2,000-character ceiling, and prevents automated submission flooding.
- **Transparent AI Disclaimer:** The application never guarantees total safety or complete detection; it explicitly educates users on independent out-of-band verification.
