---
name: terraform
description: Generate Terraform infrastructure as code
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
argument-hint: "[aws|gcp|azure] [--ecs|--eks|--lambda]"
---

# Terraform Command

Generate Terraform infrastructure code for cloud deployment.

## Execution Steps

1. **Detect cloud provider**
   - Check argument for provider
   - Look for existing Terraform config
   - Default to AWS if not specified

2. **Determine infrastructure needs**
   - Analyze project type
   - Check for existing Docker/K8s config
   - Identify database requirements

3. **Generate Terraform modules**
   - VPC and networking
   - Compute (ECS, EKS, or Lambda)
   - Database (RDS if needed)
   - Load balancer
   - DNS and certificates

4. **Create supporting files**
   - Variables file
   - Outputs file
   - Example tfvars
   - Backend configuration

## Arguments

- `aws`: AWS infrastructure (default)
- `gcp`: Google Cloud Platform
- `azure`: Microsoft Azure
- `--ecs`: ECS Fargate compute
- `--eks`: EKS Kubernetes
- `--lambda`: Lambda serverless

## Example Usage

```
/terraform                   # AWS with auto-detected compute
/terraform aws --ecs         # AWS with ECS Fargate
/terraform aws --eks         # AWS with EKS
/terraform gcp               # Google Cloud
/terraform azure             # Azure
```

## Output Files

```
terraform/
├── main.tf
├── variables.tf
├── outputs.tf
├── providers.tf
├── versions.tf
├── terraform.tfvars.example
└── modules/
    ├── vpc/
    ├── ecs/
    ├── rds/
    └── alb/
```

## Terraform Commands

After generation:
```bash
cd terraform

# Initialize
terraform init

# Plan
terraform plan -out=tfplan

# Apply
terraform apply tfplan

# Destroy (careful!)
terraform destroy
```

## Required Setup

1. Configure AWS credentials
2. Create S3 bucket for state
3. Create DynamoDB table for locking
4. Set variables in terraform.tfvars
