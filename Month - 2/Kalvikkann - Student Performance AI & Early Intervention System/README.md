# Kalvikkann – Student Performance AI & Early Intervention System

[![Next.js](https://img.shields.io/badge/Next.js-14.2-black?logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue?logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4%2B-orange?logo=scikit-learn)](https://scikit-learn.org/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38bdf8?logo=tailwind-css)](https://tailwindcss.com/)

> **An end-to-end AI-driven academic early warning, student achievement gallery, and intelligent intervention platform built for higher education institutions.**

---

## 1. Project Title & Introduction

**Kalvikkann** (*கண் - "The Eye of Education"*) is an enterprise-grade AI academic analytics and early intervention platform designed to proactively identify students at risk of academic failure, automate faculty remediation workflows, and authenticate holistic student achievements through an integrated student certificate gallery.

Combining a modern **Next.js 14** web portal with a trained **Scikit-Learn Machine Learning pipeline**, Kalvikkann transforms fragmented marks, attendance records, and extracurricular certificates into actionable insights, real-time risk scores, and automated parent notifications.

---

## 2. Problem Statement

Modern collegiate institutions face significant retention and performance monitoring challenges:
- **Delayed Intervention:** Risk factors such as low attendance, declining internal assessment scores, or missing assignments are typically noticed only after end-semester exam results are released, when it is too late to intervene.
- **Data Fragmentation:** Marks, attendance sheets, and certificates are scattered across disconnected paper records, spreadsheets, and portals.
- **Uncredited Co-curricular Achievements:** Valuable co-curricular certificates (e.g., NPTEL courses, hackathon awards, industrial workshops) often remain unverified and do not contribute to academic trajectory models.
- **Opaque Risk Scoring:** Traditional academic scoring offers black-box classifications without explainable root causes, preventing mentors from delivering targeted remediation.

---

## 3. Objectives

- **Early Risk Detection:** Forecast student performance category (`High`, `Average`, `Low`) prior to final exams using trained predictive machine learning models.
- **Explainable Diagnostics:** Provide mentors with clear impact factors (e.g., *Attendance < 75%*, *Previous Semester Drop*, *Weak Performance in Mathematics*).
- **Holistic Achievement Gallery:** Maintain a dedicated visual gallery for every student to store, view, verify, and export all certificates, credentials, and achievements.
- **Multimodal Credential Extraction:** Support single or multiple image uploads for marksheets and certificates with OCR-driven metric extraction and automatic prediction score bonuses.
- **Closed-Loop Remediation:** Enable mentors to generate personalized remedial study plans, assign peer mentors, and log automated alerts to parents.

---

## 4. Key Features

### 🎓 1. Student Achievement Gallery & Verification
* **Dedicated Visual Gallery for Every Student:** Stores every uploaded certificate, award, marksheet, and credential.
* **Faculty Verification & Endorsement:** Mentors can inspect credentials in high resolution, verify authenticity, and digitally endorse them with a single click.
* **Credential Export & Print:** Download high-resolution credentials or print official certificates directly from the browser.
* **Skill Badges & Prediction Bonus:** Each verified credential tags relevant technical competences (e.g., *Deep Learning*, *Cloud Computing*, *Full Stack*) and applies a transparent score bonus (+2% to +5%).

### 🤖 2. Dual-Engine Machine Learning Prediction
* **Trained Models:** Built with Scikit-Learn utilizing **RandomForestClassifier** (Early Prediction mode, CV Macro-F1: 77.1%, Test Accuracy: 79.1%) and **HistGradientBoostingClassifier** (Full Academic mode, 100% test accuracy).
* **Live Probability Distribution:** Interactive probability breakdown across all three performance classes (`High`, `Average`, `Low`).
* **Real-Time Input Simulation:** Interactive parameter sliders for attendance, internal marks, study hours, technical skills, coding scores, and backlogs.

### 📄 3. Multimodal Batch Image & Marksheet Upload
* **Single & Multiple Image Uploads:** Drop multiple certificate or marksheet photos (PNG, JPG, JPEG, WebP) simultaneously.
* **Automated OCR Parsing:** Automatically parses document titles, issuing authorities, attendance percentages, and internal marks.
* **Instant Notification Dispatch:** Broadcasts instant alerts informing faculty and students of updated predictions.

### 📊 4. Faculty & Student Multi-Role Portals
* **Faculty Dashboard:** Institution-wide cohort overview, risk distribution charts, student ranking directory, and batch dataset uploaders.
* **Student Private Portal:** Personalized dashboard highlighting current standing, AI recommendations, weakest subjects, assigned peer mentors, and achievement gallery.
* **Explainable AI Insights:** Detailed diagnostic breakdown explaining exactly why a student was flagged.
* **Intervention Center & Parent Alerts:** Track remediation plans, assign department advisors, and log parent communications via SMS/Email.

---

## 5. System Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                     Client Browser (UI)                         │
│   Next.js 14 App Router • Tailwind CSS • Lucide Icons • Recharts │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Next.js API & Client Engine                  │
│   ├── /api/predict          → ML Proxy & Fallback Engine        │
│   ├── Store (Local Storage) → Multi-Role State & Galleries      │
│   ├── Document Extractor    → Multimodal OCR Vision Parser      │
│   └── Report Generator      → Academic PDF / Export Engine      │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│               Python Machine Learning Microservice              │
│   ├── Flask API (app.py)    → Endpoint /predict & /batch-predict│
│   ├── Preprocessing         → OneHotEncoder + StandardScaler   │
│   ├── Trained Models        → model_early.pkl (RandomForest)    │
│   │                         → model_full.pkl (HistGradientBoost)│
│   └── Datasets              → 12,500+ Engineering Student Records│
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend Framework** | Next.js 14 (App Router), React 18, TypeScript 5.6 |
| **Styling & UI** | Tailwind CSS, Lucide React Icons, Clsx, Tailwind-Merge |
| **Data Visualization** | Recharts (Responsive Line & Bar Charts) |
| **Backend / ML Service** | Python 3.10+, Flask, Flask-CORS |
| **Machine Learning** | Scikit-Learn 1.4+, Pandas, NumPy, Joblib |
| **Document OCR Vision** | Multimodal Document Parser & Canvas Image Generator |

---

## 7. AI Prediction Workflow

1. **Data Ingestion:** Collects 20 student features: department, semester, attendance percentage, study hours, internal marks, assignment completion, coding skills, technical skills, and backlogs.
2. **Preprocessing Pipeline:**
   - Numerical columns processed with `SimpleImputer(strategy='median')` followed by `StandardScaler()`.
   - Categorical columns processed with `SimpleImputer(strategy='most_frequent')` followed by `OneHotEncoder(handle_unknown='ignore')`.
3. **Model Evaluation:** The trained `RandomForestClassifier` analyzes the pipeline output and generates class probabilities.
4. **Explainability Extraction:** Identifies primary risk drivers (e.g., attendance falling below Anna University/institutional 75% thresholds).
5. **Score Formulation:** Integrates verified co-curricular certificates from the Student Gallery as calibrated score bonuses.

---

## 8. Student & Faculty Functionalities

### For Faculty:
- Browse all enrolled students filtered by department, risk level, or name.
- View individual student achievement galleries with all uploaded certificates.
- Verify and endorse submitted credentials with verified-by timestamps.
- Upload marks, attendance slips, and activity certificates via single or multi-image upload.
- Launch remedial interventions and notify parents.

### For Students:
- View verified predicted scores and risk status privately.
- Access their personalized **Achievement Gallery** showcasing all earned certificates.
- Upload new certificates, awards, and marksheets with live previews.
- View weakest subject diagnostics and assigned peer mentors.
- Download or print certificates and semester progress reports.

---

## 9. Early Intervention Mechanism

When Kalvikkann detects a student transitioning into `MEDIUM` or `HIGH` risk:
1. **Explainable Flagging:** Alerts the mentor with specific contributing factors.
2. **Action Plan Generation:** Formulates a tailored study schedule targeting weak subjects.
3. **Peer Mentor Pairing:** Matches the student with a high-performing peer in the same department.
4. **Parent Notification Log:** Records formal SMS/Email alerts to parents with delivery status tracking.

---

## 10. Installation Instructions

### Prerequisites
- **Node.js** v18.17 or higher
- **npm** or **yarn**
- **Python** 3.10 or higher with `pip`

### Step 1: Clone the Repository
```bash
git clone https://github.com/naveenkumar6957/CN-INTERNSHIP-PROJECTS.git
cd "CN-INTERNSHIP-PROJECTS/Month - 2/Kalvikkann - Student Performance AI & Early Intervention System"
```

### Step 2: Install Node Dependencies
```bash
npm install
```

### Step 3: Install Python ML Dependencies
```bash
pip install flask flask-cors scikit-learn pandas numpy joblib
```

---

## 11. Environment Variable Configuration

Create a `.env.local` file in the project root if customizing default ports:

```env
# Optional: URL of the running Python Flask ML API (Defaults to http://127.0.0.1:5000)
FLASK_API_URL=http://127.0.0.1:5000

# Optional: Port configuration
PORT=3000
```

*(Note: The Next.js application includes an internal fallback engine and will run smoothly even before starting the Python service.)*

---

## 12. How to Run the Application Locally

### Running the Python ML Prediction Service
In a terminal window, start the Flask prediction API:
```bash
python app.py
```
*API will run on `http://127.0.0.1:5000`.*

### Running the Next.js Web Application
In a separate terminal window, start the Next.js development server:
```bash
npm run dev
```
*Open your browser and navigate to `http://localhost:3000`.*

### Re-training the ML Models (Optional)
If you wish to re-train the models on the dataset:
```bash
python train_model.py
```

---

## 13. Default Demo Accounts

For demonstration and testing purposes, Kalvikkann includes pre-configured demo credentials:

| Role | Email / ID | Password | Access Scope |
|---|---|---|---|
| **Faculty / Mentor** | `ramanathan@edu.in` | `faculty@123` | Full faculty dashboard, gallery verification, interventions |
| **Student (High Risk)** | `eng0025@edu.in` (EMIS: `ENG0025`) | `student@123` | Student dashboard, gallery uploads, remedial plan |
| **Student (On Track)** | `eng0001@edu.in` (EMIS: `ENG0001`) | `student@123` | Student dashboard, verified achievement gallery |
| **Administrator** | `admin@kalvikkan.ai` | `admin@123` | Faculty registration, model weight adjustments |

---

## 14. Future Enhancements

- Integration with University ERP databases via automated REST hooks.
- Biometric & automated camera attendance syncing.
- LLM-powered dynamic chat responses using Retrieval-Augmented Generation (RAG) over university syllabus documents.
- Blockchain-backed credential hashing for tamper-proof certificate verification.
