# Fin-LLM-NFRA

# NFRA - ML-Powered PDF Page Classification System

**Date:** February 12, 2026

---

## What This System Does

Automatically identifies and extracts **financial statement pages** from annual report PDFs using Machine Learning.

**Input:** Annual Report PDF (300+ pages)  
**Output:** Separate markdown files for each financial statement type

---

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Usage

**Two processing modes available:**

| Script | Model | Description |
|--------|-------|-------------|
| `Single_model.py` | Logistic Regression | Fast, single model classification |
| `category_segmentation.py` | Ensemble (LR + RF) | Higher recall, union of both models |

**Classify only (preview pages without LlamaParse):**
```bash
cd Preprocessing
python Single_model.py "path/to/annual_report.pdf" --classify
python category_segmentation.py "path/to/annual_report.pdf" --classify
```

**Full processing (classify + extract markdown):**
```bash
cd Preprocessing
python Single_model.py "path/to/annual_report.pdf"
python category_segmentation.py "path/to/annual_report.pdf"
```

Output files are saved to: `output/<pdf_name>/`

---

## The Problem We Solve

Annual reports contain many sections, but we only need **4 types of financial statements**:

| Category | What It Contains |
|----------|------------------|
| **Balance Sheet (BS)** | Assets, Liabilities, Equity |
| **Profit & Loss (PL)** | Revenue, Expenses, Net Income |
| **Cash Flow** | Operating, Investing, Financing Activities |
| **Notes** | Accounting Policies, Disclosures |

Manually finding these pages in 300+ page documents is slow and error-prone. **Our ML models automate this.**

---

## How the ML Models Identify Pages

### Single Model Mode (Single_model.py)
Uses **Logistic Regression** classifier for fast, accurate classification.

### Ensemble Mode (category_segmentation.py)
Uses **union of both LR and RF** models - if either model classifies a page as financial, it's included. Higher recall, catches more relevant pages.

### ML Classification Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ML PAGE CLASSIFICATION                            │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  PDF Page Text   │
    └────────┬─────────┘
             │
             ▼
┌─────────────────────────────────────┐
│       TEXT PREPROCESSING            │
│  ┌─────────────────────────────┐    │
│  │ 1. Convert to Lowercase     │    │
│  │ 2. Remove Special Characters│    │
│  │ 3. Normalize Whitespace     │    │
│  └─────────────────────────────┘    │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│           ML ENGINE                 │
│  ┌─────────────────────────────┐    │
│  │    TF-IDF Vectorizer        │    │
│  │           ▼                 │    │
│  │  Single: Logistic Regression│    │
│  │  Ensemble: LR + Random Forest│   │
│  └─────────────────────────────┘    │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│     HEADER KEYWORD MATCHING         │
│  ┌─────────────────────────────┐    │
│  │ Filters BS/PL/Cash Flow by  │    │
│  │ checking page headers       │    │
│  └─────────────────────────────┘    │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│        CATEGORY OUTPUT              │
│                                     │
│   ┌───────────┐  ┌─────────────┐    │
│   │ Balance   │  │ Profit &    │    │
│   │ Sheet     │  │ Loss        │    │
│   └───────────┘  └─────────────┘    │
│   ┌───────────┐  ┌─────────────┐    │
│   │ Cash Flow │  │ Notes       │    │
│   └───────────┘  └─────────────┘    │
│   ┌─────────────────────────────┐   │
│   │ Skip - Not Financial        │   │
│   └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### What Keywords Matter?

The ML models learn to recognize patterns:

| If page contains... | Model predicts... |
|---------------------|-------------------|
| "assets", "liabilities", "equity", "property" | **Balance Sheet** |
| "revenue", "expenses", "profit", "cost of goods" | **Profit & Loss** |
| "cash flows", "operating activities", "financing" | **Cash Flow** |
| "accounting policies", "disclosure", "valuation" | **Notes** |

### Header Keyword Matching

After ML classification, pages are further validated by checking headers:

| Category | Header must contain |
|----------|---------------------|
| BS | "balance sheet", "statement of assets and liabilities" |
| PL | "income statement", "profit and loss", "statement of profit and loss" |
| Cash Flow | "cash flow", "statement of cash flow" |

Notes pages are excluded from BS/PL/Cash Flow if header starts with "notes".

---

## Technical Pipeline: Where Each Tool is Used

### Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE PROCESSING PIPELINE                              │
└─────────────────────────────────────────────────────────────────────────────┘

╔═════════════════════════════════════════════════════════════════════════════╗
║  STAGE 1: PAGE CLASSIFICATION (PyMuPDF + ML)                                ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║   [Load PDF with PyMuPDF]                                                   ║
║            │                                                                ║
║            ▼                                                                ║
║   [Extract raw text from each page]                                         ║
║            │                                                                ║
║            ▼                                                                ║
║   [Preprocess text - lowercase, clean]                                      ║
║            │                                                                ║
║            ▼                                                                ║
║   [TF-IDF Vectorization]                                                    ║
║            │                                                                ║
║            ▼                                                                ║
║   [ML predicts category (LR or LR+RF)]                                      ║
║            │                                                                ║
║            ▼                                                                ║
║   [Group pages by category]                                                 ║
║                                                                             ║
╚═══════════════════════════════════╤═════════════════════════════════════════╝
                                    │
                                    ▼
