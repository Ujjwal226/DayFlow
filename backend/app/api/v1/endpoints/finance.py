import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services.finance_service import FinanceService
from app.schemas.finance import (
    FinancialAccountCreate,
    FinancialAccountUpdate,
    FinancialAccountResponse,
    BalanceAdjustmentCreate,
    FinancialCategoryCreate,
    FinancialCategoryUpdate,
    FinancialCategoryResponse,
    FinancialTagCreate,
    FinancialTagResponse,
    FinancialTransactionCreate,
    FinancialTransactionUpdate,
    FinancialTransactionResponse,
    TransactionListResponse,
    FinancialTransferCreate,
    FinancialTransferResponse,
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    RecurringTransactionCreate,
    RecurringTransactionUpdate,
    RecurringTransactionResponse,
    FinancialSavingsGoalCreate,
    FinancialSavingsGoalUpdate,
    FinancialSavingsGoalResponse,
    SavingsGoalEntryCreate,
    SavingsGoalEntryResponse,
    FinanceDashboardOverview,
    FinancialAnalyticsResponse,
)

router = APIRouter(prefix="/finance", tags=["finance"])


# ------------------ ACCOUNTS ------------------
@router.get("/accounts", response_model=List[FinancialAccountResponse])
def get_accounts(
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return service.get_accounts(current_user.id, include_archived=include_archived)


@router.post("/accounts", response_model=FinancialAccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    data: FinancialAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return service.create_account(current_user.id, data)


@router.get("/accounts/{account_id}", response_model=FinancialAccountResponse)
def get_account(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    acc = service.get_account(account_id, current_user.id)
    if not acc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return acc


@router.put("/accounts/{account_id}", response_model=FinancialAccountResponse)
def update_account(
    account_id: uuid.UUID,
    data: FinancialAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    acc = service.update_account(account_id, current_user.id, data)
    if not acc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return acc


@router.patch("/accounts/{account_id}/archive", response_model=FinancialAccountResponse)
def archive_account(
    account_id: uuid.UUID,
    archive: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    acc = service.archive_account(account_id, current_user.id, archive=archive)
    if not acc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return acc


@router.post("/accounts/{account_id}/adjust-balance", response_model=FinancialAccountResponse)
def adjust_account_balance(
    account_id: uuid.UUID,
    data: BalanceAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    try:
        return service.create_balance_adjustment(account_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ------------------ CATEGORIES & TAGS ------------------
@router.get("/categories", response_model=List[FinancialCategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return service.get_categories(current_user.id)


@router.post("/categories", response_model=FinancialCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: FinancialCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return service.create_category(current_user.id, data)


@router.put("/categories/{category_id}", response_model=FinancialCategoryResponse)
def update_category(
    category_id: uuid.UUID,
    data: FinancialCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    cat = service.update_category(category_id, current_user.id, data)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return cat


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    if not service.delete_category(category_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return None


@router.get("/tags", response_model=List[FinancialTagResponse])
def get_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return service.get_tags(current_user.id)


@router.post("/tags", response_model=FinancialTagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    data: FinancialTagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return service.create_tag(current_user.id, data)


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    if not service.delete_tag(tag_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return None


# ------------------ TRANSACTIONS ------------------
@router.get("/transactions", response_model=TransactionListResponse)
def get_transactions(
    account_id: Optional[uuid.UUID] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    transaction_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    include_voided: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return service.get_transactions(
        user_id=current_user.id,
        account_id=account_id,
        category_id=category_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        search=search,
        include_voided=include_voided,
        page=page,
        page_size=page_size,
    )


@router.post("/transactions", response_model=FinancialTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: FinancialTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    try:
        return service.create_transaction(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/transactions/{transaction_id}", response_model=FinancialTransactionResponse)
def get_transaction(
    transaction_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    tx = service.get_transaction(transaction_id, current_user.id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return tx


@router.put("/transactions/{transaction_id}", response_model=FinancialTransactionResponse)
def update_transaction(
    transaction_id: uuid.UUID,
    data: FinancialTransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    try:
        tx = service.update_transaction(transaction_id, current_user.id, data)
        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        return tx
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/transactions/{transaction_id}/void", response_model=FinancialTransactionResponse)
def void_transaction(
    transaction_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    tx = service.void_transaction(transaction_id, current_user.id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return tx


# ------------------ TRANSFERS ------------------
@router.post("/transfers", response_model=FinancialTransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(
    data: FinancialTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    try:
        return service.create_transfer(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/transfers/{transfer_id}/void", response_model=FinancialTransferResponse)
def void_transfer(
    transfer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    t = service.void_transfer(transfer_id, current_user.id)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
    return t


# ------------------ BUDGETS ------------------
@router.get("/budgets", response_model=List[BudgetResponse])
def get_budgets(
    year: int = Query(default_factory=lambda: date.today().year),
    month: int = Query(default_factory=lambda: date.today().month, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return service.get_budgets(current_user.id, year=year, month=month)


@router.post("/budgets", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    try:
        return service.create_budget(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/budgets/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: uuid.UUID,
    data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    b = service.update_budget(budget_id, current_user.id, data)
    if not b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return b


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    if not service.delete_budget(budget_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return None


# ------------------ RECURRING TRANSACTIONS ------------------
@router.get("/recurring", response_model=List[RecurringTransactionResponse])
def get_recurring_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return service.get_recurring_rules(current_user.id)


@router.post("/recurring", response_model=RecurringTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_recurring_rule(
    data: RecurringTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    try:
        return service.create_recurring_rule(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/recurring/{rule_id}", response_model=RecurringTransactionResponse)
def update_recurring_rule(
    rule_id: uuid.UUID,
    data: RecurringTransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    r = service.update_recurring_rule(rule_id, current_user.id, data)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring rule not found")
    return r


@router.delete("/recurring/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring_rule(
    rule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    if not service.delete_recurring_rule(rule_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring rule not found")
    return None


# ------------------ SAVINGS GOALS ------------------
@router.get("/savings-goals", response_model=List[FinancialSavingsGoalResponse])
def get_savings_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return service.get_savings_goals(current_user.id)


@router.post("/savings-goals", response_model=FinancialSavingsGoalResponse, status_code=status.HTTP_201_CREATED)
def create_savings_goal(
    data: FinancialSavingsGoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return service.create_savings_goal(current_user.id, data)


@router.get("/savings-goals/{goal_id}", response_model=FinancialSavingsGoalResponse)
def get_savings_goal(
    goal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    g = service.get_savings_goal(goal_id, current_user.id)
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Savings goal not found")
    return g


@router.put("/savings-goals/{goal_id}", response_model=FinancialSavingsGoalResponse)
def update_savings_goal(
    goal_id: uuid.UUID,
    data: FinancialSavingsGoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    g = service.update_savings_goal(goal_id, current_user.id, data)
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Savings goal not found")
    return g


@router.delete("/savings-goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_savings_goal(
    goal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    if not service.delete_savings_goal(goal_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Savings goal not found")
    return None


@router.post("/savings-goals/{goal_id}/entries", response_model=SavingsGoalEntryResponse, status_code=status.HTTP_201_CREATED)
def add_savings_entry(
    goal_id: uuid.UUID,
    data: SavingsGoalEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    try:
        return service.add_savings_entry(current_user.id, goal_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ------------------ OVERVIEW & ANALYTICS ------------------
@router.get("/overview", response_model=FinanceDashboardOverview)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return service.get_dashboard_overview(current_user.id)


@router.get("/analytics", response_model=FinancialAnalyticsResponse)
def get_financial_analytics(
    currency: str = Query("USD"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    return service.get_financial_analytics(current_user.id, currency=currency, start_date=start_date, end_date=end_date)


# ------------------ CSV EXPORT ------------------
@router.get("/export/csv")
def export_transactions_csv(
    account_id: Optional[uuid.UUID] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    transaction_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    include_voided: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FinanceService(db)
    content = service.export_transactions_csv(
        user_id=current_user.id,
        account_id=account_id,
        category_id=category_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        include_voided=include_voided,
    )
    filename = f"dayflow-transactions-{date.today().isoformat()}.csv"
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
