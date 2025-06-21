# Global Memory MCP Server - Part IX: Deployment & Operations Guide

**Document Version:** 1.0  
**Date:** June 12, 2025  
**Part:** IX of X - Deployment & Operations Guide  
**Classification:** Technical Operations Manual  

---

## Table of Contents

1. [Overview](#1-overview)
2. [Environment Setup](#2-environment-setup)
3. [Deployment Methods](#3-deployment-methods)
4. [Configuration Management](#4-configuration-management)
5. [Monitoring & Observability](#5-monitoring--observability)
6. [Maintenance Procedures](#6-maintenance-procedures)
7. [Backup & Recovery](#7-backup--recovery)
8. [Troubleshooting Guide](#8-troubleshooting-guide)
9. [Performance Tuning](#9-performance-tuning)
10. [Production Checklist](#10-production-checklist)

---

## 1. Overview

### 1.1 Deployment Architecture

The Global Memory MCP Server supports multiple deployment patterns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Deployment                     │
├─────────────────────────────────────────────────────────────┤
│  Load Balancer (Nginx/HAProxy)                              │
│  ├── App Server 1 (FastAPI + MCP Server)                   │
│  ├── App Server 2 (FastAPI + MCP Server)                   │
│  └── App Server N (FastAPI + MCP Server)                   │
│                                                             │
│  Database Layer                                             │
│  ├── PostgreSQL Primary (Read/Write)                       │
│  ├── PostgreSQL Replica 1 (Read Only)                      │
│  └── PostgreSQL Replica N (Read Only)                      │
│                                                             │
│  External Services                                          │
│  ├── Redis Cache                                           │
│  ├── Monitoring (Prometheus/Grafana)                       │
│  └── Logging (ELK Stack)                                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Deployment Options

- **Single Node**: Development and testing
- **Multi-Node**: Production with load balancing
- **Container**: Docker/Kubernetes deployment
- **Cloud**: AWS/GCP/Azure managed services

---

## 2. Environment Setup

### 2.1 System Requirements

#### Minimum Requirements
```yaml
CPU: 2 cores (x86_64)
RAM: 4GB
Storage: 20GB SSD
Network: 1Gbps
OS: Ubuntu 20.04 LTS / CentOS 8 / RHEL 8
```

#### Recommended Production
```yaml
CPU: 8+ cores (x86_64)
RAM: 16GB+
Storage: 100GB+ NVMe SSD
Network: 10Gbps
OS: Ubuntu 22.04 LTS
Load Balancer: Yes
Database: Separate server/cluster
```

### 2.2 Prerequisites Installation

#### Ubuntu/Debian
```bash
# System updates
sudo apt update && sudo apt upgrade -y

# Python 3.11+
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# PostgreSQL 15+
sudo apt install postgresql-15 postgresql-client-15 postgresql-contrib-15 -y

# Essential tools
sudo apt install git curl wget htop iotop redis-server nginx -y

# Development tools
sudo apt install build-essential libssl-dev libffi-dev -y
```

#### CentOS/RHEL
```bash
# System updates
sudo dnf update -y

# Python 3.11+
sudo dnf install python3.11 python3.11-pip python3.11-devel -y

# PostgreSQL 15+
sudo dnf install postgresql15-server postgresql15-contrib -y

# Essential tools
sudo dnf install git curl wget htop iotop redis nginx -y
```

### 2.3 Database Setup

#### PostgreSQL Configuration
```bash
# Initialize database
sudo postgresql-setup --initdb

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE global_memory_production;
CREATE USER mcp_user WITH ENCRYPTED PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE global_memory_production TO mcp_user;
ALTER USER mcp_user CREATEDB;
\q
EOF
```

#### PostgreSQL Optimization
```sql
-- /etc/postgresql/15/main/postgresql.conf optimizations
shared_buffers = '256MB'          -- 25% of RAM for small instances
effective_cache_size = '1GB'      -- 75% of RAM
work_mem = '4MB'                  -- Per operation memory
maintenance_work_mem = '64MB'     -- Maintenance operations
checkpoint_completion_target = 0.9
wal_buffers = '16MB'
default_statistics_target = 100
random_page_cost = 1.1            -- For SSD storage
effective_io_concurrency = 200    -- For SSD storage
```

---

## 3. Deployment Methods

### 3.1 Manual Deployment

#### Step 1: Clone Repository
```bash
git clone https://github.com/your-org/agentros.git
cd agentros
```

#### Step 2: Create Virtual Environment
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-prod.txt
```

#### Step 4: Environment Configuration
```bash
# Create production environment file
cp .env.example .env.production

# Edit configuration
nano .env.production
```

#### Step 5: Database Migration
```bash
# Run migrations
python -m alembic upgrade head

# Verify database schema
python scripts/verify_database.py
```

#### Step 6: Start Services
```bash
# Start MCP Server
python -m memory_mcp_server --host 0.0.0.0 --port 8000 --env production

# Start FastAPI server (separate terminal)
uvicorn api.main:app --host 0.0.0.0 --port 8001 --workers 4
```

### 3.2 Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-prod.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["python", "-m", "memory_mcp_server", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  database:
    image: postgres:15
    environment:
      POSTGRES_DB: global_memory_production
      POSTGRES_USER: mcp_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./config/postgres.conf:/etc/postgresql/postgresql.conf
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mcp_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  mcp-server:
    build: .
    depends_on:
      database:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://mcp_user:${DB_PASSWORD}@database:5432/global_memory_production
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=production
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  api-server:
    build: .
    command: uvicorn api.main:app --host 0.0.0.0 --port 8001 --workers 4
    depends_on:
      - mcp-server
    environment:
      - MCP_SERVER_URL=http://mcp-server:8000
      - ENVIRONMENT=production
    ports:
      - "8001:8001"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    depends_on:
      - api-server
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 3.3 Kubernetes Deployment

#### Namespace
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: global-memory
```

#### ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-config
  namespace: global-memory
data:
  DATABASE_HOST: "postgres-service"
  DATABASE_PORT: "5432"
  DATABASE_NAME: "global_memory_production"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
```

#### Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mcp-secrets
  namespace: global-memory
type: Opaque
data:
  DATABASE_PASSWORD: <base64-encoded-password>
  DATABASE_USER: <base64-encoded-username>
  JWT_SECRET_KEY: <base64-encoded-jwt-secret>
```

#### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
  namespace: global-memory
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: your-registry/global-memory-mcp:latest
        ports:
        - containerPort: 8000
        - containerPort: 8001
        envFrom:
        - configMapRef:
            name: mcp-config
        - secretRef:
            name: mcp-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## 4. Configuration Management

### 4.1 Environment Variables

#### Production Configuration (.env.production)
```bash
# Database Configuration
DATABASE_URL=postgresql://mcp_user:password@localhost:5432/global_memory_production
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=10

# Server Configuration
HOST=0.0.0.0
PORT=8000
API_PORT=8001
WORKERS=4
ENVIRONMENT=production

# Security
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-here
ENCRYPTION_KEY=your-32-byte-encryption-key-here
ALLOWED_HOSTS=your-domain.com,api.your-domain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/global-memory/app.log
ACCESS_LOG=/var/log/global-memory/access.log

# Performance
MEMORY_CACHE_SIZE=1000
VECTOR_CACHE_SIZE=500
EMBEDDING_BATCH_SIZE=100

# External Services
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
HEALTH_CHECK_INTERVAL=30
```

### 4.2 Nginx Configuration

#### /etc/nginx/sites-available/global-memory
```nginx
upstream mcp_api {
    least_conn;
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8003 max_fails=3 fail_timeout=30s;
}

upstream mcp_server {
    least_conn;
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8010 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8020 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    # API endpoints
    location /api/ {
        proxy_pass http://mcp_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # MCP Server WebSocket
    location /mcp/ {
        proxy_pass http://mcp_server;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health checks
    location /health {
        proxy_pass http://mcp_api;
        access_log off;
    }

    # Static files (if any)
    location /static/ {
        alias /var/www/global-memory/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 5. Monitoring & Observability

### 5.1 Prometheus Configuration

#### prometheus.yml
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "global_memory_rules.yml"

scrape_configs:
  - job_name: 'global-memory-api'
    static_configs:
      - targets: ['localhost:8001', 'localhost:8002', 'localhost:8003']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'global-memory-mcp'
    static_configs:
      - targets: ['localhost:8000', 'localhost:8010', 'localhost:8020']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'postgresql'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:9113']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

#### Alert Rules (global_memory_rules.yml)
```yaml
groups:
  - name: global_memory_alerts
    rules:
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: DatabaseConnectionsHigh
        expr: pg_stat_activity_count > 80
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High database connections"
          description: "Database has {{ $value }} active connections"

      - alert: MemoryUsageHigh
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      - alert: DiskUsageHigh
        expr: (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High disk usage"
          description: "Disk usage is {{ $value | humanizePercentage }}"
```

### 5.2 Grafana Dashboards

#### System Overview Dashboard
```json
{
  "dashboard": {
    "title": "Global Memory MCP Server - System Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (instance)"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))"
          }
        ]
      },
      {
        "title": "Memory Operations",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(memory_operations_total[5m])) by (operation_type)"
          }
        ]
      }
    ]
  }
}
```

### 5.3 Logging Configuration

#### Structured Logging (logging.conf)
```ini
[loggers]
keys=root,global_memory,uvicorn,sqlalchemy

[handlers]
keys=console,file,error_file

[formatters]
keys=json,detailed

[logger_root]
level=INFO
handlers=console,file

[logger_global_memory]
level=INFO
handlers=file,error_file
qualname=global_memory
propagate=0

[logger_uvicorn]
level=INFO
handlers=file
qualname=uvicorn
propagate=0

[logger_sqlalchemy]
level=WARNING
handlers=file
qualname=sqlalchemy
propagate=0

[handler_console]
class=StreamHandler
level=INFO
formatter=json
args=(sys.stdout,)

[handler_file]
class=handlers.RotatingFileHandler
level=INFO
formatter=json
args=('/var/log/global-memory/app.log', 'a', 100000000, 5)

[handler_error_file]
class=handlers.RotatingFileHandler
level=ERROR
formatter=detailed
args=('/var/log/global-memory/error.log', 'a', 100000000, 5)

[formatter_json]
format={"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "line": %(lineno)d}

[formatter_detailed]
format=%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s
```

---

## 6. Maintenance Procedures

### 6.1 Regular Maintenance Tasks

#### Daily Tasks
```bash
#!/bin/bash
# daily_maintenance.sh

# Check system health
curl -f http://localhost:8001/health || echo "Health check failed"

# Database maintenance
sudo -u postgres psql global_memory_production << EOF
ANALYZE;
VACUUM (ANALYZE, VERBOSE);
EOF

# Log rotation
sudo logrotate /etc/logrotate.d/global-memory

# Backup verification
./scripts/verify_backup.sh
```

#### Weekly Tasks
```bash
#!/bin/bash
# weekly_maintenance.sh

# Full database vacuum
sudo -u postgres psql global_memory_production << EOF
VACUUM FULL ANALYZE;
REINDEX DATABASE global_memory_production;
EOF

# Update system packages
sudo apt update && sudo apt upgrade -y

# Certificate renewal check
sudo certbot renew --dry-run

# Performance report generation
python scripts/generate_performance_report.py
```

#### Monthly Tasks
```bash
#!/bin/bash
# monthly_maintenance.sh

# Database statistics update
sudo -u postgres psql global_memory_production << EOF
ANALYZE VERBOSE;
UPDATE pg_stat_user_tables SET n_tup_ins = 0, n_tup_upd = 0, n_tup_del = 0;
EOF

# Security audit
./scripts/security_audit.sh

# Dependency updates
pip list --outdated
./scripts/update_dependencies.sh

# Backup retention cleanup
./scripts/cleanup_old_backups.sh
```

### 6.2 Update Procedures

#### Application Updates
```bash
#!/bin/bash
# update_application.sh

# 1. Create backup
./scripts/create_backup.sh pre-update-$(date +%Y%m%d-%H%M%S)

# 2. Test new version in staging
git checkout staging
docker-compose -f docker-compose.staging.yml up -d
./scripts/run_tests.sh staging

# 3. Deploy to production (blue-green)
git checkout main
docker-compose -f docker-compose.blue.yml up -d

# 4. Switch traffic
./scripts/switch_traffic.py blue

# 5. Verify deployment
./scripts/verify_deployment.sh

# 6. Cleanup old version
docker-compose -f docker-compose.green.yml down
```

#### Database Schema Updates
```bash
#!/bin/bash
# update_database_schema.sh

# 1. Backup database
pg_dump global_memory_production > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Test migration on copy
createdb global_memory_test
psql global_memory_test < backup_$(date +%Y%m%d_%H%M%S).sql
alembic -c alembic.test.ini upgrade head

# 3. Apply to production
alembic upgrade head

# 4. Verify schema
python scripts/verify_schema.py
```

---

## 7. Backup & Recovery

### 7.1 Backup Strategy

#### Database Backups
```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="/backups/global-memory"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="global_memory_production"

# Create backup directory
mkdir -p $BACKUP_DIR/{daily,weekly,monthly}

# Full database backup
pg_dump -U mcp_user -h localhost $DB_NAME | gzip > $BACKUP_DIR/daily/db_backup_$DATE.sql.gz

# Vector embeddings backup
python scripts/backup_embeddings.py $BACKUP_DIR/daily/embeddings_$DATE.json

# Configuration backup
tar -czf $BACKUP_DIR/daily/config_$DATE.tar.gz /etc/global-memory/ ~/.env.production

# Upload to cloud storage
aws s3 cp $BACKUP_DIR/daily/ s3://your-backup-bucket/daily/ --recursive
```

#### Automated Backup (Cron)
```bash
# /etc/cron.d/global-memory-backup

# Daily backup at 2 AM
0 2 * * * mcp_user /opt/global-memory/scripts/backup_database.sh

# Weekly full backup at 3 AM Sunday
0 3 * * 0 mcp_user /opt/global-memory/scripts/weekly_backup.sh

# Monthly archive backup at 4 AM 1st of month
0 4 1 * * mcp_user /opt/global-memory/scripts/monthly_backup.sh

# Cleanup old backups daily at 5 AM
0 5 * * * mcp_user /opt/global-memory/scripts/cleanup_backups.sh
```

### 7.2 Recovery Procedures

#### Database Recovery
```bash
#!/bin/bash
# restore_database.sh

BACKUP_FILE=$1
DB_NAME="global_memory_production"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Stop services
sudo systemctl stop global-memory-api
sudo systemctl stop global-memory-mcp

# Drop and recreate database
sudo -u postgres psql << EOF
DROP DATABASE IF EXISTS ${DB_NAME}_old;
ALTER DATABASE $DB_NAME RENAME TO ${DB_NAME}_old;
CREATE DATABASE $DB_NAME;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO mcp_user;
EOF

# Restore from backup
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE | sudo -u postgres psql $DB_NAME
else
    sudo -u postgres psql $DB_NAME < $BACKUP_FILE
fi

# Verify restoration
python scripts/verify_database.py

# Start services
sudo systemctl start global-memory-mcp
sudo systemctl start global-memory-api

echo "Database restored successfully"
```

#### Point-in-Time Recovery
```bash
#!/bin/bash
# point_in_time_recovery.sh

TARGET_TIME=$1
BACKUP_BASE_DIR="/backups/global-memory"

if [ -z "$TARGET_TIME" ]; then
    echo "Usage: $0 'YYYY-MM-DD HH:MM:SS'"
    exit 1
fi

# Find base backup before target time
BASE_BACKUP=$(find $BACKUP_BASE_DIR -name "*.sql.gz" -newermt "$TARGET_TIME" | head -1)

# Restore base backup
./restore_database.sh $BASE_BACKUP

# Apply WAL files up to target time
sudo -u postgres pg_waldump /var/lib/postgresql/15/main/pg_wal/ \
    --start=$BASE_BACKUP_LSN --end-time="$TARGET_TIME" | \
    sudo -u postgres psql global_memory_production

echo "Point-in-time recovery completed to $TARGET_TIME"
```

---

## 8. Troubleshooting Guide

### 8.1 Common Issues

#### High CPU Usage
```bash
# Identify CPU-intensive processes
top -p $(pgrep -d',' python)

# Check database queries
sudo -u postgres psql global_memory_production << EOF
SELECT query, state, query_start, now() - query_start AS duration 
FROM pg_stat_activity 
WHERE state != 'idle' 
ORDER BY duration DESC;
EOF

# Check for long-running embedding operations
tail -f /var/log/global-memory/app.log | grep "embedding"
```

#### Memory Leaks
```bash
# Monitor memory usage
watch 'ps aux --sort=-%mem | head -20'

# Check Python memory usage
python scripts/memory_profiler.py

# Analyze memory dumps
gcore $(pgrep python)
gdb python core.xxxx
```

#### Database Connection Issues
```bash
# Check connection pool status
sudo -u postgres psql global_memory_production << EOF
SELECT 
    state,
    count(*),
    max(now() - state_change) as max_duration
FROM pg_stat_activity 
WHERE datname = 'global_memory_production'
GROUP BY state;
EOF

# Reset connections
sudo systemctl restart postgresql
./scripts/reset_connection_pool.py
```

#### SSL/TLS Issues
```bash
# Check certificate validity
openssl x509 -in /etc/ssl/certs/your-domain.crt -text -noout

# Verify certificate chain
openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/your-domain.crt

# Test SSL connectivity
openssl s_client -connect api.your-domain.com:443 -servername api.your-domain.com
```

### 8.2 Performance Issues

#### Slow Query Identification
```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();

-- Analyze slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 20;
```

#### Index Analysis
```sql
-- Missing indexes
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
AND n_distinct > 100
AND correlation < 0.1;

-- Unused indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_tup_read = 0
AND idx_tup_fetch = 0;
```

### 8.3 Recovery Scenarios

#### Complete System Failure
```bash
#!/bin/bash
# disaster_recovery.sh

# 1. Provision new infrastructure
terraform apply -var="environment=disaster-recovery"

# 2. Restore latest backup
LATEST_BACKUP=$(aws s3 ls s3://your-backup-bucket/daily/ | sort | tail -1 | awk '{print $4}')
aws s3 cp s3://your-backup-bucket/daily/$LATEST_BACKUP ./

# 3. Restore database
./restore_database.sh $LATEST_BACKUP

# 4. Deploy application
docker-compose up -d

# 5. Verify system health
./scripts/health_check.sh

# 6. Update DNS records
./scripts/update_dns.py --environment disaster-recovery
```

#### Data Corruption
```bash
#!/bin/bash
# data_corruption_recovery.sh

# 1. Identify corruption extent
python scripts/data_integrity_check.py

# 2. Stop write operations
./scripts/enable_read_only_mode.py

# 3. Restore from clean backup
./restore_database.sh $CLEAN_BACKUP_FILE

# 4. Replay valid transactions
python scripts/replay_transactions.py --since $CORRUPTION_TIME

# 5. Verify data integrity
python scripts/verify_data_integrity.py

# 6. Resume normal operations
./scripts/disable_read_only_mode.py
```

---

## 9. Performance Tuning

### 9.1 Database Optimization

#### Connection Pool Tuning
```python
# config/database.py
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 20,                    # Base connections
    "max_overflow": 30,                 # Additional connections
    "pool_timeout": 30,                 # Connection timeout
    "pool_recycle": 1800,              # Connection refresh (30 min)
    "pool_pre_ping": True,             # Validate connections
    "echo": False,                      # Disable SQL logging in prod
}

# PostgreSQL connection limits
# max_connections = 200
# shared_buffers = 2GB               # 25% of RAM
# effective_cache_size = 6GB         # 75% of RAM
# work_mem = 16MB                    # Per operation
# maintenance_work_mem = 512MB       # Maintenance ops
```

#### Query Optimization
```sql
-- Create optimized indexes
CREATE INDEX CONCURRENTLY idx_memories_user_type_time 
ON memories (user_id, memory_type, created_at DESC);

CREATE INDEX CONCURRENTLY idx_embeddings_vector_cosine 
ON memory_embeddings USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Partition large tables
CREATE TABLE memories_2025 PARTITION OF memories
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- Materialized views for analytics
CREATE MATERIALIZED VIEW memory_stats AS
SELECT 
    user_id,
    memory_type,
    DATE_TRUNC('day', created_at) as date,
    COUNT(*) as count,
    AVG(importance_score) as avg_importance
FROM memories
GROUP BY user_id, memory_type, DATE_TRUNC('day', created_at);

CREATE UNIQUE INDEX ON memory_stats (user_id, memory_type, date);
```

### 9.2 Application Performance

#### Caching Strategy
```python
# config/cache.py
CACHE_CONFIG = {
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "encoding": "utf-8",
        "decode_responses": True,
        "socket_connect_timeout": 5,
        "socket_timeout": 5,
        "connection_pool_kwargs": {
            "max_connections": 50,
            "retry_on_timeout": True,
        }
    },
    "cache_ttl": {
        "memory_query": 300,            # 5 minutes
        "user_profile": 3600,           # 1 hour
        "embeddings": 7200,             # 2 hours
        "search_results": 600,          # 10 minutes
    }
}

# Implement cache warming
async def warm_cache():
    """Pre-populate frequently accessed data"""
    popular_memories = await get_popular_memories()
    for memory in popular_memories:
        await cache.set(f"memory:{memory.id}", memory, ttl=3600)
```

#### Async Processing
```python
# Background task optimization
from celery import Celery
from redis import Redis

# Configure Celery for heavy operations
celery_app = Celery(
    'global_memory',
    broker='redis://localhost:6379/1',
    backend='redis://localhost:6379/2',
    include=['tasks.embeddings', 'tasks.analysis']
)

@celery_app.task(bind=True, max_retries=3)
def generate_embedding_async(self, memory_id: str):
    """Generate embeddings asynchronously"""
    try:
        memory = get_memory(memory_id)
        embedding = generate_embedding(memory.content)
        store_embedding(memory_id, embedding)
        return {"status": "success", "memory_id": memory_id}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### 9.3 System-Level Optimization

#### Nginx Tuning
```nginx
# /etc/nginx/nginx.conf
worker_processes auto;
worker_connections 4096;
worker_rlimit_nofile 65535;

events {
    use epoll;
    multi_accept on;
}

http {
    # Connection optimization
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 100;

    # Buffer optimization
    client_body_buffer_size 128k;
    client_max_body_size 10m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_conn_zone $binary_remote_addr zone=addr:10m;
}
```

#### Operating System Tuning
```bash
# /etc/sysctl.conf optimizations

# Network optimization
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 3

# Memory optimization
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# File system optimization
fs.file-max = 65535
fs.nr_open = 65535

# PostgreSQL specific
kernel.shmmax = 68719476736
kernel.shmall = 4294967296
```

---

## 10. Production Checklist

### 10.1 Pre-Deployment Checklist

#### Security Checklist
- [ ] SSL/TLS certificates installed and valid
- [ ] Firewall rules configured (ports 22, 80, 443, 5432)
- [ ] Database access restricted to application servers
- [ ] Strong passwords for all accounts
- [ ] SSH key-based authentication enabled
- [ ] Root login disabled
- [ ] Regular security updates scheduled
- [ ] Backup encryption enabled
- [ ] Secrets management configured
- [ ] Rate limiting implemented

#### Performance Checklist
- [ ] Database indexes created and optimized
- [ ] Connection pooling configured
- [ ] Caching layer implemented
- [ ] CDN configured for static assets
- [ ] Compression enabled
- [ ] Database query optimization completed
- [ ] Load testing performed
- [ ] Resource monitoring configured
- [ ] Auto-scaling rules defined
- [ ] Performance baselines established

#### Monitoring Checklist
- [ ] Application metrics collection enabled
- [ ] Database monitoring configured
- [ ] System resource monitoring active
- [ ] Log aggregation setup
- [ ] Alerting rules configured
- [ ] Health check endpoints implemented
- [ ] Uptime monitoring enabled
- [ ] Error tracking configured
- [ ] Performance monitoring active
- [ ] Dashboard access configured

### 10.2 Go-Live Checklist

#### Final Verification
```bash
#!/bin/bash
# go_live_checklist.sh

echo "=== Global Memory MCP Server - Go-Live Checklist ==="

# 1. Service Health
echo "1. Checking service health..."
curl -f http://localhost:8001/health || echo "❌ Health check failed"
curl -f http://localhost:8000/status || echo "❌ MCP server status failed"

# 2. Database Connectivity
echo "2. Checking database connectivity..."
python -c "
from db.connection import get_db_connection
try:
    conn = get_db_connection()
    conn.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"

# 3. Memory Operations
echo "3. Testing memory operations..."
python scripts/test_memory_operations.py || echo "❌ Memory operations test failed"

# 4. Performance Test
echo "4. Running performance test..."
python scripts/performance_test.py --duration 60 || echo "❌ Performance test failed"

# 5. Security Scan
echo "5. Running security scan..."
python scripts/security_scan.py || echo "❌ Security scan failed"

# 6. Backup Verification
echo "6. Verifying backup system..."
./scripts/test_backup.sh || echo "❌ Backup test failed"

# 7. Monitoring Check
echo "7. Checking monitoring..."
curl -f http://localhost:9090/-/healthy || echo "❌ Prometheus not healthy"
curl -f http://localhost:3000/api/health || echo "❌ Grafana not healthy"

# 8. SSL Certificate
echo "8. Checking SSL certificate..."
openssl s_client -connect api.your-domain.com:443 -servername api.your-domain.com </dev/null 2>/dev/null | openssl x509 -noout -dates

echo "=== Go-Live Checklist Complete ==="
```

### 10.3 Post-Deployment Monitoring

#### 24-Hour Watch
```bash
#!/bin/bash
# 24_hour_watch.sh

echo "Starting 24-hour production monitoring..."

for hour in {1..24}; do
    echo "Hour $hour monitoring..."
    
    # System health
    ./scripts/health_check.sh
    
    # Performance metrics
    curl -s http://localhost:8001/metrics | grep -E "response_time|error_rate|memory_usage"
    
    # Database performance
    sudo -u postgres psql -c "
        SELECT 
            count(*) as active_connections,
            max(now() - query_start) as longest_query
        FROM pg_stat_activity 
        WHERE state = 'active';
    "
    
    # Sleep for 1 hour
    sleep 3600
done

echo "24-hour monitoring complete. Generating report..."
python scripts/generate_monitoring_report.py --period "24h"
```

#### Weekly Health Report
```python
# scripts/weekly_health_report.py
import asyncio
from datetime import datetime, timedelta
from monitoring.metrics_collector import MetricsCollector
from reporting.report_generator import ReportGenerator

async def generate_weekly_report():
    """Generate comprehensive weekly health report"""
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    collector = MetricsCollector()
    metrics = await collector.collect_metrics(start_time, end_time)
    
    report = ReportGenerator()
    
    # System performance summary
    performance_summary = {
        "avg_response_time": metrics.get_avg_response_time(),
        "error_rate": metrics.get_error_rate(),
        "uptime_percentage": metrics.get_uptime_percentage(),
        "throughput": metrics.get_avg_throughput(),
    }
    
    # Database health
    db_health = {
        "avg_connections": metrics.get_avg_db_connections(),
        "slow_queries": metrics.get_slow_queries_count(),
        "cache_hit_ratio": metrics.get_cache_hit_ratio(),
        "storage_usage": metrics.get_storage_usage(),
    }
    
    # Memory operations
    memory_ops = {
        "total_operations": metrics.get_total_memory_operations(),
        "successful_operations": metrics.get_successful_operations(),
        "failed_operations": metrics.get_failed_operations(),
        "avg_operation_time": metrics.get_avg_operation_time(),
    }
    
    # Generate report
    report_content = await report.generate_health_report(
        performance_summary,
        db_health,
        memory_ops,
        start_time,
        end_time
    )
    
    # Save and send report
    report_file = f"health_report_{start_time.strftime('%Y%m%d')}.pdf"
    await report.save_pdf(report_content, report_file)
    await report.send_email(report_file, recipients=["ops@your-company.com"])
    
    print(f"Weekly health report generated: {report_file}")

if __name__ == "__main__":
    asyncio.run(generate_weekly_report())
```

---

## Conclusion

This deployment and operations guide provides comprehensive procedures for deploying, monitoring, and maintaining the Global Memory MCP Server in production environments. Following these guidelines will ensure reliable, secure, and performant operation of the system.

### Key Success Factors

1. **Proper Planning**: Follow the deployment checklist thoroughly
2. **Monitoring**: Implement comprehensive monitoring from day one
3. **Automation**: Automate routine maintenance and monitoring tasks
4. **Documentation**: Keep operational procedures updated
5. **Testing**: Regular testing of backup and recovery procedures
6. **Security**: Continuous security monitoring and updates

### Support and Escalation

For operational issues:
1. Check monitoring dashboards first
2. Review recent logs and error messages
3. Consult troubleshooting guide
4. Escalate to development team if needed
5. Document all incidents for future reference

---

**Document Information:**
- **Created:** June 12, 2025
- **Last Updated:** June 12, 2025
- **Version:** 1.0
- **Next Review:** June 12, 2026

---

*This document is part of the Global Memory MCP Server technical documentation suite. For questions or updates, please contact the development team.*
