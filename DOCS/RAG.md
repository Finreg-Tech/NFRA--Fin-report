---

# NFRA Deterministic Rule Engine — Implementation Instruction

---

## Objective

The goal of this implementation is to:

1. Convert the existing RAG system to a deterministic metadata engine.
2. Remove all embedding and similarity logic.
3. Add an `/ingest` endpoint.
4. Add an `/NFRA-QUERY` endpoint.
5. Move all database-related logic into the `DB/` folder.
6. Automatically create the database and tables from `.env` configuration.
7. Eliminate all vector operations.
8. Maintain a clean, modular architecture.

---

## Project Structure

```
api/
    main.py
    ingest.py
    nfra_query.py

rag/
    pdf_parser.py
    section_splitter.py
    ingestion_service.py
    retrieval_service.py

DB/
    db_config.py
    db_init.py
    models.py

.env
```

Database logic must not be placed inside the `rag/` folder. All database logic stays inside `DB/`.

---

## Database Configuration

### 1. Environment Variables

The `.env` file must contain the following:

```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=nfra_db
```

`python-dotenv` is used to load these environment variables.

---

### 2. Database Auto-Creation Logic

In `DB/db_init.py`, the following sequence runs on application startup:

1. Connect to the default `postgres` database.
2. Check whether `DB_NAME` exists.
3. If it does not exist, create it.
4. Connect to the created database.
5. Create tables automatically if they do not already exist.

Database creation statement:

```sql
CREATE DATABASE nfra_db;
```

Table creation statement:

```sql
CREATE TABLE IF NOT EXISTS rules (
    id SERIAL PRIMARY KEY,
    document_type TEXT NOT NULL,
    standard_code TEXT NOT NULL,
    standard_number INTEGER,
    standard_name TEXT,
    section_name TEXT,
    section_order INTEGER,
    chunk TEXT,
    actual_text TEXT
);
```

This must execute automatically when the application starts.

---

## 3. Vector Logic as an Enhanced Alternative

While the current implementation relies on deterministic keyword-based metadata filtering, vector logic represents a more advanced alternative that can be considered for improved retrieval performance in future iterations.

If vector logic is adopted, the following components must be accounted for in the system design:

- Embedding generation
- pgvector usage
- Similarity search
- RRF (Reciprocal Rank Fusion) ranking
- Vector columns
- Vector indexes

The deterministic approach described in this document serves as the baseline implementation. Vector operations, when layered on top, can enhance recall for queries where exact metadata matches are insufficient.

---

## 4. Ingest Endpoint

**Route:**

```
POST /ingest
```

**Input:**

- `file`: PDF (multipart/form-data)
- `rules`: one of `IndAS`, `SEBI`, `RBI`, or `CompanyAct`

**Ingestion Flow:**

1. Use PyMuPDF to open the file:

```python
import fitz
doc = fitz.open(file)
```

2. Extract text page by page.

3. Detect the standard header using the following pattern:

```
Ind AS \d+,
```

4. Extract the following fields:
   - `standard_code`
   - `standard_number`
   - `standard_name`

5. Detect sections using title-style detection.

6. Chunk content strictly according to the following hierarchy:

```
Standard → Section → Full Section Text
```

One database row per section. Token-based chunking and similarity logic are not used.

7. Insert records using the DB service inside `DB/`.

**Response:**

```json
{
  "message": "Ingestion successful",
  "sections_inserted": <count>
}
```

---

## 5. NFRA Query Endpoint

**Route:**

```
POST /NFRA-QUERY
```

**Input JSON:**

```json
{
  "document_type": "IndAS",
  "standard_code": "Ind AS 21",
  "standard_number": 21,
  "section_name": "Functional currency",
  "section_order": 2
}
```

`document_type` and `standard_code` are mandatory. The remaining fields are optional.

**Retrieval Logic:**

1. Validate that `document_type` and `standard_code` are present in the request.
2. Build a dynamic SQL query starting with:

```sql
WHERE document_type = ?
AND standard_code = ?
```
Optional filters are appended if the corresponding fields are provided.

3. Return rows containing the following fields:

```
document_type
standard_code
standard_number
standard_name
section_name
section_order
chunk
actual_text
```

No ranking, similarity, or embeddings are used. The retrieval is purely deterministic SQL filtering.

---

## 6. DB Service Design

### db_config.py

- Loads the `.env` file.
- Creates the database engine and connection pool.

### db_init.py

- Creates the database if it does not exist.
- Creates tables if they do not exist.
- Runs automatically on application startup.

### models.py

- Defines the `rules` table schema.
- Provides an insert function.
- Provides a query function.

Routes must call database functions from the `DB/` folder exclusively.

---

## 7. Application Startup Behavior

When the application runs, the startup sequence is as follows:

1. Load environment variables.
2. Initialize the database.
3. Create the database if it does not exist.
4. Create tables if they do not exist.
5. Start the FastAPI application.

---

## Expected Final Flow

**Ingestion:**

```
Upload PDF
→ Extract text
→ Detect standard
→ Detect sections
→ Store in DB
```

**Retrieval:**

```
POST /NFRA-QUERY
→ SQL filter
→ Return rule sections
```

---

## Success Criteria

- Database is auto-created on startup.
- Tables are auto-created on startup.
- Architecture is clean and modular.
- Ingestion endpoint functions correctly.
- Metadata filtering endpoint functions correctly.
