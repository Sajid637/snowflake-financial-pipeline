{{ config(materialized='table', schema='GOLD') }}

SELECT
    DATE(transaction_ts)            AS transaction_date,
    country_code,
    merchant_category,
    risk_level,
    currency,
    COUNT(*)                        AS total_transactions,
    SUM(CASE WHEN is_flagged = TRUE THEN 1 ELSE 0 END)  AS flagged_count,
    ROUND(
        SUM(CASE WHEN is_flagged = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    )                               AS fraud_rate_pct,
    SUM(CASE WHEN is_flagged = TRUE THEN amount_usd ELSE 0 END) AS flagged_amount_usd,
    AVG(CASE WHEN is_flagged = TRUE THEN amount_usd END) AS avg_flagged_amount_usd,
    SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_count,
    ROUND(
        SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    )                               AS failure_rate_pct
FROM {{ ref('stg_transactions') }}
WHERE transaction_ts IS NOT NULL
GROUP BY 1,2,3,4,5
ORDER BY flagged_count DESC