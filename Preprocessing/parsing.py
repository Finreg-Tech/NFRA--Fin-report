import os
import time
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from llama_parse import LlamaParse

from utils import create_category_pdf

load_dotenv()

# Suppress HTTP request logs
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR.parent / "results"

LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")


def _sanitize_name(name: str) -> str:
    """Sanitize name for use as directory/file name."""
    return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name).strip()


def _parse_category_worker(
    api_key: str,
    pdf_path: str,
    category: str,
    pages: List[int],
    output_dir: Path,
    pdf_name: str
) -> Dict[str, Any]:
    """
    Worker function to parse a single category with LlamaParse.
    Each worker creates its own LlamaParse instance to avoid event loop conflicts.
    """
    start_time = time.time()
    logger.info(f"[THREAD] Processing {category} ({len(pages)} pages: {[p+1 for p in pages]})")
    
    try:
        # Create fresh LlamaParse instance for this thread
        parser = LlamaParse(
            api_key=api_key,
            result_type="markdown",
            verbose=False,
            language="en"
        )
        
        # Create PDF bytes for this category
        pdf_bytes = create_category_pdf(pdf_path, pages)
        
        # Write to temp file and parse
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            temp_path = f.name
        
        try:
            docs = parser.load_data(temp_path)
            markdown = "\n\n".join([d.text for d in docs])
        finally:
            os.unlink(temp_path)
        
        # Save result
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{_sanitize_name(category)}_{pdf_name}.md"
        filepath = output_dir / filename
        
        content = f"# {category}\n\n"
        content += f"**Source:** {pdf_name}.pdf\n\n"
        content += f"**Pages:** {[p + 1 for p in pages]}\n\n"
        content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "---\n\n"
        content += markdown
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        elapsed = time.time() - start_time
        logger.info(f"[THREAD] {category} completed in {elapsed:.2f}s -> {filename}")
        
        return {
            "category": category,
            "status": "success",
            "pages": [p + 1 for p in pages],
            "output_path": str(filepath),
            "time": elapsed
        }
        
    except Exception as e:
        logger.error(f"[THREAD] Error processing {category}: {e}")
        return {
            "category": category,
            "status": "error",
            "error": str(e),
            "pages": [p + 1 for p in pages]
        }


def process_categories_concurrent(
    pdf_path: str,
    categorized_pages: Dict[str, List[int]],
    pdf_name: str,
    output_dir: Path = None,
    max_workers: int = 3
) -> Dict[str, Any]:
    """
    Process all categories concurrently using ThreadPoolExecutor.
    
    Args:
        pdf_path: Path to the source PDF file
        categorized_pages: Dict mapping category names to page numbers (0-indexed)
        pdf_name: Name of the PDF (used for output filenames)
        output_dir: Output directory (defaults to results/<pdf_name>)
        max_workers: Maximum concurrent LlamaParse requests
        
    Returns:
        Dict containing output_dir, successful results, and failed results
    """
    if not LLAMA_CLOUD_API_KEY:
        raise ValueError("LLAMA_CLOUD_API_KEY not found in environment variables")
    
    if output_dir is None:
        output_dir = RESULTS_DIR / pdf_name
    
    logger.info("=" * 60)
    logger.info(f"CONCURRENT LLAMAPARSE PROCESSING")
    logger.info(f"Categories: {list(categorized_pages.keys())}")
    logger.info(f"Output dir: {output_dir}")
    logger.info(f"Max workers: {max_workers}")
    logger.info("=" * 60)
    
    successful = []
    failed = []
    
    # Filter out empty categories
    categories_to_process = {k: v for k, v in categorized_pages.items() if v}
    
    if not categories_to_process:
        logger.warning("No categories to process")
        return {"output_dir": str(output_dir), "successful": [], "failed": []}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_category = {
            executor.submit(
                _parse_category_worker,
                LLAMA_CLOUD_API_KEY,
                pdf_path,
                category,
                pages,
                output_dir,
                pdf_name
            ): category
            for category, pages in categories_to_process.items()
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_category):
            category = future_to_category[future]
            try:
                result = future.result()
                if result.get("status") == "success":
                    successful.append(result)
                else:
                    failed.append(result)
            except Exception as e:
                logger.error(f"[THREAD] Exception for {category}: {e}")
                failed.append({
                    "category": category,
                    "status": "error",
                    "error": str(e)
                })
    
    logger.info("=" * 60)
    logger.info(f"CONCURRENT PROCESSING COMPLETE")
    logger.info(f"Successful: {len(successful)}/{len(categories_to_process)}")
    if failed:
        logger.info(f"Failed: {len(failed)}")
    logger.info("=" * 60)
    
    return {
        "output_dir": str(output_dir),
        "successful": successful,
        "failed": failed
    }


def parse_pdf_to_markdown(
    pdf_path: str,
    pages: List[int] = None,
    output_path: str = None
) -> str:
    """
    Parse a PDF (or specific pages) to markdown using LlamaParse.
    
    Args:
        pdf_path: Path to the PDF file
        pages: Optional list of page numbers (0-indexed) to extract
        output_path: Optional path to save the markdown output
        
    Returns:
        Markdown string
    """
    if not LLAMA_CLOUD_API_KEY:
        raise ValueError("LLAMA_CLOUD_API_KEY not found in environment variables")
    
    parser = LlamaParse(
        api_key=LLAMA_CLOUD_API_KEY,
        result_type="markdown",
        verbose=False,
        language="en"
    )
    
    if pages:
        # Extract specific pages
        pdf_bytes = create_category_pdf(pdf_path, pages)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            temp_path = f.name
        try:
            docs = parser.load_data(temp_path)
        finally:
            os.unlink(temp_path)
    else:
        # Parse entire PDF
        docs = parser.load_data(pdf_path)
    
    markdown = "\n\n".join([d.text for d in docs])
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        logger.info(f"Saved markdown to: {output_path}")
    
    return markdown
