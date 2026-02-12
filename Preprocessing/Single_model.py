import time
import logging
from pathlib import Path
from typing import Dict, List, Any

import fitz
import joblib
from dotenv import load_dotenv

from utils import (ALLOWED_CATEGORIES, normalize_category, normalize_text, key_matching)
from parsing import process_categories_concurrent

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
ML_MODELS_DIR = BASE_DIR.parent / "ML_MODELS"
RESULTS_DIR = BASE_DIR.parent / "results"

# Categories to send to LlamaParse (excluding Notes)
LLAMAPARSE_CATEGORIES = {"BS", "PL", "Cash Flow"}

logger.info("Loading ML models...")
vectorizer = joblib.load(ML_MODELS_DIR / "LR_NFRA_vectorizer.pkl")
model = joblib.load(ML_MODELS_DIR / "LR_NFRA_CLASSIFIER.pkl")
logger.info("ML models loaded")


def classify_pages(pdf_path):
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


def process_pdf(pdf_path: str, max_workers: int = 3) -> Dict[str, Any]:
    """
    Process PDF - classify pages and send to LlamaParse concurrently.
    Only BS, PL, and Cash Flow are sent to LlamaParse (Notes excluded).
    """
    total_start = time.time()
    pdf_name = Path(pdf_path).stem
    
    logger.info("=" * 60)
    logger.info(f"PROCESSING: {Path(pdf_path).name}")
    logger.info("=" * 60)
    
    # Step 1: Classify pages
    category_pages = classify_pages(pdf_path)
    filtered = {k: v for k, v in category_pages.items() if k in ALLOWED_CATEGORIES}
    filtered = key_matching(pdf_path, filtered)
    
    # Step 2: Filter to only LlamaParse categories (exclude Notes)
    llamaparse_categories = {
        k: v for k, v in filtered.items() 
        if k in LLAMAPARSE_CATEGORIES and v
    }
    
    if not llamaparse_categories:
        logger.warning("No pages found for BS, PL, or Cash Flow categories")
        return {"error": "No valid categories found", "time": time.time() - total_start}
    
    logger.info(f"Categories for LlamaParse: {list(llamaparse_categories.keys())}")
    logger.info(f"Notes category excluded from LlamaParse processing")
    
    # Step 3: Process with concurrent LlamaParse
    result = process_categories_concurrent(
        pdf_path=pdf_path,
        categorized_pages=llamaparse_categories,
        pdf_name=pdf_name,
        max_workers=max_workers
    )
    
    result["total_time"] = time.time() - total_start
    logger.info(f"TOTAL TIME: {result['total_time']:.2f}s")
    
    return result


def main(pdf_path: str, classify_only: bool = False) -> Dict[str, Any]:
    """
    Main entry point for PDF processing.
    
    Args:
        pdf_path: Path to the PDF file
        classify_only: If True, only classify pages without LlamaParse processing
    """
    if classify_only:
        logger.info("CLASSIFY ONLY mode")
        category_pages = classify_pages(pdf_path)
        filtered = {k: v for k, v in category_pages.items() if k in ALLOWED_CATEGORIES}
        
        print(f"\nClassified pages for: {Path(pdf_path).name}")
        print("-" * 40)
        print("BEFORE keyword matching:")
        for cat, pages in filtered.items():
            print(f"  {cat}: Pages {[p + 1 for p in pages]}")
        
        filtered = key_matching(pdf_path, filtered)
        
        print("\nAFTER keyword matching:")
        print("-" * 40)
        for cat, pages in filtered.items():
            print(f"  {cat}: Pages {[p + 1 for p in pages]}")
        
        # Show which categories would be sent to LlamaParse
        llamaparse_cats = {k: v for k, v in filtered.items() if k in LLAMAPARSE_CATEGORIES}
        print(f"\nCategories for LlamaParse (Notes excluded):")
        print("-" * 40)
        for cat, pages in llamaparse_cats.items():
            print(f"  {cat}: Pages {[p + 1 for p in pages]}")
        
        return filtered
    else:
        result = process_pdf(pdf_path)
        pdf_name = Path(pdf_path).stem
        
        print(f"\n{'='*50}")
        print(f"PROCESSING COMPLETE")
        print(f"{'='*50}")
        print(f"Results saved to: {RESULTS_DIR / pdf_name}")
        
        if result.get("successful"):
            print(f"\nSuccessful categories:")
            for item in result["successful"]:
                print(f"  - {item['category']}: Pages {item['pages']} ({item['time']:.2f}s)")
        
        if result.get("failed"):
            print(f"\nFailed categories:")
            for item in result["failed"]:
                print(f"  - {item.get('category', 'Unknown')}: {item.get('error', 'Unknown error')}")
        
        print(f"\nTotal time: {result.get('total_time', 0):.2f}s")
        return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        classify_only = len(sys.argv) > 2 and sys.argv[2] in ('--classify', '-c')
        main(sys.argv[1], classify_only)
    else:
        print("Usage: python Single_model.py <pdf_path> [--classify]")
        print("  --classify, -c: Only classify pages, don't process with LlamaParse")
