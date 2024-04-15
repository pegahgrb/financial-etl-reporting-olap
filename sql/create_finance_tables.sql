DROP TABLE IF EXISTS stg_transactions;
DROP TABLE IF EXISTS dim_account;
DROP TABLE IF EXISTS dim_department;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS fact_finance;

CREATE TABLE stg_transactions (
    transaction_id TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    account_code TEXT NOT NULL,
    department_code TEXT NOT NULL,
    amount REAL NOT NULL,
    amount_type TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE dim_account (
    account_key INTEGER PRIMARY KEY,
    account_code TEXT NOT NULL UNIQUE,
    account_name TEXT NOT NULL,
    account_group TEXT NOT NULL,
    reporting_group TEXT NOT NULL
);

CREATE TABLE dim_department (
    department_key INTEGER PRIMARY KEY,
    department_code TEXT NOT NULL UNIQUE,
    department_name TEXT NOT NULL
);

CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date TEXT NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    quarter INTEGER NOT NULL
);

CREATE TABLE fact_finance (
    finance_key INTEGER PRIMARY KEY,
    transaction_id TEXT NOT NULL UNIQUE,
    date_key INTEGER NOT NULL,
    account_key INTEGER NOT NULL,
    department_key INTEGER NOT NULL,
    amount REAL NOT NULL,
    amount_type TEXT NOT NULL,
    reporting_group TEXT NOT NULL,
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (account_key) REFERENCES dim_account(account_key),
    FOREIGN KEY (department_key) REFERENCES dim_department(department_key)
);

