import sys
import asyncio
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from Preprocessing.LLM.llm_pipeline import (
    process_company,
    generate_balance_sheet_json,
    generate_profit_loss_json,
    generate_cash_flow_json,
    save_json
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).resolve().parent / "results"


async def test_pipeline():
    company_name = "eternal"
    company_dir = RESULTS_DIR / company_name
    
    logger.info("=" * 60)
    logger.info(f"TESTING LLM PIPELINE FOR: {company_name}")
    logger.info("=" * 60)
    
    bs_path = company_dir / "BS_eternal.md"
    pl_path = company_dir / "PL_eternal.md"
    cf_path = company_dir / "Cash Flow_eternal.md"
    
    bs_md = bs_path.read_text(encoding="utf-8") if bs_path.exists() else None
    pl_md = pl_path.read_text(encoding="utf-8") if pl_path.exists() else None
    cf_md = cf_path.read_text(encoding="utf-8") if cf_path.exists() else None
    
    logger.info(f"Balance Sheet MD: {'Loaded' if bs_md else 'Not found'} ({len(bs_md) if bs_md else 0} chars)")
    logger.info(f"Profit & Loss MD: {'Loaded' if pl_md else 'Not found'} ({len(pl_md) if pl_md else 0} chars)")
    logger.info(f"Cash Flow MD: {'Loaded' if cf_md else 'Not found'} ({len(cf_md) if cf_md else 0} chars)")
    
    logger.info("\n" + "=" * 60)
    logger.info("STARTING PARALLEL LLM PROCESSING")
    logger.info("=" * 60)
    
    result = await process_company(
        company_name=f"{company_name}_test",
        bs_md=bs_md,
        pl_md=pl_md,
        cf_md=cf_md
    )
    
    logger.info("\n" + "=" * 60)
    logger.info("RESULTS")
    logger.info("=" * 60)
    
    logger.info(f"Company: {result.get('company_name')}")
    logger.info(f"Balance Sheet: {'SUCCESS' if result.get('balance_sheet') else 'FAILED'}")
    logger.info(f"Profit & Loss: {'SUCCESS' if result.get('profit_and_loss') else 'FAILED'}")
    logger.info(f"Cash Flow: {'SUCCESS' if result.get('cash_flow') else 'FAILED'}")
    
    if result.get("errors"):
        logger.error(f"Errors: {result['errors']}")
    
    if result.get("balance_sheet"):
        bs = result["balance_sheet"]
        logger.info(f"\nBalance Sheet Preview:")
        logger.info(f"  Statement Type: {bs.get('statement_type')}")
        logger.info(f"  Category: {bs.get('category')}")
        logger.info(f"  Rows Count: {len(bs.get('rows', []))}")
        if bs.get("totals", {}).get("total_assets"):
            ta = bs["totals"]["total_assets"]
            logger.info(f"  Total Assets: CY={ta.get('current_year')}, PY={ta.get('previous_year')}")
    
    if result.get("profit_and_loss"):
        pl = result["profit_and_loss"]
        logger.info(f"\nProfit & Loss Preview:")
        logger.info(f"  Statement Type: {pl.get('statement_type')}")
        logger.info(f"  Category: {pl.get('category')}")
        logger.info(f"  Rows Count: {len(pl.get('rows', []))}")
    
    if result.get("cash_flow"):
        cf = result["cash_flow"]
        logger.info(f"\nCash Flow Preview:")
        logger.info(f"  Statement Type: {cf.get('statement_type')}")
        logger.info(f"  Category: {cf.get('category')}")
        logger.info(f"  Rows Count: {len(cf.get('rows', []))}")
    
    output_dir = RESULTS_DIR / f"{company_name}_test"
    logger.info(f"\nJSON files saved to: {output_dir}")
    
    return result


if __name__ == "__main__":
    result = asyncio.run(test_pipeline())
    
    success_count = sum([
        1 if result.get("balance_sheet") else 0,
        1 if result.get("profit_and_loss") else 0,
        1 if result.get("cash_flow") else 0
    ])
    
    print(f"\n{'='*60}")
    print(f"TEST COMPLETE: {success_count}/3 statements processed successfully")
    print(f"{'='*60}")
