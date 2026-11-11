import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.services.finance_service import advance_next_occurrence, sanitize_csv_cell, FinanceService
from app.services.scheduler_service import ReminderSchedulerService
from app.schemas.finance import (
    FinancialAccountCreate,
    FinancialCategoryCreate,
    FinancialTransactionCreate,
    BudgetCreate,
    RecurringTransactionCreate,
)


@pytest.fixture
def finance_user_a(db_session: Session):
    user = User(
        email="fin_user_a@example.com",
        display_name="Finance User A",
        hashed_password=hash_password("PasswordA123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def finance_user_b(db_session: Session):
    user = User(
        email="fin_user_b@example.com",
        display_name="Finance User B",
        hashed_password=hash_password("PasswordB123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers_a(finance_user_a: User):
    token = create_access_token(user_id=finance_user_a.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_b(finance_user_b: User):
    token = create_access_token(user_id=finance_user_b.id)
    return {"Authorization": f"Bearer {token}"}


def test_financial_accounts_crud_and_balance(client: TestClient, auth_headers_a: dict):
    # 1. Create checking account
    acc_payload = {
        "name": "Primary Checking",
        "account_type": "BANK_ACCOUNT",
        "currency": "USD",
        "opening_balance": "1000.00",
        "description": "Main bank checking account",
        "institution_name": "Chase",
    }
    res = client.post("/api/v1/finance/accounts", json=acc_payload, headers=auth_headers_a)
    assert res.status_code == 201, res.text
    acc_data = res.json()
    assert acc_data["name"] == "Primary Checking"
    assert acc_data["currency"] == "USD"
    assert acc_data["opening_balance"] == "1000.00"
    assert acc_data["calculated_balance"] == "1000.00"
    acc_id = acc_data["id"]

    # 2. Get list of accounts
    res = client.get("/api/v1/finance/accounts", headers=auth_headers_a)
    assert res.status_code == 200
    accounts = res.json()
    assert len(accounts) >= 1
    assert any(a["id"] == acc_id for a in accounts)

    # 3. Update account details
    update_payload = {"name": "Chase Primary Checking", "institution_name": "JPMorgan Chase"}
    res = client.put(f"/api/v1/finance/accounts/{acc_id}", json=update_payload, headers=auth_headers_a)
    assert res.status_code == 200
    assert res.json()["name"] == "Chase Primary Checking"

    # 4. Balance adjustment
    adj_payload = {
        "new_balance": "1500.00",
        "adjustment_date": date.today().isoformat(),
        "description": "Reconciled with bank statement"
    }
    res = client.post(f"/api/v1/finance/accounts/{acc_id}/adjust-balance", json=adj_payload, headers=auth_headers_a)
    assert res.status_code == 200
    assert res.json()["calculated_balance"] == "1500.00"

    # 5. Archive and unarchive
    res = client.patch(f"/api/v1/finance/accounts/{acc_id}/archive?archive=true", headers=auth_headers_a)
    assert res.status_code == 200
    assert res.json()["is_archived"] is True


def test_credit_card_liabilities_behavior(client: TestClient, auth_headers_a: dict):
    # Credit Card: opening owed balance 200
    card_res = client.post("/api/v1/finance/accounts", json={
        "name": "Sapphire Reserve",
        "account_type": "CREDIT_CARD",
        "currency": "USD",
        "opening_balance": "200.00",
    }, headers=auth_headers_a).json()
    card_id = card_res["id"]

    # Spending 150 increases card liability (200 + 150 = 350)
    client.post("/api/v1/finance/transactions", json={
        "account_id": card_id,
        "transaction_type": "EXPENSE",
        "amount": "150.00",
        "currency": "USD",
        "description": "Flight ticket",
        "transaction_date": date.today().isoformat(),
    }, headers=auth_headers_a)

    card = client.get(f"/api/v1/finance/accounts/{card_id}", headers=auth_headers_a).json()
    assert Decimal(card["calculated_balance"]) == Decimal("350.00")

    # Making a payment of 250 decreases liability (350 - 250 = 100)
    client.post("/api/v1/finance/transactions", json={
        "account_id": card_id,
        "transaction_type": "INCOME",
        "amount": "250.00",
        "currency": "USD",
        "description": "Card payment from checking",
        "transaction_date": date.today().isoformat(),
    }, headers=auth_headers_a)

    card = client.get(f"/api/v1/finance/accounts/{card_id}", headers=auth_headers_a).json()
    assert Decimal(card["calculated_balance"]) == Decimal("100.00")


def test_financial_categories_and_tags(client: TestClient, auth_headers_a: dict):
    # 1. Fetch categories (default categories automatically seeded)
    res = client.get("/api/v1/finance/categories", headers=auth_headers_a)
    assert res.status_code == 200
    cats = res.json()
    assert len(cats) >= 10
    cat_names = [c["name"] for c in cats]
    assert "Salary" in cat_names
    assert "Groceries" in cat_names

    # 2. Create custom category
    cat_payload = {
        "name": "Software & AI Tools",
        "category_type": "EXPENSE",
        "color": "#6366F1",
        "icon": "cpu"
    }
    res = client.post("/api/v1/finance/categories", json=cat_payload, headers=auth_headers_a)
    assert res.status_code == 201
    custom_cat = res.json()
    assert custom_cat["name"] == "Software & AI Tools"

    # 3. Create tag
    tag_payload = {"name": "TaxDeductible", "color": "#10B981"}
    res = client.post("/api/v1/finance/tags", json=tag_payload, headers=auth_headers_a)
    assert res.status_code == 201
    tag = res.json()
    assert tag["name"] == "TaxDeductible"


def test_transactions_ledger_and_voiding(client: TestClient, auth_headers_a: dict):
    # Setup account
    acc_res = client.post("/api/v1/finance/accounts", json={
        "name": "Ledger Account",
        "account_type": "BANK_ACCOUNT",
        "currency": "USD",
        "opening_balance": "500.00",
    }, headers=auth_headers_a)
    acc_id = acc_res.json()["id"]

    # Setup category
    cat_res = client.post("/api/v1/finance/categories", json={
        "name": "Dining",
        "category_type": "EXPENSE",
    }, headers=auth_headers_a)
    cat_id = cat_res.json()["id"]

    # 1. Create Expense
    tx_payload = {
        "account_id": acc_id,
        "category_id": cat_id,
        "transaction_type": "EXPENSE",
        "amount": "45.50",
        "currency": "USD",
        "description": "Lunch at Bistro",
        "transaction_date": date.today().isoformat(),
        "merchant_or_source": "Bistro Cafe",
    }
    res = client.post("/api/v1/finance/transactions", json=tx_payload, headers=auth_headers_a)
    assert res.status_code == 201
    tx = res.json()
    assert tx["amount"] == "45.50"
    tx_id = tx["id"]

    # Check updated balance: 500 - 45.50 = 454.50
    acc = client.get(f"/api/v1/finance/accounts/{acc_id}", headers=auth_headers_a).json()
    assert Decimal(acc["calculated_balance"]) == Decimal("454.50")

    # 2. Create Income
    inc_payload = {
        "account_id": acc_id,
        "transaction_type": "INCOME",
        "amount": "200.00",
        "currency": "USD",
        "description": "Freelance payment",
        "transaction_date": date.today().isoformat(),
    }
    client.post("/api/v1/finance/transactions", json=inc_payload, headers=auth_headers_a)

    # Balance: 454.50 + 200.00 = 654.50
    acc = client.get(f"/api/v1/finance/accounts/{acc_id}", headers=auth_headers_a).json()
    assert Decimal(acc["calculated_balance"]) == Decimal("654.50")

    # 3. Void expense transaction
    void_res = client.post(f"/api/v1/finance/transactions/{tx_id}/void", headers=auth_headers_a)
    assert void_res.status_code == 200
    assert void_res.json()["is_voided"] is True

    # Voided transaction should no longer decrease balance: 500 + 200 = 700.00
    acc = client.get(f"/api/v1/finance/accounts/{acc_id}", headers=auth_headers_a).json()
    assert Decimal(acc["calculated_balance"]) == Decimal("700.00")


def test_atomic_transfers(client: TestClient, auth_headers_a: dict):
    # Setup source and destination
    src = client.post("/api/v1/finance/accounts", json={
        "name": "Checking for Transfer",
        "account_type": "BANK_ACCOUNT",
        "currency": "USD",
        "opening_balance": "1000.00",
    }, headers=auth_headers_a).json()

    dst = client.post("/api/v1/finance/accounts", json={
        "name": "Savings for Transfer",
        "account_type": "SAVINGS_ACCOUNT",
        "currency": "USD",
        "opening_balance": "200.00",
    }, headers=auth_headers_a).json()

    # Perform transfer
    transfer_payload = {
        "source_account_id": src["id"],
        "destination_account_id": dst["id"],
        "amount": "300.00",
        "transfer_date": date.today().isoformat(),
        "description": "Monthly savings transfer",
    }
    res = client.post("/api/v1/finance/transfers", json=transfer_payload, headers=auth_headers_a)
    assert res.status_code == 201
    transfer_data = res.json()
    transfer_id = transfer_data["id"]

    # Check updated balances
    src_after = client.get(f"/api/v1/finance/accounts/{src['id']}", headers=auth_headers_a).json()
    dst_after = client.get(f"/api/v1/finance/accounts/{dst['id']}", headers=auth_headers_a).json()
    assert Decimal(src_after["calculated_balance"]) == Decimal("700.00")
    assert Decimal(dst_after["calculated_balance"]) == Decimal("500.00")

    # Void transfer
    void_res = client.post(f"/api/v1/finance/transfers/{transfer_id}/void", headers=auth_headers_a)
    assert void_res.status_code == 200
    assert void_res.json()["is_voided"] is True

    # Balances restored
    src_restored = client.get(f"/api/v1/finance/accounts/{src['id']}", headers=auth_headers_a).json()
    dst_restored = client.get(f"/api/v1/finance/accounts/{dst['id']}", headers=auth_headers_a).json()
    assert Decimal(src_restored["calculated_balance"]) == Decimal("1000.00")
    assert Decimal(dst_restored["calculated_balance"]) == Decimal("200.00")


def test_cross_currency_and_same_account_transfer_rejection(client: TestClient, auth_headers_a: dict):
    usd_acc = client.post("/api/v1/finance/accounts", json={
        "name": "USD Account",
        "account_type": "BANK_ACCOUNT",
        "currency": "USD",
        "opening_balance": "500.00",
    }, headers=auth_headers_a).json()

    eur_acc = client.post("/api/v1/finance/accounts", json={
        "name": "EUR Account",
        "account_type": "BANK_ACCOUNT",
        "currency": "EUR",
        "opening_balance": "500.00",
    }, headers=auth_headers_a).json()

    # 1. Cross currency rejection
    res = client.post("/api/v1/finance/transfers", json={
        "source_account_id": usd_acc["id"],
        "destination_account_id": eur_acc["id"],
        "amount": "100.00",
        "transfer_date": date.today().isoformat(),
    }, headers=auth_headers_a)
    assert res.status_code == 400
    assert "Cross-currency transfers are not supported" in res.json()["detail"]

    # 2. Same account rejection
    res2 = client.post("/api/v1/finance/transfers", json={
        "source_account_id": usd_acc["id"],
        "destination_account_id": usd_acc["id"],
        "amount": "50.00",
        "transfer_date": date.today().isoformat(),
    }, headers=auth_headers_a)
    assert res2.status_code == 400
    assert "Source and destination accounts must be different" in res2.json()["detail"]


def test_insufficient_funds_transfer_rejection(client: TestClient, auth_headers_a: dict):
    acc1 = client.post("/api/v1/finance/accounts", json={
        "name": "Low Balance Checking",
        "account_type": "BANK_ACCOUNT",
        "currency": "USD",
        "opening_balance": "50.00",
    }, headers=auth_headers_a).json()

    acc2 = client.post("/api/v1/finance/accounts", json={
        "name": "Target Account",
        "account_type": "BANK_ACCOUNT",
        "currency": "USD",
        "opening_balance": "100.00",
    }, headers=auth_headers_a).json()

    res = client.post("/api/v1/finance/transfers", json={
        "source_account_id": acc1["id"],
        "destination_account_id": acc2["id"],
        "amount": "500.00",
        "transfer_date": date.today().isoformat(),
    }, headers=auth_headers_a)
    assert res.status_code == 400
    assert "Insufficient funds in source account" in res.json()["detail"]


def test_budgets_and_utilization(client: TestClient, auth_headers_a: dict):
    today = date.today()
    # Create budget
    b_payload = {
        "name": "Monthly Groceries Budget",
        "amount": "400.00",
        "currency": "USD",
        "year": today.year,
        "month": today.month,
    }
    res = client.post("/api/v1/finance/budgets", json=b_payload, headers=auth_headers_a)
    assert res.status_code == 201
    budget = res.json()
    assert budget["amount"] == "400.00"
    assert budget["actual_spending"] == "0.00"
    assert budget["remaining_amount"] == "400.00"
    assert budget["is_overspent"] is False


def test_budget_notifications_and_thresholds(db_session: Session, finance_user_a: User):
    finance_service = FinanceService(db_session)
    scheduler_service = ReminderSchedulerService(db_session)

    # 1. Setup account and category
    acc = finance_service.create_account(finance_user_a.id, FinancialAccountCreate(
        name="Alert Checking",
        account_type="BANK_ACCOUNT",
        currency="USD",
        opening_balance=Decimal("2000.00"),
    ))
    cat = finance_service.create_category(finance_user_a.id, FinancialCategoryCreate(
        name="Electronics",
        category_type="EXPENSE",
    ))

    today = date.today()
    # Create budget of 1000 USD
    finance_service.create_budget(finance_user_a.id, BudgetCreate(
        name="Electronics Budget",
        category_id=cat.id,
        amount=Decimal("1000.00"),
        currency="USD",
        year=today.year,
        month=today.month,
    ))

    # Record 800 USD expense (80% utilization -> crosses 75%)
    finance_service.create_transaction(finance_user_a.id, FinancialTransactionCreate(
        account_id=acc.id,
        category_id=cat.id,
        transaction_type="EXPENSE",
        amount=Decimal("800.00"),
        currency="USD",
        description="New monitor",
        transaction_date=today,
    ))

    # Process budget alerts
    alerts_count = scheduler_service.process_budget_notifications()
    assert alerts_count == 1

    # Rerun scheduler: should be idempotent and not dispatch duplicate 75% alert
    alerts_count_again = scheduler_service.process_budget_notifications()
    assert alerts_count_again == 0


def test_recurring_recurrence_calendar_math():
    # Leap year February 29 to next month -> March 29
    feb29 = date(2024, 2, 29)
    next_m = advance_next_occurrence(feb29, "MONTHLY", 1)
    assert next_m == date(2024, 3, 29)

    # Month end Jan 31 -> Feb 28 (non-leap year)
    jan31 = date(2023, 1, 31)
    feb_end = advance_next_occurrence(jan31, "MONTHLY", 1)
    assert feb_end == date(2023, 2, 28)

    # Yearly from leap day Feb 29 2024 -> Feb 28 2025
    next_y = advance_next_occurrence(feb29, "YEARLY", 1)
    assert next_y == date(2025, 2, 28)

    # Weekly
    next_w = advance_next_occurrence(date(2026, 11, 12), "WEEKLY", 1)
    assert next_w == date(2026, 11, 19)


def test_recurring_scheduler_execution_idempotency(db_session: Session, finance_user_a: User):
    finance_service = FinanceService(db_session)

    acc = finance_service.create_account(finance_user_a.id, FinancialAccountCreate(
        name="Recurring Account",
        account_type="BANK_ACCOUNT",
        currency="USD",
        opening_balance=Decimal("1000.00"),
    ))

    # Create monthly recurring bill
    today = date.today()
    finance_service.create_recurring_rule(finance_user_a.id, RecurringTransactionCreate(
        account_id=acc.id,
        transaction_type="EXPENSE",
        amount=Decimal("50.00"),
        currency="USD",
        description="Internet Service Provider",
        frequency="MONTHLY",
        start_date=today,
    ))

    # Process due recurring transactions
    processed = finance_service.process_due_recurring_transactions(today)
    assert processed == 1

    # Rerun immediately for same date: must be 0 processed (idempotency constraint)
    processed_again = finance_service.process_due_recurring_transactions(today)
    assert processed_again == 0


def test_savings_goals_and_ledger_entries(client: TestClient, auth_headers_a: dict):
    goal_payload = {
        "title": "Emergency Reserve",
        "target_amount": "5000.00",
        "currency": "USD",
        "target_date": (date.today() + timedelta(days=180)).isoformat(),
    }
    res = client.post("/api/v1/finance/savings-goals", json=goal_payload, headers=auth_headers_a)
    assert res.status_code == 201
    goal = res.json()
    assert goal["target_amount"] == "5000.00"
    assert goal["current_amount"] == "0.00"
    assert goal["status"] == "ACTIVE"
    goal_id = goal["id"]

    # 1. Deposit contribution
    dep_payload = {
        "entry_type": "DEPOSIT",
        "amount": "1500.00",
        "entry_date": date.today().isoformat(),
        "notes": "First paycheck allocation",
    }
    res = client.post(f"/api/v1/finance/savings-goals/{goal_id}/entries", json=dep_payload, headers=auth_headers_a)
    assert res.status_code == 201

    # Check updated goal
    updated_goal = client.get(f"/api/v1/finance/savings-goals/{goal_id}", headers=auth_headers_a).json()
    assert Decimal(updated_goal["current_amount"]) == Decimal("1500.00")
    assert Decimal(updated_goal["remaining_amount"]) == Decimal("3500.00")
    assert updated_goal["progress_percentage"] == 30.0

    # 2. Reject excess withdrawal
    excess_withdrawal = {
        "entry_type": "WITHDRAWAL",
        "amount": "2000.00",
        "entry_date": date.today().isoformat(),
    }
    res_err = client.post(f"/api/v1/finance/savings-goals/{goal_id}/entries", json=excess_withdrawal, headers=auth_headers_a)
    assert res_err.status_code == 400
    assert "Cannot withdraw" in res_err.json()["detail"]

    # 3. Valid withdrawal of 500
    valid_withdrawal = {
        "entry_type": "WITHDRAWAL",
        "amount": "500.00",
        "entry_date": date.today().isoformat(),
    }
    res_ok = client.post(f"/api/v1/finance/savings-goals/{goal_id}/entries", json=valid_withdrawal, headers=auth_headers_a)
    assert res_ok.status_code == 201
    goal_after_w = client.get(f"/api/v1/finance/savings-goals/{goal_id}", headers=auth_headers_a).json()
    assert Decimal(goal_after_w["current_amount"]) == Decimal("1000.00")


def test_overview_and_analytics_multi_currency(client: TestClient, auth_headers_a: dict):
    # Setup USD and EUR accounts
    client.post("/api/v1/finance/accounts", json={
        "name": "US Dollar Checking",
        "account_type": "BANK_ACCOUNT",
        "currency": "USD",
        "opening_balance": "3000.00",
    }, headers=auth_headers_a)

    client.post("/api/v1/finance/accounts", json={
        "name": "Euro Account",
        "account_type": "BANK_ACCOUNT",
        "currency": "EUR",
        "opening_balance": "2500.00",
    }, headers=auth_headers_a)

    res = client.get("/api/v1/finance/overview", headers=auth_headers_a)
    assert res.status_code == 200
    overview = res.json()
    currencies = [c["currency"] for c in overview["currencies"]]
    assert "USD" in currencies
    assert "EUR" in currencies

    # Currencies are separated and never blindly summed
    usd_summary = next(c for c in overview["currencies"] if c["currency"] == "USD")
    eur_summary = next(c for c in overview["currencies"] if c["currency"] == "EUR")
    assert Decimal(usd_summary["net_worth"]) == Decimal("3000.00")
    assert Decimal(eur_summary["net_worth"]) == Decimal("2500.00")


def test_csv_export_and_formula_injection_mitigation(client: TestClient, auth_headers_a: dict):
    acc = client.post("/api/v1/finance/accounts", json={
        "name": "Export Test Account",
        "account_type": "BANK_ACCOUNT",
        "currency": "USD",
        "opening_balance": "100.00",
    }, headers=auth_headers_a).json()

    # Create transaction with dangerous injection formula strings
    client.post("/api/v1/finance/transactions", json={
        "account_id": acc["id"],
        "transaction_type": "EXPENSE",
        "amount": "10.00",
        "currency": "USD",
        "description": "=SUM(A1:A10)",
        "merchant_or_source": "+cmd|' /C calc'!A0",
        "notes": "@HYPERLINK('http://evil.com')",
        "transaction_date": date.today().isoformat(),
    }, headers=auth_headers_a)

    res = client.get("/api/v1/finance/export/csv", headers=auth_headers_a)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    content = res.text

    # Formulas must be escaped with single-quote prefix
    assert "'=SUM(A1:A10)" in content
    assert "'+cmd|' /C calc'!A0" in content
    assert "'@HYPERLINK('http://evil.com')" in content


def test_multi_user_data_isolation(client: TestClient, auth_headers_a: dict, auth_headers_b: dict):
    # User A creates account
    acc = client.post("/api/v1/finance/accounts", json={
        "name": "User Secret Account",
        "account_type": "CASH",
        "currency": "USD",
        "opening_balance": "999.00",
    }, headers=auth_headers_a).json()

    # User B cannot access User A's account directly
    res = client.get(f"/api/v1/finance/accounts/{acc['id']}", headers=auth_headers_b)
    assert res.status_code == 404

    # User B's account list does not contain User A's account
    b_accounts = client.get("/api/v1/finance/accounts", headers=auth_headers_b).json()
    assert not any(a["id"] == acc["id"] for a in b_accounts)


def test_advance_next_occurrence_calendar_math():
    from app.services.finance_service import advance_next_occurrence

    # Leap day February 29 anchor
    leap_start = date(2024, 2, 29)
    # Year 1 (non-leap 2025): should be clamped to Feb 28
    y1 = advance_next_occurrence(leap_start, "YEARLY", anchor_day=leap_start.day)
    assert y1 == date(2025, 2, 28)

    # Year 2 (non-leap 2026): should remain Feb 28
    y2 = advance_next_occurrence(y1, "YEARLY", anchor_day=leap_start.day)
    assert y2 == date(2026, 2, 28)

    # Year 3 (non-leap 2027): should remain Feb 28
    y3 = advance_next_occurrence(y2, "YEARLY", anchor_day=leap_start.day)
    assert y3 == date(2027, 2, 28)

    # Year 4 (leap 2028): anchor_day 29 restores the date to February 29
    y4 = advance_next_occurrence(y3, "YEARLY", anchor_day=leap_start.day)
    assert y4 == date(2028, 2, 29)

    # Month end: Day 31 anchored across 30-day and 28-day months
    jan31 = date(2025, 1, 31)
    feb = advance_next_occurrence(jan31, "MONTHLY", anchor_day=31)
    assert feb == date(2025, 2, 28)

    mar = advance_next_occurrence(feb, "MONTHLY", anchor_day=31)
    assert mar == date(2025, 3, 31)

    apr = advance_next_occurrence(mar, "MONTHLY", anchor_day=31)
    assert apr == date(2025, 4, 30)

    may = advance_next_occurrence(apr, "MONTHLY", anchor_day=31)
    assert may == date(2025, 5, 31)
