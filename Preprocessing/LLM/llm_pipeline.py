import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Type

from pydantic import BaseModel, ValidationError
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv

from Preprocessing.LLM.schemas import BalanceSheetSchema, ProfitLossSchema, CashFlowSchema

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "JSON" / "prompts"
RESULTS_DIR = BASE_DIR.parent / "results"

PROMPT_FILES = {
    "balance_sheet": PROMPTS_DIR / "BS.j2",
    "profit_loss": PROMPTS_DIR / "PL.j2",
    "cash_flow": PROMPTS_DIR / "CF.j2"
}


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )


def load_prompt(statement_type: str) -> str:
    prompt_path = PROMPT_FILES.get(statement_type)
    if not prompt_path or not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found for {statement_type}")
    return prompt_path.read_text(encoding="utf-8")


def create_chain(statement_type: str, schema: Type[BaseModel]):
    llm = get_llm()
    parser = JsonOutputParser(pydantic_object=schema)
    system_prompt = load_prompt(statement_type)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{markdown_content}")
    ])
    
    chain = prompt | llm | parser
    return chain


async def call_llm_with_retry(
    chain,
    markdown: str,
    schema: Type[BaseModel],
    statement_type: str,
    max_retries: int = 2
) -> Tuple[Optional[Dict], Optional[str]]:
    for attempt in range(max_retries):
        try:
            result = await chain.ainvoke({"markdown_content": markdown})
            validated = schema.model_validate(result)
            return validated.model_dump(), None
        except ValidationError as e:
            error_msg = f"Validation error for {statement_type} (attempt {attempt + 1}): {str(e)}"
            logger.warning(error_msg)
            if attempt == max_retries - 1:
                return None, error_msg
        except Exception as e:
            error_msg = f"LLM error for {statement_type} (attempt {attempt + 1}): {str(e)}"
            logger.warning(error_msg)
            if attempt == max_retries - 1:
                return None, error_msg
    return None, f"Max retries exceeded for {statement_type}"


async def generate_balance_sheet_json(markdown: str) -> Tuple[Optional[Dict], Optional[str]]:
    chain = create_chain("balance_sheet", BalanceSheetSchema)
    return await call_llm_with_retry(chain, markdown, BalanceSheetSchema, "balance_sheet")


async def generate_profit_loss_json(markdown: str) -> Tuple[Optional[Dict], Optional[str]]:
    chain = create_chain("profit_loss", ProfitLossSchema)
    return await call_llm_with_retry(chain, markdown, ProfitLossSchema, "profit_loss")


async def generate_cash_flow_json(markdown: str) -> Tuple[Optional[Dict], Optional[str]]:
    chain = create_chain("cash_flow", CashFlowSchema)
    return await call_llm_with_retry(chain, markdown, CashFlowSchema, "cash_flow")


def save_json(company_name: str, filename: str, data: Dict) -> bool:
    try:
        company_dir = RESULTS_DIR / company_name
        company_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = company_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Saved {filename} for {company_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save {filename} for {company_name}: {str(e)}")
        return False


async def process_statements_parallel(
    company_name: str,
    bs_md: Optional[str] = None,
    pl_md: Optional[str] = None,
    cf_md: Optional[str] = None
) -> Dict:
    results = {
        "company_name": company_name,
        "balance_sheet": None,
        "profit_and_loss": None,
        "cash_flow": None,
        "errors": []
    }
    
    tasks = []
    task_mapping = []
    
    if bs_md and bs_md.strip():
        tasks.append(generate_balance_sheet_json(bs_md))
        task_mapping.append(("balance_sheet", "balance_sheet.json"))
    
    if pl_md and pl_md.strip():
        tasks.append(generate_profit_loss_json(pl_md))
        task_mapping.append(("profit_and_loss", "profit_and_loss.json"))
    
    if cf_md and cf_md.strip():
        tasks.append(generate_cash_flow_json(cf_md))
        task_mapping.append(("cash_flow", "cash_flow.json"))
    
    if not tasks:
        results["errors"].append("No markdown content provided")
        return results
    
    logger.info(f"Processing {len(tasks)} statements for {company_name}")
    
    task_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for (statement_type, filename), result in zip(task_mapping, task_results):
        if isinstance(result, Exception):
            error_msg = f"Task exception for {statement_type}: {str(result)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            continue
        
        data, error = result
        if error:
            logger.error(f"Processing failed for {statement_type}: {error}")
            results["errors"].append(error)
            continue
        
        results[statement_type] = data
        save_json(company_name, filename, data)
    
    if not results["errors"]:
        results["errors"] = None
    
    logger.info(f"Completed processing for {company_name}")
    return results


async def process_company(
    company_name: str,
    bs_md: Optional[str] = None,
    pl_md: Optional[str] = None,
    cf_md: Optional[str] = None
) -> Dict:
    return await process_statements_parallel(company_name, bs_md, pl_md, cf_md)

