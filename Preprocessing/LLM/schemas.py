from typing import Optional, List, Literal, Dict
from pydantic import BaseModel


class BalanceSheetRow(BaseModel):
    section: Literal["assets", "equity", "liabilities"]
    classification: Optional[Literal["current", "non_current"]] = None
    raw_label: str
    normalized_label: str
    note_reference: Optional[str] = None
    values: Dict[str, Optional[float]]


class BalanceSheetTotals(BaseModel):
    total_assets: Optional[Dict[str, Optional[float]]] = None
    total_equity: Optional[Dict[str, Optional[float]]] = None
    total_liabilities: Optional[Dict[str, Optional[float]]] = None
    total_equity_and_liabilities: Optional[Dict[str, Optional[float]]] = None


class BalanceSheetMetadata(BaseModel):
    statement_title: Optional[str] = None
    period: Optional[str] = None
    reporting_dates: Optional[List[str]] = None


class BalanceSheetSchema(BaseModel):
    statement_type: Literal["balance_sheet"] = "balance_sheet"
    category: Literal["standalone", "consolidated"]
    metadata: BalanceSheetMetadata
    rows: List[BalanceSheetRow]
    totals: BalanceSheetTotals


class ProfitLossRow(BaseModel):
    section: Literal["income", "expenses", "tax", "other_comprehensive_income"]
    raw_label: str
    normalized_label: str
    note_reference: Optional[str] = None
    values: Dict[str, Optional[float]]


class ProfitLossTotals(BaseModel):
    total_income: Optional[Dict[str, Optional[float]]] = None
    total_expenses: Optional[Dict[str, Optional[float]]] = None
    profit_before_tax: Optional[Dict[str, Optional[float]]] = None
    profit_after_tax: Optional[Dict[str, Optional[float]]] = None
    basic_eps: Optional[Dict[str, Optional[float]]] = None


class ProfitLossMetadata(BaseModel):
    statement_title: Optional[str] = None
    period: Optional[str] = None
    reporting_dates: Optional[List[str]] = None


class ProfitLossSchema(BaseModel):
    statement_type: Literal["profit_and_loss"] = "profit_and_loss"
    category: Literal["standalone", "consolidated"]
    metadata: Optional[ProfitLossMetadata] = None
    rows: List[ProfitLossRow]
    totals: ProfitLossTotals


class CashFlowRow(BaseModel):
    activity_type: Literal["operating", "investing", "financing"]
    raw_label: str
    normalized_label: str
    note_reference: Optional[str] = None
    values: Dict[str, Optional[float]]


class CashFlowTotals(BaseModel):
    net_cash_from_operating: Optional[Dict[str, Optional[float]]] = None
    net_cash_from_investing: Optional[Dict[str, Optional[float]]] = None
    net_cash_from_financing: Optional[Dict[str, Optional[float]]] = None
    net_increase_in_cash: Optional[Dict[str, Optional[float]]] = None
    opening_cash_balance: Optional[Dict[str, Optional[float]]] = None
    closing_cash_balance: Optional[Dict[str, Optional[float]]] = None


class CashFlowMetadata(BaseModel):
    statement_title: Optional[str] = None
    period: Optional[str] = None
    reporting_dates: Optional[List[str]] = None


class CashFlowSchema(BaseModel):
    statement_type: Literal["cash_flow"] = "cash_flow"
    category: Literal["standalone", "consolidated"]
    metadata: Optional[CashFlowMetadata] = None
    rows: List[CashFlowRow]
    totals: CashFlowTotals
