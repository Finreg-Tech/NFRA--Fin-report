import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from config import API_HOST, API_PORT, MAX_FILE_SIZE_BYTES
from Preprocessing.LLM.extractor import extract_financial_markdown
from Preprocessing.LLM.pipeline import process_company

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")


app = FastAPI(
    title="Financial Statement Processor",
    description="API for processing financial statement PDFs into structured JSON",
    version="1.0.0",
    lifespan=lifespan
)


def validate_pdf_file(filename: str | None, content_type: str | None, content_length: int) -> None:
    if not filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    if content_type and content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid content type")

    if content_length == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    if content_length > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File too large")


def sanitize_filename(filename: str) -> str:
    stem = Path(filename).stem
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in stem)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/NFRA")
async def process_financials(file: UploadFile = File(...)) -> dict[str, Any]:
    try:
        content = await file.read()
    except IOError as e:
        logger.error("Error reading uploaded file: %s", e)
        raise HTTPException(status_code=400, detail="Error reading uploaded file")

    validate_pdf_file(file.filename, file.content_type, len(content))

    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            temp_path = tmp.name

        company_name = sanitize_filename(file.filename or "unknown")
        logger.info("Processing file: %s", file.filename)

        data = extract_financial_markdown(temp_path, company_name=company_name)

        if not data:
            raise HTTPException(status_code=400, detail="Failed to extract financial data from PDF")

        result = await process_company(
            data["company_name"],
            data.get("balance_sheet_md"),
            data.get("profit_loss_md"),
            data.get("cash_flow_md")
        )

        logger.info("Successfully processed: %s", data["company_name"])

        return {
            "company_name": data["company_name"],
            "balance_sheet": result.get("balance_sheet"),
            "profit_and_loss": result.get("profit_and_loss"),
            "cash_flow": result.get("cash_flow")
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.error("Validation error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Processing error: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error during processing")

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError as e:
                logger.warning("Failed to delete temporary file: %s", e)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
