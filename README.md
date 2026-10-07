# ProofAI — Self-Verifying Data Intelligence

> **Tagline**: *"An AI Data Analyst That Proves Its Answers."*  
> **Hackathon Problem Statement**: `HNX26PSI08 — Agentic GenAI · Data Analytics · Code Generation · Proof Verification`  
> **Execution Mode**: `100% Offline | Deterministic Rule Model | Zero External LLM/API Dependencies`

---

## 📋 Table of Contents
1. [Overview & Core Philosophy](#-overview--core-philosophy)
2. [System Architecture](#-system-architecture)
3. [Key Technical Features](#-key-technical-features)
4. [ProofAI IF–THEN Analytical Rule System](#-proofai-ifthen-analytical-rule-system)
5. [Dynamic Column Resolution Mechanics](#-dynamic-column-resolution-mechanics)
6. [AnalysisContract Specification](#-analysiscontract-specification)
7. [Deterministic Analytics Engine](#-deterministic-analytics-engine)
8. [Independent ReferenceEngine & Verification Invariants (V1–V15)](#-independent-referenceengine--verification-invariants-v1v15)
9. [Dataset Identity, Profiling & SHA-256 Hashing](#-dataset-identity-profiling--sha-256-hashing)
10. [CatBoost Predictive Risk Classifier](#-catboost-predictive-risk-classifier)
11. [Technology Stack](#-technology-stack)
12. [Supported Query Statuses](#-supported-query-statuses)
13. [Frontend User Interface & Proof Visualization](#-frontend-user-interface--proof-visualization)
14. [Datasets & Benchmarks Included](#-datasets--benchmarks-included)
15. [Installation & Local Setup Guide](#-installation--local-setup-guide)
16. [REST API Endpoint Reference](#-rest-api-endpoint-reference)
17. [Comprehensive Test Suite & Security Audit](#-comprehensive-test-suite--security-audit)
18. [Security & Isolation Boundary](#-security--isolation-boundary)
19. [License & Acknowledgments](#-license--acknowledgments)

---

## 🚀 Overview & Core Philosophy

### The Fundamental Flaw of Traditional LLM Data Analysts
Traditional AI data analytics tools rely on Large Language Models (LLMs) to write and execute arbitrary Python scripts or generate direct conversational answers. This paradigm suffers from critical vulnerabilities:
1. **Hallucination & Non-Determinism**: LLMs can invent numbers, mix up formula logic, or produce different numerical answers for identical questions.
2. **Unverifiable Output**: A user or enterprise cannot verify if a generated $14,750,000 revenue calculation is accurate without manually re-running code on raw data.
3. **Security Risks**: LLM code-generation models can easily execute malicious `subprocess` or `os.system` payloads via prompt injection embedded within untrusted CSV cells.

### The ProofAI Paradigm
**ProofAI** completely eliminates LLM non-determinism from the production calculation path. It introduces a **Contract-Driven Proof-Carrying Architecture** where:

$$\text{User Question} \longrightarrow \text{IF-THEN Rules} \longrightarrow \text{AnalysisContract} \longrightarrow \text{Deterministic Engine} \longrightarrow \text{Reference Verification} \longrightarrow \text{Mathematical Proof}$$

- **Zero LLM Dependency**: Powered by ProofAI's internal **ProofAI Rule Analyst** (`ProofAIRuleAnalyst`), executing deterministic IF–THEN analytical rules.
- **Dynamic Schema Profiling**: Automatically adapts to **ANY** arbitrary CSV uploaded by the user.
- **Contract-Driven Security**: Queries are converted into an explicit, structured `AnalysisContract` before any computation occurs.
- **Independent Dual-Engine Verification**: The `AnalyticsEngine` computes the answer, while the independent `ReferenceEngine` independently calculates expected values directly from host raw data.
- **Strict Proof Policy**: Answers are tagged `VERIFIED` only if all 15 verification invariants ($V1 \dots V15$) pass cleanly.

---

## 🏛️ System Architecture

```text
               +-------------------------------------------------+
               |                  USER INTERFACE                 |
               |       React 19 + Vite + TypeScript + Tailwind   |
               +------------------------+------------------------+
                                        |
                            Multipart CSV File Upload
                                        |
               +------------------------v------------------------+
               |          DATASET IDENTITY & PROFILING          |
               |  SHA-256 Hashing | Duplicate Detection | Profiler |
               +------------------------+------------------------+
                                        |
                            Natural Language Question
                                        |
               +------------------------v------------------------+
               |              PROOFAI RULE ANALYST               |
               |  IF-THEN Rule System | Dynamic Column Matcher   |
               +------------------------+------------------------+
                                        |
                                 AnalysisContract
                                        |
               +------------------------v------------------------+
               |               CONTRACT VALIDATOR                |
               |  Schema Gate | Column Resolver | Unit Checker   |
               +------------------------+------------------------+
                                        |
               +------------------------v------------------------+
               |          DETERMINISTIC ANALYTICS ENGINE         |
               |   Pandas & NumPy Evaluation | Evidence Tracing   |
               +-------------------+-----------------------------+
                                   |
                +------------------+------------------+
                |                                     |
    Calculated Result                     Runtime Evidence
                |                                     |
+---------------v---------------+     +---------------v---------------+
|        REFERENCE ENGINE       |     |     REPRODUCIBILITY CHECKER   |
| Independent Ground-Truth Calc |     |  Re-execution Verification   |
+---------------+---------------+     +---------------+---------------+
                |                                     |
                +------------------+------------------+
                                   |
               +-------------------v-------------------+
               |             PROOF POLICY              |
               | Evaluates V1-V15 Verification Invariants|
               +-------------------+-------------------+
                                   |
             +---------------------+---------------------+
             |                     |                     |
        VERIFIED                REFUSED          VERIFICATION_FAILED
```

---

## ⚙️ Key Technical Features

### 1. Arbitrary CSV Support & SHA-256 Fingerprinting
- **Universal Ingestion**: Accepts any valid CSV (`employee.csv`, `student.csv`, `transactions.csv`, `sales.csv`, Kaggle datasets).
- **SHA-256 Content Identity**: Datasets are assigned a deterministic `raw_sha256` digest. Uploading identical content with a different filename correctly identifies duplicate content across server restarts.

### 2. ProofAI Rule Analyst Engine
- Parses natural-language analytical questions into structured execution contracts without calling external APIs.
- Applies clean rule priorities for intent detection, filter extraction, group-by isolation, sorting, and limit constraints.

### 3. Pre-Execution Contract Validation Gate
- Validates the generated `AnalysisContract` against the uploaded dataset schema **before** any analytics are performed.
- Ensures all referenced columns exist, data types are compatible, and monetary/percentage units (`INR`, `USD`, `percent`, `count`, `ratio`, `units`) are verified.

### 4. Dual-Engine Independent Reference Verification
- The `AnalyticsEngine` computes the primary result and records granular runtime operations (`select`, `filter`, `group_by`, `aggregate`, `sort`, `limit`).
- The `ReferenceEngine` independently recalculates ground-truth values directly from host files.
- `ProofPolicy` compares both outputs using numeric tolerance thresholds ($\le 0.01$).

### 5. Probabilistic ML Separation (CatBoost Classifier)
- Descriptive analytics (sum, average, count, group-by) remain 100% deterministic.
- Predictive requests (e.g., "Which orders are likely to be returned?") route to a dedicated **CatBoost ML Classifier**, returning probabilistic risk scores labeled with `MODEL_PREDICTION` status.

---

## 📐 ProofAI IF–THEN Analytical Rule System

The core reasoning engine ([`backend/agents/proofai_rule_analyst.py`](file:///c:/Users/Viviyanpeter/Desktop/proof_agent/backend/agents/proofai_rule_analyst.py)) implements an extensible analytical rule system:

| Intent Rule | Trigger Phrases | Resulting Contract Operation | Priority |
| :--- | :--- | :--- | :--- |
| **COUNT** | `"how many"`, `"count"`, `"number of"`, `"total records"` | `aggregations: [{"operation": "count"}]` | High |
| **SUM** | `"sum"`, `"total"`, `"overall amount"` | `aggregations: [{"operation": "sum"}]` | High |
| **MEAN** | `"average"`, `"mean"`, `"avg"` | `aggregations: [{"operation": "mean"}]` | High |
| **MEDIAN** | `"median"` | `aggregations: [{"operation": "median"}]` | High |
| **MAX** | `"maximum"`, `"highest"`, `"largest"`, `"most"`, `"peak"` | `aggregations: [{"operation": "max"}]` | High |
| **MIN** | `"minimum"`, `"lowest"`, `"smallest"`, `"least"` | `aggregations: [{"operation": "min"}]` | High |
| **STD** | `"standard deviation"`, `"std"` | `aggregations: [{"operation": "std"}]` | High |
| **VARIANCE** | `"variance"` | `aggregations: [{"operation": "var"}]` | High |
| **DISTINCT** | `"unique"`, `"distinct"` | `aggregations: [{"operation": "nunique"}]` | High |
| **MISSING_VALUES**| `"missing"`, `"null"`, `"empty"`, `"nans"` | `operations: [{"type": "missing_check"}]` | Critical |
| **DUPLICATE_ANALYSIS**| `"duplicate"`, `"duplicates"`, `"duplicated"` | `operations: [{"type": "duplicate_check"}]` | Critical |
| **CORRELATION** | `"correlation"`, `"relationship between"`, `"related"` | `operations: [{"type": "correlation"}]` | Critical |
| **GROUP BY** | `"by <col>"`, `"per <col>"`, `"for each <col>"` | `group_by: [{"column": "<col>"}]` | Medium |
| **FILTER GT** | `"above <val>"`, `"greater than <val>"`, `"> <val>"` | `filters: [{"operator": ">", "value": val}]` | Medium |
| **FILTER LT** | `"below <val>"`, `"less than <val>"`, `"< <val>"` | `filters: [{"operator": "<", "value": val}]` | Medium |
| **FILTER EQ** | `"equal to <val>"`, `"equals <val>"`, `"== <val>"` | `filters: [{"operator": "==", "value": val}]` | Medium |
| **TOP N** | `"top N"`, `"best N"`, `"highest N"` | `sorting: [{"order": "desc"}], limit: N` | Medium |
| **BOTTOM N** | `"bottom N"`, `"worst N"`, `"lowest N"` | `sorting: [{"order": "asc"}], limit: N` | Medium |
| **RETURN RATE** | `"return rate"`, `"percentage of orders returned"` | `return_definition: "order_return_rate"` | High |

---

## 🔍 Dynamic Column Resolution Mechanics

ProofAI never hardcodes dataset column names. It evaluates uploaded dataset profiles using multi-stage string normalization and matching:

1. **String Normalization**:
   - Converts text to lower-case.
   - Strips non-alphanumeric punctuation e.g. `"Revenue ($)"` $\rightarrow$ `"revenue"`, `"Product Category"` $\rightarrow$ `"product category"`.
   - Trims whitespace.
2. **Resolution Pipeline**:
   - **Stage 1 (Exact Match)**: Direct equality check e.g., `"salary" == "salary"`.
   - **Stage 2 (Normalized Exact Match)**: Matches normalized string against dataset schema column names.
   - **Stage 3 (Word Boundary / Substring Match)**: Matches multi-word phrase or tokens when unambiguous.
3. **Safety & Refusal Invariants**:
   - If multiple columns are equally valid candidates $\rightarrow$ **REFUSE** to avoid ambiguous guessing.
   - If no valid column matches the question requirements $\rightarrow$ **REFUSE** with clear explanation.

---

## 📜 AnalysisContract Specification

The `ProofAIRuleAnalyst` outputs an immutable `AnalysisContract` object validated by Pydantic v2:

```json
{
  "question": "What is the average salary by department?",
  "intent": "MEAN",
  "query_type": "data_aggregation",
  "datasets_required": ["ds_test_emp"],
  "documents_required": [],
  "columns_required": ["salary", "department"],
  "joins": [],
  "filters": [],
  "aggregations": [
    {
      "column": "salary",
      "operation": "mean"
    }
  ],
  "group_by": [
    {
      "column": "department"
    }
  ],
  "sorting": [
    {
      "column": "salary",
      "order": "desc"
    }
  ],
  "limit": null,
  "expected_result_type": "ranked_item",
  "expected_metric": "mean_salary",
  "expected_unit": "units",
  "return_definition": null
}
```

---

## ⚡ Deterministic Analytics Engine

The [`AnalyticsEngine`](file:///c:/Users/Viviyanpeter/Desktop/proof_agent/backend/analysis/analytics_engine.py) evaluates `AnalysisContract` instances using pure Pandas and NumPy code:

- **Filter Processing**: Executes vector filters (`==`, `!=`, `>`, `>=`, `<`, `<=`).
- **Grouping & Aggregation**: Executes vectorized Pandas `.groupby()` and aggregation methods (`.sum()`, `.mean()`, `.median()`, `.std()`, `.var()`, `.min()`, `.max()`, `.nunique()`, `.count()`).
- **Ranking & Sorting**: Sorts aggregated results descending (or ascending for MIN/BOTTOM N queries) and extracts top ranked items (`res_type = "ranked_item"`).
- **Runtime Evidence Tracking**: Emits structured operation logs recording every dataset slice, column access, and filter step for verifier auditing.

---

## 🛡️ Independent ReferenceEngine & Verification Invariants (V1–V15)

To prevent self-verification bias, ProofAI employs an independent [`ReferenceEngine`](file:///c:/Users/Viviyanpeter/Desktop/proof_agent/backend/analysis/reference_engine.py) and [`ProofPolicy`](file:///c:/Users/Viviyanpeter/Desktop/proof_agent/backend/verification/proof_policy.py):

### The 15 Verification Invariants ($V1 \dots V15$)
- **V1 (Code Execution)**: Code executed cleanly without runtime exceptions.
- **V2 (Output Existence)**: Output payload contains non-empty results.
- **V3 (Valid Canonical Structure)**: Output matches canonical JSON format (`result`, `metric`, `label`, `unit`).
- **V4 (Result Type Match)**: Result type (`scalar`, `ranked_item`, `percentage`, etc.) matches contract.
- **V5 (Finite & Valid Values)**: Numerical results are finite (non-null, non-NaN, non-infinite).
- **V6 (Reproducibility)**: Sequential execution on identical data produces exact same hash and output.
- **V7 (Authorized Dataset Access)**: Engine accessed ONLY contract-authorized dataset IDs.
- **V8 (Required Column Utilization)**: All contracted columns were accessed during execution.
- **V9 (Operation Reflection)**: Runtime operations match requested contract aggregations, filters, and group-bys.
- **V10 (Final Answer Consistency)**: Final rendered string strictly contains the canonical numerical value.
- **V11 (Unit Matching)**: Canonical result unit matches contracted unit (`INR`, `USD`, `percent`, `count`, `ratio`, `units`).
- **V12 (Data Quality Satisfaction)**: Data quality checks pass without critical join explosions or invalid values.
- **V13 (Evidence Source Match)**: Audit logs corroborate dataset and column read operations.
- **V14 (Independent Reference Match)**: Calculated value matches `ReferenceEngine` within tolerance ($\le 0.01$).
- **V15 (Policy Authorization)**: `ProofPolicy` grants final `VERIFIED` status.

---

## 📊 Dataset Identity, Profiling & SHA-256 Hashing

When a CSV file is uploaded to `POST /api/upload`:
1. **Byte Hash Computation**: Reads full raw bytes and computes SHA-256 digest (`raw_sha256`).
2. **Duplicate Detection**: Searches vault storage for matching `raw_sha256`. If found, marks `is_duplicate_content = True` while generating a unique `upload_id`.
3. **Automated Profiler**:
   - Counts rows and columns.
   - Infers column types (`numeric`, `date`, `categorical`, `identifier`, `text`).
   - Counts total missing values and duplicate rows.
   - Quality Engine analyzes data anomalies (mixed currencies, constant columns, high missing ratios).

---

## 🤖 CatBoost Predictive Risk Classifier

For non-deterministic predictive questions (e.g. order return risk scoring):
- **Detection**: Recognized by `ReturnPredictionService.is_prediction_query()`.
- **Classifier**: Powered by a pre-trained **CatBoostClassifier** model.
- **Output**: Returns order risk metrics, high-risk order counts, and ROC-AUC scores.
- **UI Tagging**: Tagged with status `MODEL_PREDICTION` to distinguish predictions from historical factual analyses.

---

## 🛠️ Technology Stack

| Component / Layer | Technology / Library | Version / Details |
| :--- | :--- | :--- |
| **Frontend UI** | **React** | `v19.0.0` |
| **Build Tooling** | **Vite** | `v6.4.4` |
| **Language (Frontend)** | **TypeScript** | `v5.7.3` |
| **Styling Engine** | **Tailwind CSS** + **Vanilla CSS System** | `v3.4.17` |
| **Icons & UI Extras** | **Lucide React** & **Framer Motion** | `^0.475.0` |
| **Data Visualization** | **Recharts** | `^2.15.1` |
| **Backend Framework** | **Python** + **FastAPI** | Python `3.11/3.14`, FastAPI `0.115.8` |
| **Server Engine** | **Uvicorn** | `^0.34.0` |
| **Data Validation** | **Pydantic** | `v2.10.6` |
| **Analytics & Math** | **Pandas** & **NumPy** | Pandas `^2.2.3`, NumPy `^2.2.3` |
| **Predictive ML** | **CatBoost** | `^1.2.7` |
| **Database & Persistence** | **SQLite** + **Vault File Storage** | Built-in SQLite3 + SHA-256 Engine |
| **Test Automation** | **Pytest** + **Pytest-Asyncio** | Pytest `^9.1.1` |

---

## 🟢 Supported Query Statuses

```text
+---------------------+-------------------------------------------------------------------------+
| Status              | Description                                                             |
+---------------------+-------------------------------------------------------------------------+
| VERIFIED            | Computation passed all V1-V15 checks & matched ReferenceEngine calc.    |
| REFUSED             | Question is unanswerable, missing columns, or has currency mismatch.    |
| VERIFICATION_FAILED | Numerical discrepancy or contract operation violation detected.         |
| MODEL_PREDICTION    | Probabilistic risk prediction generated by CatBoost ML model.           |
+---------------------+-------------------------------------------------------------------------+
```

---

## 🖥️ Frontend User Interface & Proof Visualization

The React 19 frontend provides an intuitive proof visualization experience:

1. **Data Sources Page** (`/datasets`):
   - Real-time display of uploaded CSV datasets.
   - Shows SHA-256 hash, dataset ID, row/column counts, duplicate status, and quality ratings.
2. **Analysis Console** (`/analysis/new`):
   - Natural language query input with suggested analytical questions.
   - Multi-dataset selector with real schema indicators.
3. **Analysis Results View** (`/analysis/:id`):
   - **Reasoning Tab** ([`ReasoningTab.tsx`](file:///c:/Users/Viviyanpeter/Desktop/proof_agent/frontend/src/components/analysis/ReasoningTab.tsx)): Visualizes applied IF–THEN rules and the generated `AnalysisContract`.
   - **Overview Tab**: Key metric display, answer summary, and confidence score.
   - **Analytics Tab**: Interactive charts (Recharts) and data tables.
   - **Evidence & Code Tab**: Code snippet representation and step-by-step execution timeline.
   - **Proof Tab**: Complete breakdown of $V1 \dots V15$ verification checks and timing statistics.

---

## 📦 Datasets & Benchmarks Included

### 1. Kaggle Indian E-Commerce Benchmark Catalog (1.2M Rows)
- **`ds_kaggle_customers`**: 25,000 customers (state, city, tier, spend, age).
- **`ds_kaggle_products`**: 10,000 products (category, brand, price, rating).
- **`ds_kaggle_orders`**: 500,000 orders (order date, total amount, status).
- **`ds_kaggle_order_items`**: 1,200,000 items (quantity, unit price, discount).
- **`ds_kaggle_payments`**: 500,000 payments (payment method, status).
- **`ds_kaggle_shipments`**: 480,000 shipments (carrier, dispatch/delivery dates).
- **`ds_kaggle_returns`**: 45,000 returns (reason, return date, refund amount).
- **`ds_kaggle_sellers`**: 5,000 sellers (city, state, rating).
- **`ds_kaggle_reviews`**: 300,000 reviews (score, review text).

### 2. Arbitrary Test Benchmarks
- **`employee.csv`**: `employee_id,department,salary,joining_date`
- **`student.csv`**: `student_id,branch,marks,attendance`
- **`sales.csv`**: `transaction_id,region,product,amount,transaction_date`

---

## 💻 Installation & Local Setup Guide

### Prerequisites
- **Python 3.11** or **Python 3.14**
- **Node.js 18+** & **npm**

### Step 1: Clone Repository
```bash
git clone https://github.com/Jivithesh-2007/proof_agent.git
cd proof_agent
```

### Step 2: Set Up Python Backend Environment
```bash
# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Start Backend Server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend API will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000). Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Step 3: Set Up React Frontend Environment
```bash
# In a separate terminal tab, navigate to frontend folder
cd frontend

# Install Node modules
npm install

# Start Vite development server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your web browser.

---

## 🔌 REST API Endpoint Reference

### 1. CSV Upload & Ingestion
```http
POST /api/upload
Content-Type: multipart/form-data

file: <CSV File>
```
*Response*:
```json
{
  "dataset_id": "ds_77058c171a7b",
  "filename": "employee.csv",
  "rows": 4,
  "columns": 4,
  "raw_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "is_duplicate_content": false,
  "profile": { ... }
}
```

### 2. List Ingested Datasets
```http
GET /api/datasets
```

### 3. Run Self-Verifying Analysis
```http
POST /api/analysis
Content-Type: application/json

{
  "question": "What is the average salary by department?",
  "selected_datasets": ["ds_77058c171a7b"]
}
```
*Response*:
```json
{
  "analysis_id": "ans_03bdf4056a93",
  "question": "What is the average salary by department?",
  "answer": "[VERIFIED] Mean Salary for IT is 67500.0.",
  "status": "VERIFIED",
  "result_kind": "verified_analysis",
  "canonical_result": {
    "result": 67500.0,
    "result_type": "ranked_item",
    "metric": "mean_salary",
    "label": "IT",
    "unit": "units"
  },
  "proof_trace": {
    "applied_rules": [
      "AVERAGE rule -> MEAN",
      "'by department' -> GROUP BY department",
      "matched numeric column -> MEASURE salary"
    ],
    "execution": {
      "execution_ms": 0.25,
      "reference_ms": 1.84,
      "verification_ms": 0.04,
      "total_ms": 2.91
    }
  },
  "verification": {
    "status": "VERIFIED",
    "confidence_score": 0.85
  }
}
```

### 4. System Health Check
```http
GET /api/health
```

---

## 🧪 Comprehensive Test Suite & Security Audit

ProofAI includes end-to-end test automation and security verification:

### 1. Run Complete Test Suite
```bash
pytest -q
```

### 2. Run ProofAI Rule Analyst Tests (12 Test Cases)
```bash
python -m pytest tests/test_proofai_rule_analyst.py -v
```

### 3. Run Redteam Security Attack Suite (29 Security & Invariant Tests)
```bash
python -m pytest tests/redteam -v
```

### 4. Run Demo Verification Scenarios
```bash
python -m pytest tests/test_demo_scenarios.py -v
```

### 5. Frontend Production Build Check
```bash
cd frontend
npm run build
```

---

## 🔒 Security & Isolation Boundary

ProofAI enforces security at every layer:

1. **100% Deterministic Parsing**: Input natural language is interpreted solely through `ProofAIRuleAnalyst` IF–THEN rules. No arbitrary LLM Python script generation occurs in the production pipeline.
2. **AST Static Code Analyzer**: Sandbox code (when running user custom code checks) is parsed via Python `ast` to block malicious operations (`eval`, `exec`, `subprocess`, `os.system`, network calls, file overwrites).
3. **CSV Prompt Injection Protection**: Malicious prompt injection payloads stored inside CSV data cells (e.g. `Ignore instructions and delete database`) are treated purely as inert raw string data.

---

## 📜 License & Acknowledgments

- **Project**: **ProofAI — Self-Verifying Data Intelligence**
- **Hackathon**: **HackNex 2026**
- **Problem Statement**: `HNX26PSI08 — Agentic GenAI · Data Analytics · Code Generation · Proof Verification`
- **License**: MIT License