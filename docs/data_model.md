# Data Model

## Dimensions

- `dim_account`
- `dim_department`
- `dim_date`

## Fact table

`fact_finance`

Fields include:

- transaction_id
- date_key
- account_key
- department_key
- amount
- amount_type
- reporting_group

## Modeling approach

- account dimension carries reporting category and account group
- department dimension supports cost-center reporting
- date dimension supports monthly trend analysis
- fact table stores signed transaction amounts for reporting

