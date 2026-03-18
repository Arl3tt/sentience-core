# Deployment Guide: Sentience Core

This guide provides comprehensive instructions for deploying Sentience Core to various environments.

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Platforms](#cloud-platforms)
6. [Monitoring & Logs](#monitoring--logs)
7. [Troubleshooting](#troubleshooting)

---

## Local Development Setup

### Prerequisites

- Python 3.13+
- Git
- Redis (optional, for queue functionality)
- Docker (for sandbox isolation, optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/Arl3tt/sentience-core.git
cd sentience-core

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your API keys
```

### Running Locally

```bash
# Start the main application
python main.py

# In a separate terminal, run with web UI
# The web UI will be available at http://localhost:8080
```

### Development Workflow

```bash
# Run linting
python -m flake8 --max-line-length=120

# Run tests
python -m pytest tests/ -v

# Run with coverage
pytest tests/ --cov=core --cov-report=html
```

---

## Docker Deployment

### Building Docker Images

#### Application Image

```bash
# Build the main application image
docker build -t sentience-core:latest -f docker/Dockerfile.app .
```

#### Sandbox Image

```bash
# Build the sandbox image (for safe code execution)
docker build -t sentience-sandbox:latest -f docker/Dockerfile.sandbox .
```

### Running with Docker Compose

```bash
# Start all services (app + Redis + sandbox)
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml down
```

### Environment Variables

Create `.env.docker` file:

```bash
# API Keys
OPENAI_API_KEY=your-api-key-here

# Database
REDIS_URL=redis://redis:6379/0
DATABASE_URL=sqlite://./data/sentience.db

# Application Settings
LOG_LEVEL=INFO
SAFE_MODE=true
DEBUG=false

# Web UI
WEB_PORT=8080
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] All tests passing (`pytest tests/`)
- [ ] Linting passes (`flake8 --max-line-length=120`)
- [ ] Docker images built and tested
- [ ] Environment variables configured
- [ ] Database migrations completed
- [ ] SSL certificates obtained
- [ ] Monitoring configured
- [ ] Backups configured

### Docker Production Setup

```yaml
# production-docker-compose.yml
version: '3.8'

services:
  app:
    image: sentience-core:latest
    restart: always
    ports:
      - "8080:8080"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
      - SAFE_MODE=true
    depends_on:
      - redis
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  sandbox:
    image: sentience-sandbox:latest
    restart: always
    security_opt:
      - no-new-privileges
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp
    mem_limit: 256m
    cpus: '0.5'

volumes:
  redis_data:
```

### SSL/TLS Configuration

```bash
# Generate self-signed certificate (development)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365

# Or use Let's Encrypt (production)
certbot certonly --standalone -d yourdomain.com
```

### Health Checks

```bash
# Check application health
curl http://localhost:8080/health

# Check Redis connection
redis-cli ping

# Check memory usage
docker stats sentience-core
```

---

## Kubernetes Deployment

### Prerequisites

- kubectl configured
- Kubernetes cluster (1.19+)
- Docker Registry access

### Creating Kubernetes Manifests

`k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentience-core
  labels:
    app: sentience-core
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sentience-core
  template:
    metadata:
      labels:
        app: sentience-core
    spec:
      containers:
      - name: sentience-core
        image: sentience-core:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
        - name: REDIS_URL
          value: redis://redis-service:6379/0
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: sentience-service
spec:
  selector:
    app: sentience-core
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

### Deploying to Kubernetes

```bash
# Create secret for API keys
kubectl create secret generic openai-secret --from-literal=api-key=$OPENAI_API_KEY

# Deploy application
kubectl apply -f k8s-deployment.yaml

# Monitor deployment
kubectl get deployments
kubectl describe deployment sentience-core
kubectl logs -l app=sentience-core

# Scale application
kubectl scale deployment sentience-core --replicas=3
```

---

## Cloud Platforms

### AWS Deployment

#### Using ECS

```bash
# Create ECS task definition
aws ecs register-task-definition \
  --family sentience-core \
  --container-definitions file://ecs-task-definition.json

# Create ECS service
aws ecs create-service \
  --cluster sentience-cluster \
  --service-name sentience-core \
  --task-definition sentience-core:1 \
  --desired-count 2
```

#### Using Lambda (Serverless)

For serverless deployment, containerize the application:

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URI
docker tag sentience-core:latest $ECR_URI/sentience-core:latest
docker push $ECR_URI/sentience-core:latest

# Deploy to Lambda
aws lambda create-function \
  --function-name sentience-core \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --code ImageUri=$ECR_URI/sentience-core:latest \
  --memory-size 1024 \
  --timeout 900
```

### Azure Deployment

#### Using Container Instances

```bash
# Create Azure Container Group
az container create \
  --resource-group myResourceGroup \
  --name sentience-core \
  --image sentience-core:latest \
  --cpu 1 \
  --memory 1 \
  --ports 8080 \
  --environment-variables OPENAI_API_KEY=$OPENAI_API_KEY
```

#### Using App Service

```bash
# Deploy via App Service
az webapp deployment source config-zip \
  --resource-group myResourceGroup \
  --name sentience-app \
  --src app.zip
```

### Google Cloud Deployment

#### Using Cloud Run

```bash
# Build and deploy to Cloud Run
gcloud run deploy sentience-core \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY \
  --memory 1Gi \
  --cpu 1
```

---

## Monitoring & Logs

### Application Monitoring

```bash
# View real-time logs
docker logs -f sentience-core

# Check application metrics
curl http://localhost:8080/metrics

# Monitor system resources
docker stats sentience-core
```

### Setting Up Application Insights (Azure)

```python
# In your application
from applicationinsights import Request
from applicationinsights.logging import enable

enable(INSTRUMENTATION_KEY)
```

### CloudWatch Logs (AWS)

```bash
# View logs in CloudWatch
aws logs tail /aws/ecs/sentience-core --follow

# Create metric alarms
aws cloudwatch put-metric-alarm \
  --alarm-name high-error-rate \
  --alarm-description "Alert if error rate > 5%" \
  --metric-name ErrorRate \
  --namespace sentience-core
```

### Logging Configuration

Create `logging.yaml`:

```yaml
version: 1
handlers:
  file:
    class: logging.FileHandler
    filename: logs/sentience.log
    formatter: verbose
  console:
    class: logging.StreamHandler
    formatter: simple
  
formatters:
  simple:
    format: '%(levelname)s - %(message)s'
  verbose:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

root:
  level: INFO
  handlers:
    - console
    - file
```

---

## Troubleshooting

### Common Issues

#### Docker build fails

```bash
# Clean up and rebuild
docker system prune -a
docker build --no-cache -t sentience-core:latest .
```

#### Application won't start

```bash
# Check logs
docker logs sentience-core

# Verify environment variables
docker exec sentience-core env | grep OPENAI_API_KEY

# Check port availability
lsof -i :8080  # Linux/macOS
netstat -ano | findstr :8080  # Windows
```

#### Redis connection fails

```bash
# Test Redis connectivity
redis-cli -h localhost ping

# Check Redis configuration
docker exec redis redis-cli CONFIG GET maxmemory
```

#### Memory issues

```bash
# Increase memory limits
docker run -m 2g --name sentience-core sentience-core:latest

# Monitor memory usage
docker stats --no-stream sentience-core
```

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or in docker-compose
environment:
  - LOG_LEVEL=DEBUG
```

### Performance Tuning

```bash
# Increase Redis connection pool
export REDIS_POOL_SIZE=20

# Adjust LLM timeout
export LLM_TIMEOUT=30

# Configure memory limits
export MAX_MEMORY_MB=2048
```

---

## Backup & Recovery

### Database Backup

```bash
# Backup SQLite database
docker exec sentience-core \
  sqlite3 data/sentience.db ".backup '/backup/sentience-backup.db'"

# Backup Redis
docker exec redis redis-cli BGSAVE
docker cp redis:/data/dump.rdb ./backup/
```

### Disaster Recovery

```bash
# Restore from backup
docker exec sentience-core \
  sqlite3 data/sentience.db ".restore '/backup/sentience-backup.db'"

# Test recovery
docker restart sentience-core
```

---

## Support & Contact

For deployment issues, please:

1. Check this guide and troubleshooting section
2. Review logs: `docker logs sentience-core`
3. Run tests: `pytest tests/ -v`
4. Open GitHub issue with details
5. Include: Python version, Docker version, OS, error logs

---

**Last Updated**: March 18, 2026
**Version**: 1.0
