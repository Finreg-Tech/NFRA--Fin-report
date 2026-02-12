import os
import re
import time
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import fitz
import joblib
from llama_parse import LlamaParse
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
ML_MODELS_DIR = BASE_DIR.parent / "ML_MODELS"
RESULTS_DIR = BASE_DIR.parent / "results"

HEADER_KEYWORDS = {
    "BS": ["balance sheet", "statement of assets and liabilities"],
    "PL": ["income statement", "profit and loss", "profit & loss", "statement of profit and loss"],
    "Cash Flow": ["cash flow", "statement of cash flow"]
}

ALLOWED_CATEGORIES = {"BS", "PL", "Cash Flow"}
LIGATURES = {'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬀ': 'ff', 'ﬃ': 'ffi', 'ﬄ': 'ffl'}

_vectorizer = None
_model = None


def _load_ml_models():
    global _vectorizer, _model
    if _vectorizer is None or _model is None:
        logger.info("Loading ML models...")
        _vectorizer = joblib.load(ML_MODELS_DIR / "LR_NFRA_vectorizer.pkl")
        _model = joblib.load(ML_MODELS_DIR / "LR_NFRA_CLASSIFIER.pkl")
        logger.info("ML models loaded")
    return _vectorizer, _model


def normalize_category(category: str, default: str = "Others") -> str:
    cat = category.lower().strip()
    if "balance" in cat or cat == "bs":
        return "BS"
    if "profit" in cat or "loss" in cat or "income" in cat or cat in ("pl", "p&l"):
        return "PL"
    if "cash" in cat:
        return "Cash Flow"
    if "note" in cat:
        return "Notes"
    return default


def normalize_text(text: str) -> str:
    text = text.lower()
    for lig, rep in LIGATURES.items():
        text = text.replace(lig, rep)
    return re.sub(r'\s+', ' ', text).strip()


def extract_header_text(page, header_ratio: float = 0.15) -> str:
    rect = page.rect
    header_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + rect.height * header_ratio)
    return normalize_text(page.get_text(clip=header_rect))


def is_notes_page(header_text: str) -> bool:
    return header_text.startswith('notes')


def classify_pages(pdf_path: str) -> Dict[str, List[int]]:
    vectorizer, model = _load_ml_models()
    
    logger.info(f"Opening PDF: {Path(pdf_path).name}")
    doc = fitz.open(pdf_path)
    logger.info(f"PDF has {len(doc)} pages")
    
    category_pages = {}
    for page_num in range(len(doc)):
        text = doc[page_num].get_text()
        if not text.strip():
            continue
        
        cleaned = normalize_text(text)
        pred = normalize_category(model.predict(vectorizer.transform([cleaned]))[0])
        
        if pred != "Others":
            category_pages.setdefault(pred, []).append(page_num)
    
    doc.close()
    logger.info(f"Categories found: {list(category_pages.keys())}")
    return category_pages


def key_matching(pdf_path: str, category_pages: Dict[str, List[int]]) -> Dict[str, List[int]]:
    doc = fitz.open(pdf_path)
    filtered = {}
    
    for category, pages in category_pages.items():
        if category not in ["BS", "PL", "Cash Flow"]:
            filtered[category] = pages
            continue
        
        keywords = HEADER_KEYWORDS.get(category, [])
        matched = []
        
        for page_num in pages:
            header = extract_header_text(doc[page_num])
            if is_notes_page(header):
                continue
            if any(kw in header for kw in keywords):
                matched.append(page_num)
        
        filtered[category] = matched
    
    doc.close()
    return filtered


def create_category_pdf(pdf_path: str, page_indices: List[int]) -> bytes:
    doc = fitz.open(pdf_path)
    new_doc = fitz.open()
    for p in page_indices:
        new_doc.insert_pdf(doc, from_page=p, to_page=p)
    pdf_bytes = new_doc.tobytes()
    new_doc.close()
    doc.close()
    return pdf_bytes


def _parse_category_worker(
    api_key: str,
    pdf_path: str,
    category: str,
    pages: List[int]
) -> Dict[str, Any]:
    start_time = time.time()
    logger.info(f"[THREAD] Processing {category} ({len(pages)} pages)")
    
    try:
        parser = LlamaParse(
            api_key=api_key,
            result_type="markdown",
            verbose=False,
            language="en"
        )
        
        pdf_bytes = create_category_pdf(pdf_path, pages)
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            temp_path = f.name
        
        try:
            docs = parser.load_data(temp_path)
            markdown = "\n\n".join([d.text for d in docs])
        finally:
            os.unlink(temp_path)
        
        elapsed = time.time() - start_time
        logger.info(f"[THREAD] {category} completed in {elapsed:.2f}s")
        
        return {
            "category": category,
            "status": "success",
            "markdown": markdown,
            "time": elapsed
        }
        
    except Exception as e:
        logger.error(f"[THREAD] Error processing {category}: {e}")
        return {
            "category": category,
            "status": "error",
            "error": str(e),
            "markdown": None
        }


def extract_financial_markdown(pdf_path: str, company_name: Optional[str] = None, max_workers: int = 3) -> Dict[str, Optional[str]]:
    pdf_name = company_name if company_name else Path(pdf_path).stem
    
    category_pages = classify_pages(pdf_path)
    filtered = {k: v for k, v in category_pages.items() if k in ALLOWED_CATEGORIES}
    filtered = key_matching(pdf_path, filtered)
    
    llamaparse_categories = {k: v for k, v in filtered.items() if v}
    
    if not llamaparse_categories:
        logger.warning("No valid financial statement pages found")
        return {
            "company_name": pdf_name,
            "balance_sheet_md": None,
            "profit_loss_md": None,
            "cash_flow_md": None
        }
    
    api_key = os.getenv("LLAMA_CLOUD_API_KEY")
    if not api_key:
        raise ValueError("LLAMA_CLOUD_API_KEY not found")
    
    results = {
        "BS": None,
        "PL": None,
        "Cash Flow": None
    }
    
    logger.info(f"Processing {len(llamaparse_categories)} categories with LlamaParse")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_category = {
            executor.submit(
                _parse_category_worker,
                api_key,
                pdf_path,
                category,
                pages
            ): category
            for category, pages in llamaparse_categories.items()
        }
        
        for future in as_completed(future_to_category):
            category = future_to_category[future]
            try:
                result = future.result()
                if result.get("status") == "success":
                    results[category] = result.get("markdown")
            except Exception as e:
                logger.error(f"Error getting result for {category}: {e}")
    
    return {
        "company_name": pdf_name,
        "balance_sheet_md": results.get("BS"),
        "profit_loss_md": results.get("PL"),
        "cash_flow_md": results.get("Cash Flow")
    }
