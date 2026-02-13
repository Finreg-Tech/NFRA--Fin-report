import asyncio
import json
import logging
from pathlib import Path
from typing import Type

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError

from config import (
    LLM_RETRY_COUNT,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    PROMPT_FILES,
    RESULTS_DIR,
)
from Preprocessing.LLM.schemas import BalanceSheetSchema, CashFlowSchema, ProfitLossSchema

logger = logging.getLogger(__name__)


def get_llm() -> ChatOpenAI:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    return ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
        api_key=OPENAI_API_KEY
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

    return prompt | llm | parser


async def call_llm_with_retry(
    chain,
    markdown: str,
    schema: Type[BaseModel],
    statement_type: str,
    max_retries: int = LLM_RETRY_COUNT
) -> tuple[dict | None, str | None]:
    for attempt in range(max_retries):
        try:
            result = await chain.ainvoke({"markdown_content": markdown})
            validated = schema.model_validate(result)
            return validated.model_dump(), None
        except ValidationError as e:
            error_msg = f"Validation error for {statement_type} (attempt {attempt + 1})"
            logger.warning("%s: %s", error_msg, str(e))
            if attempt == max_retries - 1:
                return None, error_msg
        except Exception as e:
            error_msg = f"LLM error for {statement_type} (attempt {attempt + 1})"
            logger.warning("%s: %s", error_msg, str(e))
            if attempt == max_retries - 1:
                return None, error_msg
    return None, f"Max retries exceeded for {statement_type}"


async def generate_balance_sheet_json(markdown: str) -> tuple[dict | None, str | None]:
    chain = create_chain("balance_sheet", BalanceSheetSchema)
    return await call_llm_with_retry(chain, markdown, BalanceSheetSchema, "balance_sheet")


async def generate_profit_loss_json(markdown: str) -> tuple[dict | None, str | None]:
    chain = create_chain("profit_loss", ProfitLossSchema)
    return await call_llm_with_retry(chain, markdown, ProfitLossSchema, "profit_loss")


async def generate_cash_flow_json(markdown: str) -> tuple[dict | None, str | None]:
    chain = create_chain("cash_flow", CashFlowSchema)
    return await call_llm_with_retry(chain, markdown, CashFlowSchema, "cash_flow")


def save_json(company_name: str, filename: str, data: dict) -> bool:
    try:
        company_dir = RESULTS_DIR / company_name
        company_dir.mkdir(parents=True, exist_ok=True)

        file_path = company_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        logger.info("Saved %s for %s", filename, company_name)
        return True
    except OSError as e:
        logger.error("Failed to save %s for %s: %s", filename, company_name, str(e))
        return False


async def process_company(
    company_name: str,
    bs_md: str | None = None,
    pl_md: str | None = None,
    cf_md: str | None = None
) -> dict:
    results: dict = {
        "company_name": company_name,
        "balance_sheet": None,
        "profit_and_loss": None,
        "cash_flow": None,
        "errors": []
    }

    tasks = []
    task_mapping: list[tuple[str, str]] = []

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

    logger.info("Processing %d statements for %s", len(tasks), company_name)

    task_results = await asyncio.gather(*tasks, return_exceptions=True)

    for (statement_type, filename), result in zip(task_mapping, task_results):
        if isinstance(result, Exception):
            error_msg = f"Task exception for {statement_type}"
            logger.error("%s: %s", error_msg, str(result))
            results["errors"].append(error_msg)
            continue

        data, error = result
        if error:
            logger.error("Processing failed for %s: %s", statement_type, error)
            results["errors"].append(error)
            continue

        results[statement_type] = data
        save_json(company_name, filename, data)

    if not results["errors"]:
        results["errors"] = None

    logger.info("Completed processing for %s", company_name)
    return results
