# GitLab CI

This skill provides comprehensive knowledge for GitLab CI/CD pipelines. It activates when users mention "gitlab ci", "gitlab pipeline", ".gitlab-ci.yml", "gitlab runner", or need to set up automated builds and deployments for GitLab repositories.

---

## Pipeline File Structure

### Basic Pipeline
```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

variables:
  NODE_VERSION: "20"

default:
  image: node:${NODE_VERSION}
  cache:
    paths:
      - node_modules/

build:
  stage: build
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 hour

test:
  stage: test
  script:
    - npm ci
    - npm run lint
    - npm test

deploy:
  stage: deploy
  script:
    - npm run deploy
  only:
    - main
  environment:
    name: production
    url: https://example.com
```

## Frontend Framework Pipelines

### Next.js
```yaml
stages:
  - build
  - test
  - deploy

variables:
  NODE_VERSION: "20"

default:
  image: node:${NODE_VERSION}

cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - node_modules/
    - .next/cache/

build:
  stage: build
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - .next/
    expire_in: 1 day

test:
  stage: test
  script:
    - npm ci
    - npm run lint
    - npm test
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'

deploy_vercel:
  stage: deploy
  image: node:${NODE_VERSION}
  script:
    - npm i -g vercel
    - vercel pull --yes --environment=production --token=$VERCEL_TOKEN
    - vercel build --prod --token=$VERCEL_TOKEN
    - vercel deploy --prebuilt --prod --token=$VERCEL_TOKEN
  only:
    - main
  environment:
    name: production
```

### React (Vite)
```yaml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  image: node:20
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 week

test:
  stage: test
  image: node:20
  script:
    - npm ci
    - npm run lint
    - npm test -- --coverage

pages:
  stage: deploy
  script:
    - mv dist public
  artifacts:
    paths:
      - public
  only:
    - main
```

## Docker Build & Push

```yaml
stages:
  - build
  - push
  - deploy

variables:
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE
  DOCKER_TAG: $CI_COMMIT_SHA

build_docker:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $DOCKER_IMAGE:$DOCKER_TAG .
    - docker push $DOCKER_IMAGE:$DOCKER_TAG
    - docker tag $DOCKER_IMAGE:$DOCKER_TAG $DOCKER_IMAGE:latest
    - docker push $DOCKER_IMAGE:latest
  only:
    - main
```

## Kubernetes Deployment

```yaml
deploy_k8s:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl config set-cluster k8s --server="$KUBE_URL" --certificate-authority="$KUBE_CA_PEM_FILE"
    - kubectl config set-credentials admin --token="$KUBE_TOKEN"
    - kubectl config set-context default --cluster=k8s --user=admin
    - kubectl config use-context default
    - sed -i "s/:latest/:$CI_COMMIT_SHA/g" k8s/deployment.yaml
    - kubectl apply -f k8s/
    - kubectl rollout status deployment/app -n production
  environment:
    name: production
  only:
    - main
```

## AWS ECS Deployment

```yaml
deploy_ecs:
  stage: deploy
  image: amazon/aws-cli
  script:
    - aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
    - aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
    - aws configure set region $AWS_REGION
    - aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --force-new-deployment
    - aws ecs wait services-stable --cluster $ECS_CLUSTER --services $ECS_SERVICE
  only:
    - main
```

## Multi-Environment Deployment

```yaml
stages:
  - build
  - test
  - deploy_staging
  - deploy_production

deploy_staging:
  stage: deploy_staging
  script:
    - ./deploy.sh staging
  environment:
    name: staging
    url: https://staging.example.com
  only:
    - develop

deploy_production:
  stage: deploy_production
  script:
    - ./deploy.sh production
  environment:
    name: production
    url: https://example.com
  only:
    - main
  when: manual
```

## Pipeline Rules

```yaml
workflow:
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_TAG

job:
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      variables:
        DEPLOY_ENV: "production"
    - if: $CI_COMMIT_BRANCH == "develop"
      variables:
        DEPLOY_ENV: "staging"
```

## Variables and Secrets

```yaml
variables:
  # Global variables
  NODE_VERSION: "20"
  DOCKER_DRIVER: overlay2

# CI/CD Variables (set in GitLab UI):
# - VERCEL_TOKEN (masked)
# - AWS_ACCESS_KEY_ID (masked)
# - AWS_SECRET_ACCESS_KEY (masked)
# - KUBE_TOKEN (masked)
```

## Caching Strategies

```yaml
cache:
  key:
    files:
      - package-lock.json
  paths:
    - node_modules/
  policy: pull-push

# Job-specific cache
test:
  cache:
    key: $CI_COMMIT_REF_SLUG
    paths:
      - .npm/
    policy: pull
```

## Common Issues and Solutions

### "Job failed: exit code 1"
- Check script commands for errors
- Review job logs for specific error
- Ensure dependencies are installed

### "Docker daemon not running"
- Add `services: - docker:dind`
- Set `DOCKER_TLS_CERTDIR: "/certs"`

### "Artifacts not found"
- Check artifact paths are correct
- Verify expire_in hasn't passed
- Check job dependencies

## Autonomous Pipeline Generation

When generating GitLab pipelines:
1. Detect project type from package.json/requirements.txt
2. Create appropriate stages (build, test, deploy)
3. Add Docker build if Dockerfile exists
4. Configure caching for performance
5. Set up environment-specific deployments
6. Use Context7 for latest GitLab CI syntax
