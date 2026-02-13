from typing import Literal

from pydantic import BaseModel


class BalanceSheetRow(BaseModel):
    section: Literal["assets", "equity", "liabilities"]
    classification: Literal["current", "non_current"] | None = None
    raw_label: str
    normalized_label: str
    note_reference: str | None = None
    values: dict[str, float | None]


class BalanceSheetTotals(BaseModel):
    total_assets: dict[str, float | None] | None = None
    total_equity: dict[str, float | None] | None = None
    total_liabilities: dict[str, float | None] | None = None
    total_equity_and_liabilities: dict[str, float | None] | None = None


class BalanceSheetMetadata(BaseModel):
    statement_title: str | None = None
    period: str | None = None
    reporting_dates: list[str] | None = None


class BalanceSheetSchema(BaseModel):
    statement_type: Literal["balance_sheet"] = "balance_sheet"
    category: Literal["standalone", "consolidated"]
    metadata: BalanceSheetMetadata
    rows: list[BalanceSheetRow]
    totals: BalanceSheetTotals


class ProfitLossRow(BaseModel):
    section: Literal["income", "expenses", "tax", "other_comprehensive_income"]
    raw_label: str
    normalized_label: str
    note_reference: str | None = None
    values: dict[str, float | None]


class ProfitLossTotals(BaseModel):
    total_income: dict[str, float | None] | None = None
    total_expenses: dict[str, float | None] | None = None
    profit_before_tax: dict[str, float | None] | None = None
    profit_after_tax: dict[str, float | None] | None = None
    basic_eps: dict[str, float | None] | None = None


class ProfitLossMetadata(BaseModel):
    statement_title: str | None = None
    period: str | None = None
    reporting_dates: list[str] | None = None


class ProfitLossSchema(BaseModel):
    statement_type: Literal["profit_and_loss"] = "profit_and_loss"
    category: Literal["standalone", "consolidated"]
    metadata: ProfitLossMetadata | None = None
    rows: list[ProfitLossRow]
    totals: ProfitLossTotals


class CashFlowRow(BaseModel):
    activity_type: Literal["operating", "investing", "financing"]
    raw_label: str
    normalized_label: str
    note_reference: str | None = None
    values: dict[str, float | None]


class CashFlowTotals(BaseModel):
    net_cash_from_operating: dict[str, float | None] | None = None
    net_cash_from_investing: dict[str, float | None] | None = None
    net_cash_from_financing: dict[str, float | None] | None = None
    net_increase_in_cash: dict[str, float | None] | None = None
    opening_cash_balance: dict[str, float | None] | None = None
    closing_cash_balance: dict[str, float | None] | None = None


class CashFlowMetadata(BaseModel):
    statement_title: str | None = None
    period: str | None = None
    reporting_dates: list[str] | None = None


class CashFlowSchema(BaseModel):
    statement_type: Literal["cash_flow"] = "cash_flow"
    category: Literal["standalone", "consolidated"]
    metadata: CashFlowMetadata | None = None
    rows: list[CashFlowRow]
    totals: CashFlowTotals
