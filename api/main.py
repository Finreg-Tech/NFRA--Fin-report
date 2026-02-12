import os
import logging
import tempfile
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from Preprocessing.LLM.pdf_extractor import extract_financial_markdown
from Preprocessing.LLM.llm_pipeline import process_company

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


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/NFRA")
async def process_financials(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid content type. Only PDF files are accepted")
    
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Error reading uploaded file: {e}")
        raise HTTPException(status_code=400, detail="Error reading uploaded file")
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            temp_path = tmp.name
        
        logger.info(f"Processing file: {file.filename}")
        
        company_name = Path(file.filename).stem
        data = extract_financial_markdown(temp_path, company_name=company_name)
        
        if not data:
            raise HTTPException(status_code=400, detail="Failed to extract financial data from PDF")
        
        result = await process_company(
            data["company_name"],
            data.get("balance_sheet_md"),
            data.get("profit_loss_md"),
            data.get("cash_flow_md")
        )
        
        logger.info(f"Successfully processed: {data['company_name']}")
        
        return {
            "company_name": data["company_name"],
            "balance_sheet": result.get("balance_sheet"),
            "profit_and_loss": result.get("profit_and_loss"),
            "cash_flow": result.get("cash_flow")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during processing")
    
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
