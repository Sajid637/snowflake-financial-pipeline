import boto3
import pandas as pd
import random
import uuid
import os
from faker import Faker
from datetime import datetime
from dotenv import load_dotenv

# load_dotenv()

# fake = Faker()

load_dotenv(dotenv_path=r"C:\Users\LENOVO\Documents\snowflake-financial-pipeline\.env")

fake = Faker()

S3_BUCKET   = os.getenv("S3_BUCKET_NAME")
AWS_REGION  = os.getenv("AWS_REGION")

# S3_BUCKET   = os.getenv("S3_BUCKET_NAME")
# AWS_REGION  = os.getenv("AWS_REGION")
S3_FOLDER   = "raw/transactions/"
BATCH_SIZE  = 500
NUM_BATCHES = 5

TRANSACTION_TYPES    = ["CREDIT", "DEBIT", "TRANSFER"]
CURRENCIES           = ["EUR", "USD", "GBP", "CHF", "SEK"]
MERCHANT_CATEGORIES  = ["RETAIL", "FOOD", "TRAVEL", "ENTERTAINMENT",
                         "HEALTHCARE", "UTILITIES", "EDUCATION", "FINANCE"]
TRANSACTION_STATUSES = ["COMPLETED", "PENDING", "FAILED"]
COUNTRY_CODES        = ["DE", "FR", "NL", "GB", "SE", "ES", "IT", "PL"]

def generate_transaction():
    transaction_ts = fake.date_time_between(start_date="-30d", end_date="now")
    amount = round(random.uniform(1.0, 15000.0), 2)
    is_flagged = amount > 10000 or random.random() < 0.03

    return {
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
        "is_flagged":         is_flagged,
        "transaction_ts":     transaction_ts.strftime("%Y-%m-%d %H:%M:%S"),
    }

def generate_batch(batch_size):
    return pd.DataFrame([generate_transaction() for _ in range(batch_size)])

def upload_to_s3(df, batch_number):
    s3_client = boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )

    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename   = f"transactions_batch_{batch_number}_{timestamp}.csv"
    s3_key     = f"{S3_FOLDER}{filename}"
    local_path = f"transactions_temp_{batch_number}.csv"

    df.to_csv(local_path, index=False)
    s3_client.upload_file(local_path, S3_BUCKET, s3_key)
    print(f"Batch {batch_number} uploaded to s3://{S3_BUCKET}/{s3_key} ({len(df)} records)")
    os.remove(local_path)

def main():
    print(f"Starting transaction generator — {NUM_BATCHES} batches of {BATCH_SIZE} records")
    print(f"Target: s3://{S3_BUCKET}/{S3_FOLDER}\n")

    for i in range(1, NUM_BATCHES + 1):
        df = generate_batch(BATCH_SIZE)
        upload_to_s3(df, i)

    print(f"\nDone! {NUM_BATCHES * BATCH_SIZE} total records uploaded to S3.")

if __name__ == "__main__":
    main()