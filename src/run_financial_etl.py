from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "output"


def load_sources() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    accounts = pd.read_csv(RAW_DIR / "accounts.csv")
    departments = pd.read_csv(RAW_DIR / "departments.csv")
    calendar = pd.read_csv(RAW_DIR / "calendar.csv")
    transactions = pd.read_csv(RAW_DIR / "transactions.csv")
    return accounts, departments, calendar, transactions


def clean_sources(
    accounts: pd.DataFrame,
    departments: pd.DataFrame,
    calendar: pd.DataFrame,
    transactions: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    for frame in (accounts, departments, calendar, transactions):
        text_columns = frame.select_dtypes(include="object").columns
        for column in text_columns:
            frame[column] = frame[column].astype(str).str.strip()

    transactions["transaction_date"] = pd.to_datetime(transactions["transaction_date"]).dt.date.astype(str)
    calendar["full_date"] = pd.to_datetime(calendar["full_date"]).dt.date.astype(str)
    transactions["signed_amount"] = transactions.apply(
        lambda row: row["amount"] if row["amount_type"] == "Credit" else -row["amount"],
        axis=1,
    )
    return accounts, departments, calendar, transactions


def build_dimensions(
    accounts: pd.DataFrame,
    departments: pd.DataFrame,
    calendar: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dim_account = accounts.copy()
    dim_account.insert(0, "account_key", range(1, len(dim_account) + 1))

    dim_department = departments.copy()
    dim_department.insert(0, "department_key", range(1, len(dim_department) + 1))

    dim_date = calendar.copy()
    dim_date.insert(0, "date_key", range(1, len(dim_date) + 1))

    return dim_account, dim_department, dim_date


def build_fact_finance(
    transactions: pd.DataFrame,
    dim_account: pd.DataFrame,
    dim_department: pd.DataFrame,
    dim_date: pd.DataFrame,
) -> pd.DataFrame:
    fact_finance = (
        transactions.merge(
            dim_account[["account_key", "account_code", "reporting_group"]],
            on="account_code",
            how="left",
        )
        .merge(
            dim_department[["department_key", "department_code"]],
            on="department_code",
            how="left",
        )
        .merge(
            dim_date[["date_key", "full_date"]],
            left_on="transaction_date",
            right_on="full_date",
            how="left",
        )
    )

    required_columns = ["account_key", "department_key", "date_key"]
    if fact_finance[required_columns].isnull().any().any():
        missing_rows = fact_finance[fact_finance[required_columns].isnull().any(axis=1)]
        raise ValueError(f"Missing dimension mappings found:\n{missing_rows.to_string(index=False)}")

    fact_finance.insert(0, "finance_key", range(1, len(fact_finance) + 1))
    fact_finance = fact_finance[
        [
            "finance_key",
            "transaction_id",
            "date_key",
            "account_key",
            "department_key",
            "signed_amount",
            "amount_type",
            "reporting_group",
        ]
    ].rename(columns={"signed_amount": "amount"})

    return fact_finance


def build_reporting_outputs(
    transactions: pd.DataFrame,
    accounts: pd.DataFrame,
    departments: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    enriched = transactions.merge(accounts, on="account_code", how="left").merge(
        departments, on="department_code", how="left"
    )

    enriched["year_month"] = pd.to_datetime(enriched["transaction_date"]).dt.to_period("M").astype(str)

    monthly = (
        enriched.groupby(["year_month", "reporting_group"])["signed_amount"]
        .sum()
        .reset_index()
        .pivot(index="year_month", columns="reporting_group", values="signed_amount")
        .fillna(0)
        .reset_index()
    )
    monthly["Gross Profit"] = monthly["Revenue"] + monthly["COGS"]
    monthly["Operating Profit"] = monthly["Revenue"] + monthly["COGS"] + monthly["OPEX"]

    department_expense = (
        enriched[enriched["reporting_group"] == "OPEX"]
        .groupby(["department_name", "year_month"])["signed_amount"]
        .sum()
        .reset_index()
    )
    department_expense["expense_amount"] = department_expense["signed_amount"].abs()
    department_expense = department_expense.drop(columns=["signed_amount"])

    account_group_summary = (
        enriched.groupby(["account_group", "reporting_group"])["signed_amount"]
        .sum()
        .reset_index()
    )
    account_group_summary["absolute_amount"] = account_group_summary["signed_amount"].abs()

    return monthly, department_expense, account_group_summary


def save_outputs(
    monthly: pd.DataFrame,
    department_expense: pd.DataFrame,
    account_group_summary: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    monthly.to_csv(OUTPUT_DIR / "monthly_financial_summary.csv", index=False)
    department_expense.to_csv(OUTPUT_DIR / "department_expense_summary.csv", index=False)
    account_group_summary.to_csv(OUTPUT_DIR / "account_group_summary.csv", index=False)


def print_summary(monthly: pd.DataFrame, department_expense: pd.DataFrame) -> None:
    print("Financial ETL pipeline completed successfully.")
    print()
    print("Monthly financial summary:")
    print(monthly.to_string(index=False))
    print()
    print("Department expense summary:")
    print(department_expense.to_string(index=False))


def main() -> None:
    accounts, departments, calendar, transactions = load_sources()
    accounts, departments, calendar, transactions = clean_sources(
        accounts,
        departments,
        calendar,
        transactions,
    )
    dim_account, dim_department, dim_date = build_dimensions(accounts, departments, calendar)
    _ = build_fact_finance(transactions, dim_account, dim_department, dim_date)
    monthly, department_expense, account_group_summary = build_reporting_outputs(
        transactions,
        accounts,
        departments,
    )
    save_outputs(monthly, department_expense, account_group_summary)
    print_summary(monthly, department_expense)


if __name__ == "__main__":
    main()
