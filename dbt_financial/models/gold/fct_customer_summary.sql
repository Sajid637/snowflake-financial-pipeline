{{ config(materialized='table', schema='GOLD') }}

SELECT
    customer_id,
    COUNT(DISTINCT account_id)              AS total_accounts,
    COUNT(*)                                AS total_transactions,
    SUM(amount_usd)                         AS lifetime_value_usd,
    AVG(amount_usd)                         AS avg_transaction_usd,
    MAX(amount_usd)                         AS max_transaction_usd,
    SUM(CASE WHEN is_flagged = TRUE THEN 1 ELSE 0 END)  AS flagged_transactions,
    SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_risk_count,
    COUNT(DISTINCT merchant_category)       AS unique_categories,
    COUNT(DISTINCT country_code)            AS countries_transacted,
    MIN(transaction_ts)                     AS first_transaction_ts,
    MAX(transaction_ts)                     AS last_transaction_ts,
    CASE
        WHEN SUM(CASE WHEN is_flagged = TRUE THEN 1 ELSE 0 END) > 3 THEN 'HIGH RISK'
        WHEN SUM(CASE WHEN is_flagged = TRUE THEN 1 ELSE 0 END) > 1 THEN 'MEDIUM RISK'
        ELSE 'LOW RISK'
    END                                     AS customer_risk_profile
FROM {{ ref('stg_transactions') }}
GROUP BY 1
ORDER BY lifetime_value_usd DESC