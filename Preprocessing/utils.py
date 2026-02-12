import os
import re
import tempfile
import time
import logging
import fitz
from dotenv import load_dotenv
from llama_parse import LlamaParse

load_dotenv()
logger = logging.getLogger(__name__)

HEADER_KEYWORDS = {
    "BS": ["balance sheet", "statement of assets and liabilities"],
    "PL": ["income statement", "profit and loss", "profit & loss", "statement of profit and loss"],
    "Cash Flow": ["cash flow", "statement of cash flow"]
}

ALLOWED_CATEGORIES = {"BS", "PL", "Cash Flow", "Notes"}
LIGATURES = {'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬀ': 'ff', 'ﬃ': 'ffi', 'ﬄ': 'ffl'}


def normalize_category(category, default="Others"):
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


def normalize_text(text):
    text = text.lower()
    for lig, rep in LIGATURES.items():
        text = text.replace(lig, rep)
    return re.sub(r'\s+', ' ', text).strip()


def extract_header_text(page, header_ratio=0.15):
    """Extract header text from a fitz page object (not path)."""
    rect = page.rect
    header_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + rect.height * header_ratio)
    return normalize_text(page.get_text(clip=header_rect))


def is_notes_page(header_text):
    return header_text.startswith('notes')


def key_matching(pdf_path, category_pages):
    logger.info("=" * 50)
    logger.info("HEADER KEYWORD MATCHING")
    logger.info("=" * 50)
    
    doc = fitz.open(pdf_path)
    filtered = {}
    
    for category, pages in category_pages.items():
        if category not in ["BS", "PL", "Cash Flow"]:
            filtered[category] = pages
            logger.info(f"{category}: {len(pages)} pages (not filtered)")
            continue
        
        keywords = HEADER_KEYWORDS.get(category, [])
        matched = []
        logger.info(f"\n{category} - Checking {len(pages)} pages")
        
        for page_num in pages:
            header = extract_header_text(doc[page_num])
            if is_notes_page(header):
                logger.info(f"  Page {page_num + 1}: EXCLUDED - Notes page")
                continue
            if any(kw in header for kw in keywords):
                matched.append(page_num)
        
        filtered[category] = matched
        removed = [p + 1 for p in pages if p not in matched]
        logger.info(f"\n{category}: {len(pages)} -> {len(matched)} pages")
        if removed:
            logger.info(f"  Removed: {removed}")
    
    doc.close()
    logger.info("=" * 50)
    return filtered


def create_category_pdf(pdf_path, page_indices):
    doc = fitz.open(pdf_path)
    new_doc = fitz.open()
    for p in page_indices:
        new_doc.insert_pdf(doc, from_page=p, to_page=p)
    pdf_bytes = new_doc.tobytes()
    new_doc.close()
    doc.close()
    return pdf_bytes


def parse_with_llamaparse(pdf_bytes):
    logger.info("Starting LlamaParse...")
    api_key = os.getenv("LLAMA_CLOUD_API_KEY")
    if not api_key:
        raise ValueError("LLAMA_CLOUD_API_KEY not found")
    
    parser = LlamaParse(api_key=api_key, result_type="markdown")
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
        temp_path = f.name
    
    try:
        docs = parser.load_data(temp_path)
        return "\n\n".join([d.text for d in docs])
    finally:
        os.unlink(temp_path)


def save_markdown(result, output_dir, pdf_name):
    output_dir.mkdir(parents=True, exist_ok=True)
    for category, data in result.items():
        filename = f"{category.replace(' ', '_')}_{pdf_name}.md"
        filepath = output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {category}\n\n")
            f.write(f"**Source:** {pdf_name}.pdf\n\n")
            f.write(f"**Pages:** {[p + 1 for p in data['pages']]}\n\n")
            f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(data['markdown'])
        logger.info(f"Saved: {filename}")