╔═════════════════════════════════════════════════════════════════════════════╗
║  STAGE 1.5: HEADER KEYWORD MATCHING (Validation)                            ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║   [Check page headers for category keywords]                                ║
║            │                                                                ║
║            ▼                                                                ║
║   [Filter out pages without matching headers]                               ║
║                                                                             ║
╚═══════════════════════════════════╤═════════════════════════════════════════╝
                                    │
                                    ▼
╔═════════════════════════════════════════════════════════════════════════════╗
║  STAGE 2: SMART SPLITTING (PyMuPDF)                                         ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║   [Create sub-PDF for each category]                                        ║
║            │                                                                ║
║            ▼                                                                ║
║   [Only include relevant pages]  ◄── Reduces 300 pages to 2-25 pages       ║
║                                                                             ║
╚═══════════════════════════════════╤═════════════════════════════════════════╝
                                    │
                                    ▼
╔═════════════════════════════════════════════════════════════════════════════╗
║  STAGE 3: TABLE EXTRACTION (LlamaParse API)                                 ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║   [Send category sub-PDF to LlamaParse API]                                 ║
║            │                                                                ║
║            ▼                                                                ║
║   [Extract tables and content as markdown]                                  ║
║                                                                             ║
╚═══════════════════════════════════╤═════════════════════════════════════════╝
                                    │
                                    ▼
