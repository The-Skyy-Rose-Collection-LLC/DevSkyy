# Jenkins Pipelines

This skill provides comprehensive knowledge for Jenkins CI/CD pipelines. It activates when users mention "jenkins", "jenkinsfile", "jenkins pipeline", "jenkins job", or need to set up automated builds and deployments on Jenkins servers.

---

## Jenkinsfile Structure

### Declarative Pipeline
```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        NODE_VERSION = '20'
        DOCKER_REGISTRY = 'docker.io'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install') {
            steps {
                sh 'npm ci'
            }
        }

        stage('Lint') {
            steps {
                sh 'npm run lint'
            }
        }

        stage('Test') {
            steps {
                sh 'npm test'
            }
        }

        stage('Build') {
            steps {
                sh 'npm run build'
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh './deploy.sh'
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
```

## Frontend Framework Pipelines

### Next.js
```groovy
pipeline {
    agent {
        docker {
            image 'node:20'
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    environment {
        VERCEL_TOKEN = credentials('vercel-token')
        VERCEL_ORG_ID = credentials('vercel-org-id')
        VERCEL_PROJECT_ID = credentials('vercel-project-id')
    }

    stages {
        stage('Install') {
            steps {
                sh 'npm ci'
            }
        }

        stage('Lint & Test') {
            parallel {
                stage('Lint') {
                    steps {
                        sh 'npm run lint'
                    }
                }
                stage('Test') {
                    steps {
                        sh 'npm test'
                    }
                }
            }
        }

        stage('Build') {
            steps {
                sh 'npm run build'
            }
        }

        stage('Deploy to Vercel') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    npm i -g vercel
                    vercel pull --yes --environment=production --token=$VERCEL_TOKEN
                    vercel build --prod --token=$VERCEL_TOKEN
                    vercel deploy --prebuilt --prod --token=$VERCEL_TOKEN
                '''
            }
        }
    }
}
```

### React
```groovy
pipeline {
    agent {
        docker {
            image 'node:20'
        }
    }

    stages {
        stage('Install') {
            steps {
                sh 'npm ci'
            }
        }

        stage('Test') {
            steps {
                sh 'npm test -- --coverage'
            }
            post {
                always {
                    publishHTML([
                        reportDir: 'coverage/lcov-report',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }

        stage('Build') {
            steps {
                sh 'npm run build'
            }
        }

        stage('Archive') {
            steps {
                archiveArtifacts artifacts: 'dist/**/*', fingerprint: true
            }
        }
    }
}
```

## Docker Build & Push

```groovy
pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'docker.io'
        DOCKER_IMAGE = "${DOCKER_REGISTRY}/myorg/myapp"
        DOCKER_CREDENTIALS = credentials('dockerhub-credentials')
    }

    stages {
        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${BUILD_NUMBER}")
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'dockerhub-credentials') {
                        docker.image("${DOCKER_IMAGE}:${BUILD_NUMBER}").push()
                        docker.image("${DOCKER_IMAGE}:${BUILD_NUMBER}").push('latest')
                    }
                }
            }
        }
    }
}
```

## Kubernetes Deployment

```groovy
pipeline {
    agent any

    environment {
        KUBECONFIG = credentials('kubeconfig')
        K8S_NAMESPACE = 'production'
    }

    stages {
        stage('Deploy to Kubernetes') {
            steps {
                withKubeConfig([credentialsId: 'kubeconfig']) {
                    sh '''
                        kubectl set image deployment/app app=${DOCKER_IMAGE}:${BUILD_NUMBER} -n ${K8S_NAMESPACE}
                        kubectl rollout status deployment/app -n ${K8S_NAMESPACE}
                    '''
                }
            }
        }
    }
}
```

## AWS ECS Deployment

```groovy
pipeline {
    agent any

    environment {
        AWS_CREDENTIALS = credentials('aws-credentials')
        AWS_REGION = 'us-east-1'
        ECS_CLUSTER = 'my-cluster'
        ECS_SERVICE = 'my-service'
    }

    stages {
        stage('Deploy to ECS') {
            steps {
                withAWS(credentials: 'aws-credentials', region: "${AWS_REGION}") {
                    sh '''
                        aws ecs update-service \
                            --cluster ${ECS_CLUSTER} \
                            --service ${ECS_SERVICE} \
                            --force-new-deployment

                        aws ecs wait services-stable \
                            --cluster ${ECS_CLUSTER} \
                            --services ${ECS_SERVICE}
                    '''
                }
            }
        }
    }
}
```

## Multi-Branch Pipeline

```groovy
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh 'npm ci && npm run build'
            }
        }

        stage('Deploy Staging') {
            when {
                branch 'develop'
            }
            steps {
                sh './deploy.sh staging'
            }
        }

        stage('Deploy Production') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Deploy to production?'
                sh './deploy.sh production'
            }
        }
    }
}
```

## Parallel Stages

```groovy
pipeline {
    agent any

    stages {
        stage('Parallel Tests') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        sh 'npm run test:unit'
                    }
                }
                stage('Integration Tests') {
                    steps {
                        sh 'npm run test:integration'
                    }
                }
                stage('E2E Tests') {
                    steps {
                        sh 'npm run test:e2e'
                    }
                }
            }
        }
    }
}
```

## Credentials Management

```groovy
pipeline {
    agent any

    environment {
        // Username/password credential
        DB_CREDS = credentials('database-credentials')
        // Secret text credential
        API_KEY = credentials('api-key')
        // Secret file credential
        KUBECONFIG = credentials('kubeconfig-file')
    }

    stages {
        stage('Use Credentials') {
            steps {
                sh '''
                    # DB_CREDS_USR and DB_CREDS_PSW are auto-created
                    echo "DB User: $DB_CREDS_USR"

                    # Use API key
                    curl -H "Authorization: Bearer $API_KEY" https://api.example.com
                '''
            }
        }
    }
}
```

## Common Issues and Solutions

### "Script not permitted"
- Go to Manage Jenkins > In-process Script Approval
- Approve the script signature
- Or use Pipeline Shared Libraries

### "Docker daemon not found"
- Install Docker Pipeline plugin
- Mount Docker socket: `-v /var/run/docker.sock:/var/run/docker.sock`

### "Permission denied"
- Check file permissions
- Use `chmod +x` on scripts
- Run as appropriate user

## Autonomous Pipeline Generation

When generating Jenkins pipelines:
1. Detect project type from build files
2. Choose agent strategy (any, docker, kubernetes)
3. Create stages for lint, test, build, deploy
4. Add parallel stages where possible
5. Configure post actions for cleanup/notifications
6. Use Context7 for latest Jenkins syntax
