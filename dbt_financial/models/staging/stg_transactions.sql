{{ config(materialized='view', schema='SILVER') }}

SELECT
    transaction_id,
    customer_id,
    account_id,
    transaction_type,
    amount,
    currency,
    merchant_name,
    merchant_category,
    country_code,
    transaction_status,
    is_flagged,
    transaction_ts,
    amount_usd,
    risk_level,
    day_of_week,
    hour_of_day,
    is_weekend,
    processed_at
FROM {{ source('silver', 'clean_transactions') }}