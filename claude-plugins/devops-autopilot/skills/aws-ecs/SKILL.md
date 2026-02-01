# AWS ECS

This skill provides comprehensive knowledge for AWS Elastic Container Service. It activates when users mention "ECS", "AWS ECS", "Fargate", "ECR", "elastic container", "AWS containers", or need to deploy containers to AWS.

---

## ECS Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    ECS Cluster                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Service   │  │   Service   │  │   Service   │     │
│  │  (Frontend) │  │  (Backend)  │  │   (Worker)  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│        │                │                │              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │    Task     │  │    Task     │  │    Task     │     │
│  │ Definition  │  │ Definition  │  │ Definition  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│        │                │                │              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Container  │  │  Container  │  │  Container  │     │
│  │   (Fargate) │  │   (Fargate) │  │   (Fargate) │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## ECR - Container Registry

### Create Repository
```bash
# Create ECR repository
aws ecr create-repository \
    --repository-name my-app \
    --image-scanning-configuration scanOnPush=true \
    --region us-east-1
```

### Push Image to ECR
```bash
# Get login token
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t my-app .
docker tag my-app:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest

# Push
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest
```

## Task Definition

### JSON Format
```json
{
  "family": "my-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 3000,
          "hostPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "NODE_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:ssm:us-east-1:123456789012:parameter/prod/database_url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/my-app",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "app"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:3000/api/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Register Task Definition
```bash
aws ecs register-task-definition \
    --cli-input-json file://task-definition.json
```

## ECS Service

### Create Service
```bash
aws ecs create-service \
    --cluster my-cluster \
    --service-name my-app \
    --task-definition my-app:1 \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=DISABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=app,containerPort=3000"
```

### Update Service
```bash
# Update with new task definition
aws ecs update-service \
    --cluster my-cluster \
    --service my-app \
    --task-definition my-app:2 \
    --force-new-deployment

# Wait for stable
aws ecs wait services-stable \
    --cluster my-cluster \
    --services my-app
```

## IAM Roles

### Task Execution Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "ssm:GetParameters",
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "*"
    }
  ]
}
```

### Task Role (App Permissions)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "sqs:SendMessage",
        "sqs:ReceiveMessage"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket/*",
        "arn:aws:sqs:us-east-1:123456789012:my-queue"
      ]
    }
  ]
}
```

## Auto Scaling

### Application Auto Scaling
```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id service/my-cluster/my-app \
    --scalable-dimension ecs:service:DesiredCount \
    --min-capacity 2 \
    --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --resource-id service/my-cluster/my-app \
    --scalable-dimension ecs:service:DesiredCount \
    --policy-name cpu-scaling \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration '{
        "TargetValue": 70.0,
        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
        },
        "ScaleOutCooldown": 60,
        "ScaleInCooldown": 120
    }'
```

## Blue/Green Deployment

### With CodeDeploy
```bash
# Create deployment group
aws deploy create-deployment-group \
    --application-name my-app \
    --deployment-group-name production \
    --service-role-arn arn:aws:iam::123456789012:role/CodeDeployServiceRole \
    --deployment-config-name CodeDeployDefault.ECSLinear10PercentEvery1Minutes \
    --ecs-services clusterName=my-cluster,serviceName=my-app \
    --load-balancer-info targetGroupPairInfoList=[{targetGroups=[{name=tg-blue},{name=tg-green}],prodTrafficRoute={listenerArns=[arn:...]}}]
```

## CLI Commands Reference

```bash
# List clusters
aws ecs list-clusters

# Describe cluster
aws ecs describe-clusters --clusters my-cluster

# List services
aws ecs list-services --cluster my-cluster

# Describe service
aws ecs describe-services --cluster my-cluster --services my-app

# List tasks
aws ecs list-tasks --cluster my-cluster --service-name my-app

# Describe tasks
aws ecs describe-tasks --cluster my-cluster --tasks task-id

# Get task logs
aws logs get-log-events \
    --log-group-name /ecs/my-app \
    --log-stream-name app/app/task-id

# Stop task
aws ecs stop-task --cluster my-cluster --task task-id

# Scale service
aws ecs update-service --cluster my-cluster --service my-app --desired-count 5
```

## Common Issues and Solutions

### "CannotPullContainerError"
- Check ECR repository permissions
- Verify task execution role has ECR access
- Check VPC endpoints if in private subnet

### "ResourceNotFoundException"
- Verify cluster, service names exist
- Check task definition is registered
- Confirm IAM roles exist

### "OutOfMemory" or "OutOfCpu"
- Increase task CPU/memory
- Check container memory limits
- Review application memory usage

### Tasks keep stopping
- Check CloudWatch logs for errors
- Verify health check configuration
- Review security group rules
- Check environment variables/secrets

## GitHub Actions Deployment

```yaml
name: Deploy to ECS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/my-app:$IMAGE_TAG .
          docker push $ECR_REGISTRY/my-app:$IMAGE_TAG

      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster my-cluster \
            --service my-app \
            --force-new-deployment
          aws ecs wait services-stable \
            --cluster my-cluster \
            --services my-app
```

## Autonomous ECS Setup

When deploying to ECS:
1. Create ECR repository
2. Build and push Docker image
3. Create task definition with proper configuration
4. Set up ECS cluster and service
5. Configure load balancer and target groups
6. Set up auto scaling
7. Configure logging and monitoring
8. Use Context7 for latest ECS features
