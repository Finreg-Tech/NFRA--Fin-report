# NFRA Financial Statement Compliance Validation System

## Complete Architecture & Workflow Documentation

**Document Version:** 1.0  
**Last Updated:** February 18, 2026
 
---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [High-Level Architecture](#2-high-level-architecture)
3. [System Components](#3-system-components)
4. [Multi-Agent Workflow](#4-multi-agent-workflow)
5. [Data Flow Architecture](#5-data-flow-architecture)
6. [Service Layer Details](#6-service-layer-details)
7. [API Layer](#7-api-layer)
8. [RAG Pipeline](#8-rag-pipeline)
9. [Database Schema](#9-database-schema)
10. [Configuration Management](#10-configuration-management)
11. [State Management](#11-state-management)
12. [Workflow Diagrams](#12-workflow-diagrams)
13. [Technology Stack](#13-technology-stack)
14. [Deployment Architecture](#14-deployment-architecture)

---

## 1. Executive Summary

The **NFRA (National Financial Reporting Authority) Compliance Validation System** is an AI-powered multi-agent platform designed to automatically validate Indian financial statements against **Ind AS (Indian Accounting Standards)** compliance requirements.

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **PDF Processing** | ML-based page classification + LlamaParse extraction |
| **Data Extraction** | LLM-powered structured JSON extraction from financial tables |
| **Mathematical Validation** | Automated accounting equation verification |
| **Compliance Checking** | Knowledge Graph + RAG-based Ind AS verification |
| **Risk Assessment** | Financial health indicators and red flag detection |
| **Report Generation** | Professional compliance reports with grades |

### Input/Output

```
INPUT:  Annual Report PDF (Financial Statements)
OUTPUT: Structured JSON + Markdown Compliance Report
```

---

## 2. High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Streamlit Web App]
    end
    
    subgraph "API Layer"
        API[FastAPI Server]
        Routes[API Routes]
    end
    
    subgraph "Orchestration Layer"
        LG[LangGraph Workflow Engine]
        SM[State Manager]
    end
    
    subgraph "Agent Layer"
        GK[Gatekeeper Agent]
        QT[Quant Agent]
        AC[Accountant Agent]
        AU[Auditor Agent]
        PB[Publisher Agent]
    end
    
    subgraph "Service Layer"
        EXT[Extraction Service]
        RAG[RAG Service]
        DB[Database Service]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL + pgvector)]
        KG[Knowledge Graph JSON]
        PRO[Prompt Templates]
    end
    
    subgraph "External Services"
        OAI[OpenAI GPT-4o]
        LP[LlamaParse API]
        EMB[Sentence Transformers]
    end
    
    UI --> API
    API --> Routes
    Routes --> LG
    LG --> SM
    SM --> GK --> QT --> AC --> AU --> PB
    
    GK --> EXT
    GK --> LP
    EXT --> OAI
    AC --> RAG
    AC --> KG
    AU --> OAI
    RAG --> PG
    RAG --> EMB
    DB --> PG
```

---

## 3. System Components

### 3.1 Directory Structure

```
Fin-LLM-NFRA/
├── config/                      # Configuration management
│   ├── __init__.py
│   ├── logging.py              # Logging configuration
│   └── settings.py             # Application settings
│
├── resources/                   # Static resources
│   ├── models/                 # ML models (classifiers)
│   │   ├── LR_NFRA_CLASSIFIER.pkl
│   │   └── LR_NFRA_vectorizer.pkl
│   └── prompts/                # LLM prompts & templates
│       ├── BS.j2               # Balance Sheet extraction prompt
│       ├── PL.j2               # Profit & Loss extraction prompt
│       ├── CF.j2               # Cash Flow extraction prompt
│       ├── knowledge_graph.json # Ind AS mapping
│       └── prompts.py          # Agent prompts
│
├── src/                        # Source code
│   ├── api/                    # API layer
│   │   ├── server.py           # FastAPI application
│   │   └── routes/             # API endpoints
│   │       ├── ingest.py       # Document ingestion
│   │       ├── nfra_query.py   # NFRA rule queries
│   │       └── rag_query.py    # RAG search endpoints
│   │
│   ├── core/                   # Core business logic
│   │   ├── state.py            # AgentState definitions
│   │   ├── workflow.py         # LangGraph workflow
│   │   └── agents/             # Multi-agent implementations
│   │       ├── gatekeeper.py   # PDF extraction agent
│   │       ├── quant.py        # Math validation agent
│   │       ├── accountant.py   # Compliance agent
│   │       ├── auditor.py      # Risk assessment agent
│   │       └── publisher.py    # Report generation agent
│   │
│   ├── services/               # Service layer
│   │   ├── database/           # Database operations
│   │   │   ├── db_config.py    # Connection config
│   │   │   ├── db_init.py      # Schema initialization
│   │   │   └── models.py       # Query operations
│   │   │
│   │   ├── extraction/         # Data extraction
│   │   │   └── llm/            # LLM-based extraction
│   │   │       ├── extractor.py    # PDF → Markdown
│   │   │       ├── normalizer.py   # Text normalization
│   │   │       ├── pipeline.py     # LLM processing
│   │   │       └── schemas.py      # Pydantic schemas
│   │   │
│   │   └── rag/                # RAG operations
│   │       ├── embedding_service.py   # Vector embeddings
│   │       ├── ingestion_service.py   # Document ingestion
│   │       ├── rag_service.py         # RAG search
│   │       ├── retrieval_service.py   # Rule retrieval
│   │       └── pdf_parser.py          # PDF parsing
│   │
│   └── utils/                  # Utility functions
│       └── preprocessing.py
│
├── Streamlit/                  # Frontend application
│   └── app.py                  # Streamlit UI
│
├── REPORT/                     # Generated reports
├── results/                    # Extraction results
└── tests/                      # Test suite
```

---

## 4. Multi-Agent Workflow

### 4.1 Agent Overview

```mermaid
flowchart TD
    subgraph "START"
        A[📄 PDF Upload]
    end
    
    subgraph "GATEKEEPER"
        B[Extract Metadata<br/>CIN, FY, Company]
        C[ML Page Classification<br/>BS, PL, CF, Notes]
        D[LlamaParse Extraction<br/>PDF → Markdown]
        E[LLM JSON Structuring<br/>Markdown → JSON]
        F[Schema Validation]
    end
    
    subgraph "QUANT"
        G[Accounting Equation<br/>Assets = E + L]
        H[Vertical Consistency<br/>Row Sums = Totals]
        I[Horizontal Analysis<br/>YoY Variance]
        J[Ratio Calculations]
    end
    
    subgraph "ACCOUNTANT"
        K[Knowledge Graph<br/>Line Item → Ind AS]
        L[RAG Retrieval<br/>Fetch Rules from DB]
        M[LLM Compliance Check<br/>Data vs Rules]
    end
    
    subgraph "AUDITOR"
        N[Quantitative Analysis<br/>Liquidity, Solvency]
        O[Qualitative Analysis<br/>Red Flags, Going Concern]
        P[Risk Scoring]
    end
    
    subgraph "PUBLISHER"
        Q[Calculate Score]
        R[Generate Markdown<br/>Report]
        S[Save to REPORT/]
    end
    
    subgraph "END"
        T[📊 Compliance Report]
    end
    
    A --> B --> C --> D --> E --> F
    F --> G --> H --> I --> J
    J --> K --> L --> M
    M --> N --> O --> P
    P --> Q --> R --> S --> T
```

### 4.2 Agent Responsibilities

| Agent | Type | Responsibilities | LLM Required |
|-------|------|------------------|--------------|
| **Gatekeeper** | Extraction | PDF parsing, page classification, JSON structuring | ✅ Yes |
| **Quant** | Validation | Mathematical checks, ratio analysis | ❌ No |
| **Accountant** | Compliance | Ind AS rule verification, disclosure checks | ✅ Yes |
| **Auditor** | Risk | Financial health assessment, red flag detection | ✅ Yes |
| **Publisher** | Output | Score calculation, report generation | ❌ No |

---

## 5. Data Flow Architecture

### 5.1 Complete Data Flow

```mermaid
flowchart LR
    subgraph "Input"
        PDF[📄 PDF File]
    end
    
    subgraph "Extraction Pipeline"
        ML[ML Classifier]
        LP[LlamaParse]
        LLM1[GPT-4o<br/>JSON Structuring]
    end
    
    subgraph "State Store"
        ST[AgentState<br/>TypedDict]
    end
    
    subgraph "Validation"
        QV[Quant<br/>Validation]
        CV[Compliance<br/>Validation]
        RV[Risk<br/>Validation]
    end
    
    subgraph "Knowledge Base"
        KG[Knowledge<br/>Graph]
        VDB[(Vector DB<br/>pgvector)]
    end
    
    subgraph "Output"
        REP[📊 Compliance<br/>Report]
        JSON[📋 JSON<br/>Data]
    end
    
    PDF --> ML --> LP --> LLM1
    LLM1 --> ST
    ST --> QV --> ST
    ST --> CV
    KG --> CV
    VDB --> CV
    CV --> ST
    ST --> RV --> ST
    ST --> REP
    ST --> JSON
```

### 5.2 AgentState Structure

```python
class AgentState(TypedDict):
    # Input
    file_path: str                              # Path to uploaded PDF
    
    # Gatekeeper Outputs
    metadata: MetadataState                     # CIN, FY, Company Name
    extracted_data: Dict[str, Any]              # BS, PL, CF JSON data
    markdown_content: Dict[str, str]            # Raw markdown for notes lookup
    
    # Validation Results
    validation_results: ValidationResultsState  # Errors, flags, alerts
    
    # RAG Context
    rag_context: List[Dict[str, Any]]           # Retrieved rules
    
    # Publisher Outputs
    final_report: Dict[str, Any]                # Complete report
    final_report_path: Optional[str]            # Saved file path
    
    # Status
    processing_status: str                      # "initialized" → "completed"
```

---

## 6. Service Layer Details

### 6.1 Extraction Service

```mermaid
flowchart TD
    subgraph "PDF Processing"
        A[PDF Input]
        B[PyMuPDF Page Iteration]
        C[ML Classification<br/>LogisticRegression]
    end
    
    subgraph "Page Categories"
        D[Balance Sheet Pages]
        E[Profit & Loss Pages]
        F[Cash Flow Pages]
        G[Notes Pages]
    end
    
    subgraph "Markdown Extraction"
        H[Create Category PDF]
        I[LlamaParse API]
        J[Markdown Output]
    end
    
    subgraph "JSON Structuring"
        K[Load Jinja2 Prompt]
        L[GPT-4o Processing]
        M[Pydantic Validation]
        N[Structured JSON]
    end
    
    A --> B --> C
    C --> D & E & F & G
    D & E & F --> H --> I --> J
    J --> K --> L --> M --> N
```

#### Key Components:

1. **ML Page Classifier** (`extractor.py`)
   - Uses LogisticRegression + TF-IDF
   - Classifies pages into: BS, PL, Cash Flow, Notes, Others
   - Header keyword matching for refinement

2. **LlamaParse Integration** (`extractor.py`)
   - Converts PDF pages to Markdown tables
   - Parallel processing with ThreadPoolExecutor
   - Handles table structures accurately

3. **LLM JSON Pipeline** (`pipeline.py`)
   - Uses Jinja2 prompt templates
   - GPT-4o for structured extraction
   - Pydantic schema validation

### 6.2 RAG Service

```mermaid
flowchart TD
    subgraph "Ingestion Pipeline"
        A[PDF Document]
        B[Text/Markdown Extraction]
        C[Section Splitting]
        D[Batch Embedding<br/>MiniLM-L6-v2]
        E[Insert to PostgreSQL]
    end
    
    subgraph "Retrieval Pipeline"
        F[Query Input]
        G[Query Embedding]
        H{Hybrid Search?}
        I[Vector Search<br/>Cosine Similarity]
        J[Text Search<br/>Full-text Match]
        K[Score Combination<br/>alpha weighting]
        L[Results]
    end
    
    A --> B --> C --> D --> E
    F --> G --> H
    H -->|Yes| I & J --> K --> L
    H -->|No| I --> L
```

#### Search Modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| **Vector Search** | Cosine similarity on embeddings | Semantic meaning |
| **Text Search** | PostgreSQL full-text search | Exact matches |
| **Hybrid Search** | Weighted combination (α) | Best of both |

### 6.3 Database Service

```mermaid
erDiagram
    RULES {
        int id PK
        text document_type "IndAS, SEBI, RBI"
        text standard_code "Ind AS 16, etc."
        int standard_number
        text standard_name
        text section_name
        int section_order
        int page_number
        text chunk
        text actual_text
        vector embedding "384 dimensions"
    }
```

---

## 7. API Layer

### 7.1 API Endpoints

```mermaid
flowchart LR
    subgraph "FastAPI Server"
        A[/health]
        B[/validate_report]
        C[/NFRA]
        D[/ingest]
        E[/NFRA-QUERY]
        F[/rag-query]
        G[/semantic-search]
    end
    
    subgraph "Functions"
        A1[Health Check]
        B1[Run Validation Chain]
        C1[Extract Financials]
        D1[Ingest Documents]
        E1[Query Rules DB]
        F1[Hybrid RAG Search]
        G1[Vector Search Only]
    end
    
    A --> A1
    B --> B1
    C --> C1
    D --> D1
    E --> E1
    F --> F1
    G --> G1
```

### 7.2 Endpoint Details

| Endpoint | Method | Purpose | Input | Output |
|----------|--------|---------|-------|--------|
| `/health` | GET | Health check | None | `{"status": "healthy"}` |
| `/validate_report` | POST | Full validation pipeline | PDF file | Compliance report JSON |
| `/NFRA` | POST | Extract only (no validation) | PDF file | Structured JSON |
| `/ingest` | POST | Ingest regulatory documents | PDF + type | Insertion count |
| `/NFRA-QUERY` | POST | Query rules database | Filters | Rule documents |
| `/rag-query` | POST | Semantic + hybrid search | Query text | Ranked results |

---

## 8. RAG Pipeline

### 8.1 Document Ingestion Flow

```mermaid
sequenceDiagram
    participant User
    participant API as /ingest
    participant Parser as PDF Parser
    participant Splitter as Section Splitter
    participant Embedder as Embedding Service
    participant DB as PostgreSQL

    User->>API: POST PDF + document_type
    API->>Parser: Extract full text
    Parser->>Splitter: Parse into sections
    Splitter->>Embedder: Generate embeddings (batch)
    Embedder->>DB: INSERT rules with vectors
    DB-->>API: Return count
    API-->>User: {"sections_inserted": N}
```

### 8.2 Rule Retrieval Flow

```mermaid
sequenceDiagram
    participant Agent as Accountant Agent
    participant KG as Knowledge Graph
    participant Retriever as Retrieval Service
    participant DB as PostgreSQL
    participant LLM as GPT-4o

    Agent->>KG: Lookup line item mapping
    KG-->>Agent: Return Ind AS standard code
    Agent->>Retriever: retrieve_rules(standard_code)
    Retriever->>DB: Query by standard_code
    DB-->>Retriever: Return rule documents
    Retriever-->>Agent: Rule context
    Agent->>LLM: Compliance check prompt
    LLM-->>Agent: PASS/FAIL with reasoning
```

### 8.3 Embedding Configuration

| Parameter | Value |
|-----------|-------|
| **Model** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Dimensions** | 384 |
| **Index Type** | IVFFlat (pgvector) |
| **Distance Metric** | Cosine Similarity |

---

## 9. Database Schema

### 9.1 Complete Schema

```sql
-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Rules table for regulatory documents
CREATE TABLE rules (
    id SERIAL PRIMARY KEY,
    document_type TEXT NOT NULL,        -- 'IndAS', 'SEBI', 'RBI', 'CompanyAct'
    standard_code TEXT NOT NULL,        -- 'Ind AS 16', 'SEBI LODR', etc.
    standard_number INTEGER,            -- Numeric identifier
    standard_name TEXT,                 -- Human-readable name
    section_name TEXT,                  -- Section/paragraph name
    section_order INTEGER,              -- Order within document
    page_number INTEGER,                -- Source page number
    chunk TEXT,                         -- Chunked text for context
    actual_text TEXT,                   -- Full section text
    embedding vector(384)               -- Sentence embeddings
);

-- Vector similarity index
CREATE INDEX rules_embedding_idx 
ON rules USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### 9.2 Vector Search Query

```sql
SELECT 
    id, document_type, standard_code, section_name, actual_text,
    1 - (embedding <=> :query_embedding::vector) as similarity
FROM rules
WHERE embedding IS NOT NULL
    AND document_type = :document_type
ORDER BY embedding <=> :query_embedding::vector
LIMIT :top_k;
```

---

## 10. Configuration Management

### 10.1 Settings Overview

```python
# config/settings.py

# Directory Paths
BASE_DIR = Path(__file__).parent.parent
ML_MODELS_DIR = BASE_DIR / "resources" / "models"
PROMPTS_DIR = BASE_DIR / "resources" / "prompts"
KNOWLEDGE_GRAPH_PATH = PROMPTS_DIR / "knowledge_graph.json"

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB

# LLM Configuration
OPENAI_API_KEY = env("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o"
OPENAI_TEMPERATURE = 0

# Processing Configuration
MAX_LLAMAPARSE_WORKERS = 3
LLM_RETRY_COUNT = 2

# ML Models
ML_VECTORIZER_PATH = ML_MODELS_DIR / "LR_NFRA_vectorizer.pkl"
ML_CLASSIFIER_PATH = ML_MODELS_DIR / "LR_NFRA_CLASSIFIER.pkl"
```

### 10.2 Environment Variables

```env
# Required
OPENAI_API_KEY=sk-...
LLAMA_CLOUD_API_KEY=llx-...
DATABASE_URL=postgresql://user:pass@host:5432/nfra_db

# Optional
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
MAX_FILE_SIZE_BYTES=52428800
```

---

## 11. State Management

### 11.1 Complete State Schema

```mermaid
classDiagram
    class AgentState {
        +str file_path
        +MetadataState metadata
        +Dict extracted_data
        +Dict markdown_content
        +ValidationResultsState validation_results
        +List rag_context
        +Dict final_report
        +str processing_status
    }
    
    class MetadataState {
        +str cin
        +str company_name
        +str fy
        +str report_type
        +str period_end_date
    }
    
    class ValidationResultsState {
        +List~QuantError~ quant_errors
        +List~ComplianceFlag~ compliance_flags
        +List~RiskAlert~ risk_alerts
    }
    
    class QuantError {
        +str check_name
        +bool passed
        +float expected
        +float actual
        +float difference
        +str message
    }
    
    class ComplianceFlag {
        +str rule_id
        +str description
        +str severity
        +str evidence
        +str recommendation
    }
    
    class RiskAlert {
        +str risk_type
        +str indicator
        +float value
        +float threshold
        +str severity
        +str analysis
    }
    
    AgentState --> MetadataState
    AgentState --> ValidationResultsState
    ValidationResultsState --> QuantError
    ValidationResultsState --> ComplianceFlag
    ValidationResultsState --> RiskAlert
```

### 11.2 State Transitions

```mermaid
stateDiagram-v2
    [*] --> initialized: run_validation_chain()
    initialized --> extracting: Gatekeeper starts
    extracting --> validating_math: Gatekeeper done
    validating_math --> checking_compliance: Quant done
    checking_compliance --> assessing_risk: Accountant done
    assessing_risk --> generating_report: Auditor done
    generating_report --> completed: Publisher done
    completed --> [*]
    
    extracting --> failed: Extraction error
    validating_math --> failed: Math error
    checking_compliance --> failed: API error
    failed --> [*]
```

---

## 12. Workflow Diagrams

### 12.1 Main Validation Workflow

```mermaid
flowchart TB
    subgraph "Phase 1: Extraction"
        A[📄 PDF Upload] --> B[ML Page Classification]
        B --> C{Has Financial Statements?}
        C -->|No| X1[❌ Reject: Invalid PDF]
        C -->|Yes| D[LlamaParse Extraction]
        D --> E[GPT-4o JSON Structuring]
        E --> F[Schema Validation]
        F --> G{Schema Valid?}
        G -->|No| X2[❌ Error: Schema Mismatch]
        G -->|Yes| H[Store in AgentState]
    end
    
    subgraph "Phase 2: Mathematical Validation"
        H --> I[Accounting Equation Check]
        I --> J[Vertical Consistency Check]
        J --> K[Horizontal Variance Analysis]
        K --> L[Ratio Calculations]
        L --> M[Store Quant Errors]
    end
    
    subgraph "Phase 3: Compliance Validation"
        M --> N[For Each Line Item]
        N --> O[Knowledge Graph Lookup]
        O --> P{Ind AS Mapping Found?}
        P -->|No| N
        P -->|Yes| Q[RAG Rule Retrieval]
        Q --> R[LLM Compliance Check]
        R --> S[Store Compliance Flags]
        S --> N
    end
    
    subgraph "Phase 4: Risk Assessment"
        S --> T[Liquidity Analysis]
        T --> U[Solvency Analysis]
        U --> V[Profitability Analysis]
        V --> W[Cash Flow Analysis]
        W --> Y[LLM Qualitative Analysis]
        Y --> Z[Store Risk Alerts]
    end
    
    subgraph "Phase 5: Report Generation"
        Z --> AA[Calculate Overall Score]
        AA --> AB[Determine Grade]
        AB --> AC[Generate Markdown Report]
        AC --> AD[Save to REPORT/]
        AD --> AE[📊 Return Final Report]
    end
```

### 12.2 Gatekeeper Agent Detailed Flow

```mermaid
flowchart TD
    A[Start] --> B[Open PDF with PyMuPDF]
    B --> C[Extract First Page Text]
    C --> D[Extract Company Name<br/>Corporate Suffix Detection]
    D --> E[Extract CIN<br/>Regex Pattern]
    E --> F[Extract Financial Year<br/>Multiple Patterns]
    F --> G[Detect Report Type<br/>Annual/Quarterly/Half-Yearly]
    G --> H[Store Metadata in State]
    
    H --> I[Load ML Models<br/>Vectorizer + Classifier]
    I --> J[Classify Each Page]
    J --> K[Group Pages by Category<br/>BS, PL, CF, Notes]
    K --> L[Apply Header Keyword Filtering]
    
    L --> M[Create Category PDFs]
    M --> N[LlamaParse Parallel Processing]
    N --> O[Store Markdown per Category]
    
    O --> P[Load Jinja2 Prompts]
    P --> Q[Process Balance Sheet<br/>GPT-4o + Validation]
    P --> R[Process Profit & Loss<br/>GPT-4o + Validation]
    P --> S[Process Cash Flow<br/>GPT-4o + Validation]
    
    Q & R & S --> T[Validate Extraction Schema]
    T --> U{All Required Fields?}
    U -->|No| V[Raise SchemaValidationError]
    U -->|Yes| W[Store in State.extracted_data]
    W --> X[End - Return Updated State]
```

### 12.3 Quant Agent Validation Checks

```mermaid
flowchart LR
    subgraph "Check A: Accounting Equation"
        A1[Total Assets] --> A2{= Total Equity +<br/>Total Liabilities?}
        A2 -->|Pass| A3[✅]
        A2 -->|Fail| A4[❌ Record Error]
    end
    
    subgraph "Check B: Vertical Consistency"
        B1[Sum Asset Rows] --> B2{= Reported<br/>Total Assets?}
        B2 -->|Pass| B3[✅]
        B2 -->|Fail| B4[❌ Record Error]
    end
    
    subgraph "Check C: Horizontal Analysis"
        C1[Current Year Value] --> C2[Previous Year Value]
        C2 --> C3{Variance > 50%?}
        C3 -->|Yes| C4[⚠️ Record Warning]
        C3 -->|No| C5[✅]
    end
    
    subgraph "Check D: Cash Flow Reconciliation"
        D1[Opening Cash +<br/>Net Change] --> D2{= Closing Cash?}
        D2 -->|Pass| D3[✅]
        D2 -->|Fail| D4[❌ Record Error]
    end
```

### 12.4 Accountant Agent Compliance Flow

```mermaid
sequenceDiagram
    participant State as AgentState
    participant KG as Knowledge Graph
    participant DB as PostgreSQL
    participant LLM as GPT-4o
    
    loop For Each Balance Sheet Row
        State->>KG: Get Ind AS mapping for label
        KG-->>State: standard_code, standard_name
        
        alt Mapping Found
            State->>DB: retrieve_rules(standard_code)
            DB-->>State: Rule documents
            State->>State: Extract note_text from markdown
            
            State->>LLM: Compliance check prompt
            Note over LLM: Rule context + Line item data + Note text
            LLM-->>State: {status, evidence, reasoning}
            
            alt status == FAIL
                State->>State: Add ComplianceFlag(severity=high)
            else status == DATA_GAP
                State->>State: Add ComplianceFlag(severity=info)
            end
        end
    end
```

### 12.5 Publisher Scoring Algorithm

```mermaid
flowchart TD
    A[Start with Base Score = 100] --> B{Quant Errors?}
    B -->|Yes| C[Deduct 15 per error]
    B -->|No| D[Continue]
    C --> D
    
    D --> E{Compliance Flags?}
    E -->|Yes| F[Check Severity]
    E -->|No| G[Continue]
    
    F --> F1{High Severity?}
    F1 -->|Yes| F2[Deduct 10]
    F1 -->|No| F3{Medium Severity?}
    F3 -->|Yes| F4[Deduct 5]
    F3 -->|No| F5[Deduct 2]
    
    F2 & F4 & F5 --> G
    
    G --> H{Risk Alerts?}
    H -->|Yes| I[Check Risk Level]
    H -->|No| J[Calculate Final Score]
    
    I --> I1{Critical/High?}
    I1 -->|Yes| I2[Deduct 15]
    I1 -->|No| I3[Deduct 5]
    I2 & I3 --> J
    
    J --> K[Clamp Score 0-100]
    K --> L{Score >= 85?}
    L -->|Yes| M[Grade A]
    L -->|No| N{Score >= 70?}
    N -->|Yes| O[Grade B]
    N -->|No| P{Score >= 55?}
    P -->|Yes| Q[Grade C]
    P -->|No| R{Score >= 40?}
    R -->|Yes| S[Grade D]
    R -->|No| T[Grade F]
```

---

## 13. Technology Stack

### 13.1 Complete Stack

```mermaid
graph TB
    subgraph "Frontend"
        ST[Streamlit 1.x]
    end
    
    subgraph "Backend Framework"
        FA[FastAPI]
        UV[Uvicorn ASGI]
    end
    
    subgraph "AI/ML Stack"
        LG[LangGraph]
        LC[LangChain]
        OAI[OpenAI GPT-4o]
        LP[LlamaParse]
        ST2[Sentence Transformers]
        SK[scikit-learn]
    end
    
    subgraph "Data Processing"
        PM[PyMuPDF / fitz]
        PD[Pydantic]
        JL[Joblib]
        J2[Jinja2]
    end
    
    subgraph "Database"
        PG[PostgreSQL 15+]
        PGV[pgvector Extension]
        PSY[psycopg2]
    end
    
    subgraph "Infrastructure"
        PY[Python 3.11+]
        DOT[python-dotenv]
    end
```

### 13.2 Key Dependencies

| Category | Package | Purpose |
|----------|---------|---------|
| **Web Framework** | FastAPI | REST API server |
| **AI Orchestration** | LangGraph | Multi-agent workflow |
| **LLM** | langchain-openai | GPT-4o integration |
| **PDF Parsing** | llama-parse | Table extraction |
| **PDF Processing** | PyMuPDF | Page manipulation |
| **Embeddings** | sentence-transformers | Vector generation |
| **Vector DB** | pgvector | Similarity search |
| **ML** | scikit-learn | Page classification |
| **Validation** | Pydantic | Schema validation |
| **Frontend** | Streamlit | Web UI |

---

## 14. Deployment Architecture

### 14.1 Local Development

```mermaid
flowchart LR
    subgraph "Developer Machine"
        APP[FastAPI App<br/>Port 8000]
        UI[Streamlit UI<br/>Port 8501]
        DB[(PostgreSQL<br/>Port 5432)]
    end
    
    subgraph "External APIs"
        OAI[OpenAI API]
        LP[LlamaParse API]
    end
    
    UI --> APP
    APP --> DB
    APP --> OAI
    APP --> LP
```

### 14.2 Production Architecture

```mermaid
flowchart TB
    subgraph "Load Balancer"
        LB[Nginx / ALB]
    end
    
    subgraph "Application Tier"
        API1[API Instance 1]
        API2[API Instance 2]
        API3[API Instance N]
    end
    
    subgraph "Database Tier"
        PG[(PostgreSQL<br/>Primary)]
        PGR[(PostgreSQL<br/>Replica)]
    end
    
    subgraph "Cache Layer"
        RD[Redis Cache]
    end
    
    subgraph "External Services"
        OAI[OpenAI API]
        LP[LlamaParse API]
    end
    
    LB --> API1 & API2 & API3
    API1 & API2 & API3 --> PG
    PG --> PGR
    API1 & API2 & API3 --> RD
    API1 & API2 & API3 --> OAI & LP
```

### 14.3 Container Architecture

```dockerfile
# Dockerfile example
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Appendix A: Knowledge Graph Structure

```json
{
  "financial_statement_mapping": {
    "balance_sheet": {
      "property_plant_and_equipment": {
        "standard_code": "Ind AS 16",
        "standard_name": "Property, Plant and Equipment",
        "rag_query_keywords": ["recognition criteria", "measurement", "depreciation"],
        "related_standards": ["Ind AS 36", "Ind AS 23"]
      },
      "trade_receivables": {
        "standard_code": "Ind AS 109",
        "standard_name": "Financial Instruments",
        "rag_query_keywords": ["impairment", "expected credit loss"],
        "related_standards": ["Ind AS 115"]
      }
      // ... more mappings
    },
    "profit_and_loss": {
      "revenue": {
        "standard_code": "Ind AS 115",
        "standard_name": "Revenue from Contracts with Customers",
        "rag_query_keywords": ["performance obligations", "transaction price"]
      }
      // ... more mappings
    }
  }
}
```

---

## Appendix B: API Response Schemas

### Validation Report Response

```json
{
  "metadata": {
    "company_name": "ABC Limited",
    "cin": "L55200MH1967PLC013837",
    "fy": "2024-25",
    "report_type": "Annual Report"
  },
  "assessment": {
    "overall_score": 82,
    "grade": "B",
    "status": "Conditionally Compliant"
  },
  "summary": {
    "total_checks": 45,
    "passed": 38,
    "failed": 4,
    "warnings": 3
  },
  "validation_results": {
    "quant_errors": [...],
    "compliance_flags": [...],
    "risk_alerts": [...]
  }
}
```

---

## Appendix C: Prompt Templates

### Balance Sheet Extraction Prompt (BS.j2)

```jinja
You are a financial statement structuring engine.

Convert the Markdown Balance Sheet into structured JSON with FIXED schema.

CRITICAL EXTRACTION RULES:
1. Extract EVERY single line item from the table
2. Do NOT skip any row
3. Continue parsing until the ABSOLUTE END

SECTION CLASSIFICATION:
- "assets": All asset items
- "equity": Share capital, reserves
- "liabilities": Borrowings, payables

OUTPUT SCHEMA:
{
  "statement_type": "balance_sheet",
  "category": "standalone | consolidated",
  "metadata": {...},
  "rows": [{...}],
  "totals": {...}
}
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-18 | System | Initial documentation |

---

*This document is auto-generated and should be updated when significant architectural changes are made.*
