import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Preprocessing.LLM.pipeline import process_company

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


async def test_pipeline() -> dict:
    company_name = "eternal"
    company_dir = RESULTS_DIR / company_name

    logger.info("Testing LLM pipeline for: %s", company_name)

    bs_path = company_dir / "BS_eternal.md"
    pl_path = company_dir / "PL_eternal.md"
    cf_path = company_dir / "Cash Flow_eternal.md"

    bs_md = bs_path.read_text(encoding="utf-8") if bs_path.exists() else None
    pl_md = pl_path.read_text(encoding="utf-8") if pl_path.exists() else None
    cf_md = cf_path.read_text(encoding="utf-8") if cf_path.exists() else None

    logger.info("Balance Sheet MD: %s (%d chars)", "Loaded" if bs_md else "Not found", len(bs_md) if bs_md else 0)
    logger.info("Profit & Loss MD: %s (%d chars)", "Loaded" if pl_md else "Not found", len(pl_md) if pl_md else 0)
    logger.info("Cash Flow MD: %s (%d chars)", "Loaded" if cf_md else "Not found", len(cf_md) if cf_md else 0)

    result = await process_company(
        company_name=f"{company_name}_test",
        bs_md=bs_md,
        pl_md=pl_md,
        cf_md=cf_md
    )

    logger.info("Company: %s", result.get("company_name"))
    logger.info("Balance Sheet: %s", "SUCCESS" if result.get("balance_sheet") else "FAILED")
    logger.info("Profit & Loss: %s", "SUCCESS" if result.get("profit_and_loss") else "FAILED")
    logger.info("Cash Flow: %s", "SUCCESS" if result.get("cash_flow") else "FAILED")

    if result.get("errors"):
        logger.error("Errors: %s", result["errors"])

    if result.get("balance_sheet"):
        bs = result["balance_sheet"]
        logger.info("Balance Sheet - Type: %s, Category: %s, Rows: %d",
                    bs.get("statement_type"), bs.get("category"), len(bs.get("rows", [])))

    if result.get("profit_and_loss"):
        pl = result["profit_and_loss"]
        logger.info("Profit & Loss - Type: %s, Category: %s, Rows: %d",
                    pl.get("statement_type"), pl.get("category"), len(pl.get("rows", [])))

    if result.get("cash_flow"):
        cf = result["cash_flow"]
        logger.info("Cash Flow - Type: %s, Category: %s, Rows: %d",
                    cf.get("statement_type"), cf.get("category"), len(cf.get("rows", [])))

    return result


if __name__ == "__main__":
    asyncio.run(test_pipeline())
