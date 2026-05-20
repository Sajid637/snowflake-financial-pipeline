{{ config(materialized='table', schema='GOLD') }}

SELECT
    DATE(transaction_ts)            AS transaction_date,
    transaction_type,
    currency,
    country_code,
    merchant_category,
    risk_level,
    COUNT(*)                        AS total_transactions,
    SUM(amount_usd)                 AS total_amount_usd,
    AVG(amount_usd)                 AS avg_amount_usd,
    MAX(amount_usd)                 AS max_amount_usd,
    MIN(amount_usd)                 AS min_amount_usd,
    SUM(CASE WHEN is_flagged = TRUE THEN 1 ELSE 0 END) AS flagged_count,
    SUM(CASE WHEN transaction_status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_count,
    SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_count
FROM {{ ref('stg_transactions') }}
WHERE transaction_ts IS NOT NULL
GROUP BY 1,2,3,4,5,6
ORDER BY 1 DESC