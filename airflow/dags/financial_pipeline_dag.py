# ============================================
# Financial Pipeline - Apache Airflow DAG
# Orchestrates: Data Generation → S3 → dbt
# ============================================

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from datetime import datetime, timedelta
import boto3
import pandas as pd
import random
import uuid
import os
from faker import Faker

# ── Default Arguments ───────────────────────
default_args = {
    'owner':            'sajid_abbas',
    'depends_on_past':  False,
    'start_date': datetime(2026, 5, 1),
    'email_on_failure': False,
    'email_on_retry':   False,
    'retries':          2,
    'retry_delay':      timedelta(minutes=5),
}

# ── DAG Definition ───────────────────────────
dag = DAG(
    'financial_pipeline',
    default_args=default_args,
    description='End-to-end financial transaction pipeline',
    schedule='0 */6 * * *',
    catchup=False,
    tags=['financial', 'snowflake', 'dbt', 's3']
)

# ── Task 1: Generate & Upload to S3 ──────────
def generate_and_upload():
    fake = Faker()
    TRANSACTION_TYPES    = ["CREDIT", "DEBIT", "TRANSFER"]
    CURRENCIES           = ["EUR", "USD", "GBP", "CHF", "SEK"]
    MERCHANT_CATEGORIES  = ["RETAIL", "FOOD", "TRAVEL", "ENTERTAINMENT",
                             "HEALTHCARE", "UTILITIES", "EDUCATION", "FINANCE"]
    TRANSACTION_STATUSES = ["COMPLETED", "PENDING", "FAILED"]
    COUNTRY_CODES        = ["DE", "FR", "NL", "GB", "SE", "ES", "IT", "PL"]

    records = []
    for _ in range(500):
        amount = round(random.uniform(1.0, 15000.0), 2)
        records.append({
            "transaction_id":     str(uuid.uuid4()),
            "customer_id":        f"CUST_{random.randint(1000, 9999)}",
            "account_id":         f"ACC_{random.randint(10000, 99999)}",
            "transaction_type":   random.choice(TRANSACTION_TYPES),
            "amount":             amount,
            "currency":           random.choice(CURRENCIES),
            "merchant_name":      fake.company(),
            "merchant_category":  random.choice(MERCHANT_CATEGORIES),
            "country_code":       random.choice(COUNTRY_CODES),
            "transaction_status": random.choice(TRANSACTION_STATUSES),
            "is_flagged":         amount > 10000 or random.random() < 0.03,
            "transaction_ts":     fake.date_time_between(
                                    start_date="-1d",
                                    end_date="now"
                                  ).strftime("%Y-%m-%d %H:%M:%S"),
        })

    df = pd.DataFrame(records)
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename   = f"transactions_airflow_{timestamp}.csv"
    local_path = f"/tmp/{filename}"
    df.to_csv(local_path, index=False)

    s3 = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    s3.upload_file(
        local_path,
        "snowflake-financial-pipeline-sajid",
        f"raw/transactions/{filename}"
    )
    os.remove(local_path)
    print(f"✅ Uploaded {len(df)} records → S3: {filename}")

task_generate_data = PythonOperator(
    task_id='generate_and_upload_to_s3',
    python_callable=generate_and_upload,
    dag=dag
)

# ── Task 2: Wait for Snowpipe Ingestion ───────
task_wait = BashOperator(
    task_id='wait_for_snowpipe_ingestion',
    bash_command='sleep 120',
    dag=dag
)

# ── Task 3: Run dbt Models ────────────────────
task_dbt_run = BashOperator(
    task_id='dbt_run_gold_models',
    bash_command='cd /usr/local/airflow/dbt_financial && dbt run --select gold',
    dag=dag
)

# ── Task 4: Run dbt Tests ─────────────────────
task_dbt_test = BashOperator(
    task_id='dbt_test_data_quality',
    bash_command='cd /usr/local/airflow/dbt_financial && dbt test',
    dag=dag
)

# ── Pipeline Order ────────────────────────────
task_generate_data >> task_wait >> task_dbt_run >> task_dbt_test