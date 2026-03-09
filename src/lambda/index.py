import json
import urllib.parse
import boto3
import os
import uuid
from datetime import datetime

ecs = boto3.client('ecs')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

TABLE_NAME = os.environ['DYNAMODB_TABLE']
CLUSTER = os.environ['ECS_CLUSTER']
TASK_DEF = os.environ['ECS_TASK_DEF']
SUBNETS = os.environ['SUBNETS'].split(',')

def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)
    
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        
        job_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Log Audit: Upload
        table.put_item(Item={'job_id': job_id, 'timestamp': timestamp, 'status': 'Upload', 'file': key})
        
        # Validation: Check tags for organization-id
        try:
            tags = s3.get_object_tagging(Bucket=bucket, Key=key)
            tag_dict = {t['Key']: t['Value'] for t in tags.get('TagSet', [])}
            
            if 'organization-id' not in tag_dict:
                print(f"Validation failed: No organization-id tag found for {key}")
                table.put_item(Item={'job_id': job_id, 'timestamp': datetime.utcnow().isoformat(), 'status': 'Failed Validation (No org-id)', 'file': key})
                continue
                
        except Exception as e:
            print(f"Error reading tags: {e}")
            continue

        # Log Audit: Trigger
        table.put_item(Item={'job_id': job_id, 'timestamp': datetime.utcnow().isoformat(), 'status': 'Trigger', 'file': key})

        # Execution: Trigger ECS Fargate Task
        try:
            response = ecs.run_task(
                cluster=CLUSTER,
                launchType='FARGATE',
                taskDefinition=TASK_DEF,
                networkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': SUBNETS,
                        'assignPublicIp': 'ENABLED'
                    }
                },
                overrides={
                    'containerOverrides': [{
                        'name': 'processor',
                        'environment': [
                            {'name': 'S3_BUCKET', 'value': bucket},
                            {'name': 'S3_KEY', 'value': key},
                            {'name': 'JOB_ID', 'value': job_id},
                            {'name': 'DYNAMODB_TABLE', 'value': TABLE_NAME},
                            {'name': 'ORG_ID', 'value': tag_dict['organization-id']}
                        ]
                    }]
                }
            )
            print(f"Started ECS task for {key}: {response.get('tasks', [{}])[0].get('taskArn')}")
        except Exception as e:
            print(f"Error starting ECS task: {e}")
            table.put_item(Item={'job_id': job_id, 'timestamp': datetime.utcnow().isoformat(), 'status': 'Failed Trigger', 'error': str(e)})