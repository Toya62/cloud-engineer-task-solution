# Secure Data Orchestration & Hybrid Relay

## Prerequisites
- AWS CLI configured
- Terraform installed
- Docker installed

## 1. Deploy Infrastructure
Navigate to the `/infra` directory:
```bash
cd infra
terraform init
terraform apply -auto-approve
```
*Note the output values for `s3_bucket_name` and `ecr_repository_url`.*

## 2. Build and Push the Docker Image
Navigate to the `/src/processor` directory:
```bash
cd src/processor

# Login to ECR (Replace <region> and <account_id>)
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account_id>.dkr.ecr.<region>.amazonaws.com

# Build the image
docker build -t data-processor .

# Tag and Push
docker tag data-processor:latest <ecr_repository_url>:latest
docker push <ecr_repository_url>:latest
```

## 3. Test the Prototype
1. Create a dummy zip file: `touch test.zip && zip test.zip test.zip`
2. Upload to the bucket and apply the required tag `organization-id`:
```bash
aws s3api put-object --bucket <s3_bucket_name> --key test.zip --body test.zip --tagging "organization-id=org-123"
```
3. Check the DynamoDB table `AuditLog` to view the Upload -> Trigger -> Processing Start -> Completion transitions.
4. View the ECS Fargate logs in CloudWatch under `/ecs/data-processor`.