╔═════════════════════════════════════════════════════════════════════════════╗
║  OUTPUT FILES                                                               ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║   ┌────────────────┐  ┌────────────────┐                                    ║
║   │ BS_company.md  │  │ PL_company.md  │                                    ║
║   └────────────────┘  └────────────────┘                                    ║
║   ┌────────────────────────┐  ┌────────────────────┐                        ║
║   │ Cash_Flow_company.md   │  │ Notes_company.md   │                        ║
║   └────────────────────────┘  └────────────────────┘                        ║
║                                                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝
```

### Tool Responsibilities

| Stage | Tool | What It Does |
|-------|------|--------------|
| **Stage 1** | **PyMuPDF** | Opens PDF, extracts raw text from each page for ML classification |
| **Stage 1** | **TF-IDF + ML** | Converts text to features, predicts page category (LR or LR+RF ensemble) |
| **Stage 1.5** | **Header Matching** | Validates pages by checking headers for category keywords |
| **Stage 2** | **PyMuPDF** | Creates smaller sub-PDFs containing only relevant category pages |
| **Stage 3** | **LlamaParse API** | Converts sub-PDF to structured markdown with proper tables |

---

## How We Save LlamaParse API Time

### The Optimization Strategy

**Without ML (Naive Approach):**
- Send entire 300+ page PDF to LlamaParse
- API processes ALL pages including irrelevant content
- High API cost and long processing time

**With ML (Our Approach):**
- ML classifies pages first using PyMuPDF (fast, local, free)
- Create small sub-PDFs with only relevant pages (e.g., 2-4 pages for Balance Sheet)
- Send only small sub-PDFs to LlamaParse API
- **Result: 90%+ reduction in API calls and processing time**

### Example Savings

| Category | Pages in Full PDF | Pages After ML Filter | Reduction |
|----------|-------------------|----------------------|-----------|
| Balance Sheet | 300+ | 2 | 99% |
| Cash Flow | 300+ | 4 | 98% |
| Notes | 300+ | ~25 | 92% |

**Key Insight:** PyMuPDF handles page classification locally (free, fast), LlamaParse only processes the filtered pages (expensive, accurate).

---

## Real Output Samples

### Balance Sheet Output

**File:** `BS_eternal.md`  
**Source:** eternal.pdf  
**Pages Identified:** [185, 297]

---

# Consolidated Balance Sheet
## as at March 31, 2025

| Particulars                                        | Note  | As at March 31, 2025 | As at March 31, 2024 |
| -------------------------------------------------- | ----- | -------------------- | -------------------- |
| Assets                                             |       |                      |                      |
| Non-current assets                                 |       |                      |                      |
| Property, plant and equipment                      | 3     | 965                  | 287                  |
| Capital work-in-progress                           | 3     | 51                   | 18                   |
| Right-of-use assets                                | 31    | 1,918                | 690                  |
| Goodwill                                           | 4     | 5,737                | 4,717                |
| Other intangible assets                            | 4     | 912                  | 754                  |
| Investments                                        | 5     | 10,920               | 10,365               |
| Other financial assets                             | 10    | 2,744                | 747                  |
| Tax assets (net)                                   | 11    | 129                  | 221                  |
| Other non-current assets                           | 12    | 546                  | 99                   |
| **Total non-current assets**                       |       | **23,922**           | **17,898**           |
| Current assets                                     |       |                      |                      |
| Inventories                                        | 13    | 176                  | 88                   |
| Investments                                        | 6     | 2,272                | 1,280                |
| Trade receivables                                  | 7     | 1,946                | 794                  |
| Cash and cash equivalents                          | 8     | 666                  | 309                  |
| Bank balances other than cash and cash equivalents | 9     | 2,948                | 422                  |
| Other financial assets                             | 10    | 2,769                | 2,324                |
| Other current assets                               | 12    | 924                  | 241                  |
| **Total current assets**                           |       | **11,701**           | **5,458**            |
| **Total assets**                                   |       | **35,623**           | **23,356**           |
| Equity                                             |       |                      |                      |
| Equity share capital                               | 14(a) | 907                  | 868                  |
| Other equity                                       | 14(b) | 29,410               | 19,545               |
| **Total equity**                                   |       | **30,310**           | **20,406**           |

---

### Cash Flow Statement Output

**File:** `Cash_Flow_eternal.md`  
**Source:** eternal.pdf  
**Pages Identified:** [193, 194, 305, 306]

---

# Consolidated Statement of Cash Flows
## for the year ended March 31, 2025

| Particulars                                                                           | FY 2025 | FY 2024 |
| ------------------------------------------------------------------------------------- | ------- | ------- |
| **A) Cash flows from operating activities**                                           |         |         |
| Profit / (loss) before tax                                                            | 697     | 291     |
| Depreciation on property, plant and equipment                                         | 576     | 284     |
| Amortisation on intangible assets                                                     | 287     | 242     |
| Provision for doubtful debts and advances                                             | 71      | 68      |
| Share-based payment expense                                                           | 798     | 515     |
| Interest income on debentures or bonds                                                | (436)   | (320)   |
| Interest on lease liabilities                                                         | 147     | 67      |
| Operating profit before working capital changes                                       | 1,519   | 633     |
| Trade receivables                                                                     | (1,117) | (348)   |
| Trade payables                                                                        | 629     | 211     |
| **Net cash from operating activities (A)**                                            | **308** | **646** |
| **B) Cash flows from investing activities**                                           |         |         |
| Purchase of property, plant and equipment                                             | (936)   | (215)   |
| Proceeds from redemption of mutual fund units                                         | 46,738  | 29,509  |
| Investment in mutual fund units                                                       | (47,326)| (27,010)|
| Acquisition of businesses, net of cash acquired                                       | (2,005) | -       |
| Interest received                                                                     | 819     | 618     |
| **Net cash from investing activities (B)**                                            | **(7,993)** | **(347)** |
| **C) Cash flows from financing activities**                                           |         |         |
| Proceeds from issue of equity shares                                                  | 8,501   | 23      |
| Payment of lease liabilities                                                          | (258)   | (129)   |
| **Net cash from financing activities (C)**                                            | **8,042** | **(207)** |
| **Net increase in cash and cash equivalents (A+B+C)**                                 | **357** | **92**  |
| Cash and cash equivalents at beginning of the year                                    | 309     | 218     |
| **Cash and cash equivalents at end of the year**                                      | **666** | **309** |

---

## Key Benefits

| Benefit | Description |
|---------|-------------|
| **Automated** | No manual page searching required |
| **Cost Efficient** | ML reduces LlamaParse API usage by 90%+ |
| **Accurate** | ML trained on financial documents + header validation |
| **Flexible** | Single model (fast) or ensemble (high recall) modes |
| **Structured** | Clean markdown tables ready for analysis |
| **Traceable** | Each file shows source page numbers |

---

## Technology Stack

| Component | Purpose |
|-----------|---------|
| **Logistic Regression** | Fast, accurate page classification (Single_model.py) |
| **Random Forest Classifier** | Higher coverage classification (used in ensemble) |
| **TF-IDF Vectorizer** | Converts text to numerical ML features |
| **PyMuPDF (fitz)** | PDF text extraction and page splitting (local, fast) |
| **LlamaParse** | High-quality table extraction to markdown (API) |

---

## Project Structure

```
Fin-LLM-NFRA/
├── Preprocessing/
│   ├── Single_model.py       # Single LR model processing
│   ├── category_segmentation.py  # Ensemble (LR+RF) processing
│   └── utils.py              # Shared utilities
├── ML_MODELS/
│   ├── LR_NFRA_vectorizer.pkl    # TF-IDF for LR model
│   ├── LR_NFRA_CLASSIFIER.pkl    # Logistic Regression model
│   ├── RF_tfidf_vectorizer.pkl   # TF-IDF for RF model
│   └── RF_CLASSIFIER.pkl         # Random Forest model
├── output/                   # Generated markdown files
├── requirements.txt
└── README.md
```

---

## Environment Variables

Create a `.env` file in the project root:

```
LLAMA_CLOUD_API_KEY=your_api_key_here
```

Get your API key from [LlamaIndex Cloud](https://cloud.llamaindex.ai/)

---
