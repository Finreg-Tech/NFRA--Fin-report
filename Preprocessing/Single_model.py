import time
import logging
from pathlib import Path
import fitz
import joblib
from utils import (ALLOWED_CATEGORIES, normalize_category, normalize_text,
                   key_matching, create_category_pdf, parse_with_llamaparse, save_markdown)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
ML_MODELS_DIR = BASE_DIR.parent / "ML_MODELS"

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


def process_pdf(pdf_path, save_output=True):
    total_start = time.time()
    logger.info("=" * 50)
    logger.info(f"Processing: {Path(pdf_path).name}")
    logger.info("=" * 50)

    category_pages = classify_pages(pdf_path)
    filtered = {k: v for k, v in category_pages.items() if k in ALLOWED_CATEGORIES}
    filtered = key_matching(pdf_path, filtered)
    
    result = {}
    for category, pages in filtered.items():
        if not pages:
            continue
        logger.info(f"Processing {category} ({len(pages)} pages)")
        pdf_bytes = create_category_pdf(pdf_path, pages)
        result[category] = {"pages": pages, "markdown": parse_with_llamaparse(pdf_bytes)}
    
    if save_output and result:
        pdf_name = Path(pdf_path).stem
        save_markdown(result, BASE_DIR.parent / "output" / pdf_name, pdf_name)
    
    logger.info(f"TOTAL TIME: {time.time() - total_start:.2f}s")
    return result


def main(pdf_path, classify_only=False):
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
        return filtered
    else:
        result = process_pdf(pdf_path)
        print(f"\nCompleted! Files saved to: {BASE_DIR.parent / 'output' / Path(pdf_path).stem}")
        for cat in result:
            print(f"  - {cat}: {len(result[cat]['pages'])} pages")
        return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        classify_only = len(sys.argv) > 2 and sys.argv[2] in ('--classify', '-c')
        main(sys.argv[1], classify_only)
    else:
        print("DONE")
