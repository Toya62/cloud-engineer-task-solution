import os
import boto3
from datetime import datetime

bucket = os.environ.get('S3_BUCKET')
key = os.environ.get('S3_KEY')
job_id = os.environ.get('JOB_ID')
table_name = os.environ.get('DYNAMODB_TABLE')
org_id = os.environ.get('ORG_ID')

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')
table = dynamodb.Table(table_name)

def log_audit(status):
    table.put_item(Item={
        'job_id': job_id,
        'timestamp': datetime.utcnow().isoformat(),
        'status': status,
        'file': key,
        'org_id': org_id
    })
    print(f"[{datetime.utcnow().isoformat()}] Audit logged: {status}")

def main():
    if not all([bucket, key, job_id, table_name]):
        print("Missing required environment variables.")
        return

    # Audit: Processing Start
    log_audit('Processing Start')

    try:
        # Dummy script: log the file name and size
        response = s3.head_object(Bucket=bucket, Key=key)
        size_bytes = response.get('ContentLength', 0)
        
        print(f"--- Processing Details ---")
        print(f"Organization ID: {org_id}")
        print(f"File Name: {key}")
        print(f"File Size: {size_bytes} bytes")
        print(f"--------------------------")
        
        # Audit: Completion
        log_audit('Completion')

    except Exception as e:
        print(f"Error processing file: {e}")
        log_audit('Processing Failed')

if __name__ == '__main__':
    main()