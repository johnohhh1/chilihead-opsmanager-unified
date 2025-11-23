# Product Requirements Document: ChiliHead OpsManager - Google Ecosystem Migration

**Document Version:** 1.0  
**Date:** November 19, 2025  
**Author:** Product Engineering Team  
**Status:** Draft for Review  

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Goals & Success Metrics](#project-goals--success-metrics)
3. [Current Architecture Overview](#current-architecture-overview)
4. [Google Ecosystem Strategy](#google-ecosystem-strategy)
5. [Technical Architecture (Google Stack)](#technical-architecture-google-stack)
6. [Detailed Component Mapping](#detailed-component-mapping)
7. [Database Strategy](#database-strategy)
8. [Authentication & Security](#authentication--security)
9. [AI/ML Integration (Gemini)](#aiml-integration-gemini)
10. [Frontend Migration](#frontend-migration)
11. [API Structure](#api-structure)
12. [Implementation Phases](#implementation-phases)
13. [Risk Analysis & Mitigation](#risk-analysis--mitigation)
14. [Cost Analysis](#cost-analysis)
15. [Timeline & Milestones](#timeline--milestones)
16. [Success Criteria](#success-criteria)
17. [Appendix: Code Examples](#appendix-code-examples)

---

## 1. Executive Summary

### Overview
Migrate the ChiliHead OpsManager Unified platform from its current multi-vendor stack (OpenAI GPT-4, PostgreSQL, FastAPI) to a fully Google-native ecosystem. This migration will leverage Google Cloud Platform (GCP), Gemini AI models, Firebase/Cloud SQL, and Google Workspace APIs to create a cohesive, performant, and cost-effective solution.

### Key Benefits
- **Unified Billing & Management**: Single vendor for all cloud services
- **Native Integration**: Seamless Gmail, Calendar, Tasks API integration
- **Cost Optimization**: Potentially 30-40% reduction in AI inference costs
- **Performance**: Lower latency with co-located services
- **Gemini 2.0**: Access to latest multimodal AI capabilities
- **Simplified Auth**: Google Identity Platform for all services
- **Scalability**: Auto-scaling with Cloud Run

### Business Impact
- Reduced monthly operational costs ($150-200/month → $80-120/month estimated)
- Improved response times (50-100ms latency reduction)
- Enhanced reliability through GCP's 99.95% SLA
- Future-proof architecture with Google's AI roadmap

---

## 2. Project Goals & Success Metrics

### Primary Goals
1. **Complete Migration**: 100% feature parity with current system
2. **Performance**: ≤2s response time for AI analysis (current: 3-5s)
3. **Cost Reduction**: 30% reduction in monthly operational costs
4. **Zero Downtime**: Seamless transition without service interruption
5. **Maintainability**: Simplified codebase with Google SDKs

### Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| AI Response Time (p95) | 3-5s | ≤2s | Cloud Monitoring |
| Monthly Cost | $150-200 | $80-120 | GCP billing |
| API Availability | 99.5% | 99.95% | Uptime monitoring |
| Email Processing | 10-15s | 5-8s | End-to-end time |
| Deployment Time | 15-20 min | <5 min | CI/CD pipeline |
| Code Maintainability | Medium | High | Tech debt score |

### Key Performance Indicators (KPIs)
- **Email Triage Accuracy**: >90% (maintain current level)
- **Task Extraction Precision**: >85% (maintain current level)
- **User Satisfaction**: 4.5/5 stars
- **System Uptime**: 99.95%
- **Bug Report Rate**: <5 per month

---

## 3. Current Architecture Overview

### Current Stack
```
┌─────────────────────────────────────────────────────┐
│                    CURRENT SYSTEM                    │
├─────────────────────────────────────────────────────┤
│                                                       │
│  Frontend: Next.js 14 + React + TypeScript          │
│  ├─ Tailwind CSS                                    │
│  ├─ Lucide Icons                                    │
│  └─ Axios for API calls                             │
│                                                       │
│  Backend: FastAPI (Python 3.11)                     │
│  ├─ SQLAlchemy ORM                                  │
│  ├─ Alembic Migrations                              │
│  ├─ OAuth 2.0 (Google)                              │
│  └─ RESTful API                                     │
│                                                       │
│  Database: PostgreSQL 15 (Docker)                   │
│  └─ Self-hosted on local/VPS                        │
│                                                       │
│  AI/ML: OpenAI GPT-4o                               │
│  ├─ Email triage & analysis                         │
│  ├─ Task extraction                                 │
│  ├─ Operations chat                                 │
│  └─ Daily digest generation                         │
│                                                       │
│  Integrations:                                       │
│  ├─ Gmail API                                       │
│  ├─ Google Calendar API                             │
│  ├─ Google Tasks API                                │
│  └─ Twilio (SMS)                                    │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### Key Features Requiring Migration
1. **Email Triage System**
   - Gmail API integration
   - GPT-4o analysis of email threads
   - Priority scoring
   - Task extraction with deadlines

2. **Operations Chat Assistant (AUBS)**
   - GPT-4o powered conversational AI
   - Context-aware responses
   - Session management
   - Chat history persistence

3. **Task Management**
   - Eisenhower Matrix prioritization
   - Deadline tracking
   - Google Tasks integration
   - Bulk operations

4. **ChiliHead 5-Pillar Delegations**
   - Delegation tracking
   - 5-pillar framework
   - Follow-up system

5. **Calendar Integration**
   - Event extraction from emails
   - Google Calendar sync

6. **SMS Notifications**
   - Twilio integration
   - Critical alerts

---

## 4. Google Ecosystem Strategy

### Philosophy
**"Cloud-Native Google First"** - Leverage Google's ecosystem for maximum integration and minimal external dependencies.

### Core Principles
1. **Native Services First**: Use GCP services before third-party
2. **Managed Over Self-Hosted**: Cloud Run, Cloud SQL over VMs
3. **Gemini for All AI**: Single AI provider for consistency
4. **Workspace Integration**: Deep Gmail, Calendar, Tasks integration
5. **Serverless Architecture**: Auto-scaling, pay-per-use
6. **Infrastructure as Code**: Terraform for reproducibility

### Google Services Selected

| Function | Google Service | Alternative Considered | Rationale |
|----------|---------------|----------------------|-----------|
| Compute | Cloud Run | Cloud Functions, GKE | Best balance of simplicity/power |
| Database | Cloud SQL (PostgreSQL) | Firestore, Spanner | SQL compatibility, managed |
| AI/ML | Gemini 2.0 Flash | Gemini Pro | Speed + cost for high volume |
| Authentication | Identity Platform | Firebase Auth | Enterprise features |
| Storage | Cloud Storage | Persistent Disk | Object storage for attachments |
| Secrets | Secret Manager | Environment vars | Secure credential management |
| Monitoring | Cloud Monitoring | Stackdriver legacy | Native integration |
| Logging | Cloud Logging | Self-hosted ELK | Managed, searchable logs |

---

## 5. Technical Architecture (Google Stack)

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     GOOGLE CLOUD PLATFORM                       │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              FRONTEND (Vercel or Firebase Hosting)    │     │
│  │  ┌────────────────────────────────────────────┐     │     │
│  │  │  Next.js 14 App                             │     │     │
│  │  │  ├─ App Router                              │     │     │
│  │  │  ├─ React 18 + TypeScript                   │     │     │
│  │  │  ├─ Tailwind CSS                            │     │     │
│  │  │  └─ Google Identity Sign-In                 │     │     │
│  │  └────────────────────────────────────────────┘     │     │
│  └──────────────────────────────────────────────────────┘     │
│                           ↕ HTTPS                               │
│  ┌──────────────────────────────────────────────────────┐     │
│  │        BACKEND (Cloud Run - Auto-scaling)            │     │
│  │  ┌────────────────────────────────────────────┐     │     │
│  │  │  FastAPI Application                        │     │     │
│  │  │  ├─ REST API Routes                         │     │     │
│  │  │  ├─ Gemini AI Client                        │     │     │
│  │  │  ├─ Google Workspace APIs                   │     │     │
│  │  │  │  ├─ Gmail API                            │     │     │
│  │  │  │  ├─ Calendar API                         │     │     │
│  │  │  │  └─ Tasks API                            │     │     │
│  │  │  └─ SQLAlchemy ORM                          │     │     │
│  │  └────────────────────────────────────────────┘     │     │
│  └──────────────────────────────────────────────────────┘     │
│                           ↕                                     │
│  ┌──────────────────────────────────────────────────────┐     │
│  │       DATABASE (Cloud SQL PostgreSQL 15)             │     │
│  │  ├─ Tables: tasks, delegations, email_state          │     │
│  │  ├─ Chat history: chat_sessions, chat_messages       │     │
│  │  ├─ Private IP connection                            │     │
│  │  └─ Automated backups                                │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              AI/ML (Gemini API)                      │     │
│  │  ├─ Gemini 2.0 Flash (Email Analysis)               │     │
│  │  ├─ Gemini 2.0 Flash (Chat Assistant)               │     │
│  │  ├─ Gemini Pro (Complex Analysis)                   │     │
│  │  └─ Function Calling for structured output          │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐     │
│  │            SUPPORTING SERVICES                       │     │
│  │  ├─ Cloud Storage (Email attachments)               │     │
│  │  ├─ Secret Manager (API keys, credentials)          │     │
│  │  ├─ Cloud Monitoring (Metrics & alerting)           │     │
│  │  ├─ Cloud Logging (Centralized logs)                │     │
│  │  └─ Identity Platform (OAuth 2.0)                   │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                  │
└────────────────────────────────────────────────────────────────┘

      ↕ External Integrations (Unchanged)
      
┌────────────────────────────────────────────────────────────────┐
│  - Twilio SMS API (unchanged)                                   │
│  - Google Workspace (Gmail, Calendar, Tasks)                    │
└────────────────────────────────────────────────────────────────┘
```

### Architecture Decisions

#### Why Cloud Run?
- **Auto-scaling**: 0 → 100 instances based on load
- **Pay-per-use**: No cost when idle
- **Container-native**: Easy Docker deployment
- **Fast cold starts**: <1s for Python FastAPI
- **Built-in load balancing**: No extra config

#### Why Cloud SQL (PostgreSQL)?
- **Managed Service**: Automatic backups, patching, HA
- **SQL Compatibility**: Zero schema changes required
- **Performance**: Similar to self-hosted PostgreSQL
- **Private IP**: Secure Cloud Run → DB connection
- **Migration Path**: pg_dump/restore from Docker

#### Why Gemini 2.0 Flash?
- **Speed**: 2-3x faster than GPT-4o for similar tasks
- **Cost**: ~60% cheaper than GPT-4o ($0.075/$0.30 per 1M tokens)
- **Multimodal**: Native support for images, PDFs
- **Function Calling**: Structured outputs without hacks
- **Context**: 1M token context window (vs 128k GPT-4o)

---

## 6. Detailed Component Mapping

### 6.1 AI/ML Migration (OpenAI → Gemini)

#### Current OpenAI Implementation
```python
# Current: services/smart_assistant.py
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": email_content}
    ],
    temperature=0.7,
    max_tokens=2000
)

analysis = response.choices[0].message.content
```

#### New Gemini Implementation
```python
# New: services/gemini_assistant.py
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY"))

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    system_instruction=SYSTEM_PROMPT,
    generation_config={
        "temperature": 0.7,
        "top_p": 0.95,
        "max_output_tokens": 8192,
    }
)

response = model.generate_content(email_content)
analysis = response.text
```

#### Gemini Models Mapping

| Current (OpenAI) | New (Gemini) | Use Case | Cost Comparison |
|------------------|--------------|----------|-----------------|
| GPT-4o | Gemini 2.0 Flash | Email triage, chat | 60% cheaper |
| GPT-4o (complex) | Gemini 2.0 Pro | Complex analysis | 40% cheaper |
| GPT-4o-mini | Gemini 1.5 Flash | Simple tasks | 70% cheaper |

#### Function Calling Migration

**Current (OpenAI):**
```python
functions = [{
    "name": "extract_tasks",
    "description": "Extract actionable tasks",
    "parameters": {
        "type": "object",
        "properties": {
            "tasks": {"type": "array", "items": {...}}
        }
    }
}]
```

**New (Gemini):**
```python
from google.generativeai.types import FunctionDeclaration, Tool

extract_tasks_func = FunctionDeclaration(
    name="extract_tasks",
    description="Extract actionable tasks from email",
    parameters={
        "type": "object",
        "properties": {
            "tasks": {"type": "array", "items": {...}}
        }
    }
)

tool = Tool(function_declarations=[extract_tasks_func])
```

### 6.2 Database Migration (Docker PostgreSQL → Cloud SQL)

#### Migration Steps
1. **Export Current Data**
   ```bash
   # From Docker container
   docker exec chilihead_opsmanager_db pg_dump \
     -U openinbox \
     -d openinbox_dev \
     -F c \
     -f backup.dump
   ```

2. **Create Cloud SQL Instance**
   ```bash
   gcloud sql instances create chilihead-opsmanager \
     --database-version=POSTGRES_15 \
     --tier=db-f1-micro \
     --region=us-central1 \
     --network=default \
     --enable-google-private-path
   ```

3. **Import Data**
   ```bash
   gcloud sql import sql chilihead-opsmanager \
     gs://chilihead-backups/backup.dump \
     --database=openinbox_dev
   ```

#### Connection String Changes

**Current:**
```python
DATABASE_URL = "postgresql://openinbox:devpass123@localhost:5432/openinbox_dev"
```

**New (Cloud Run → Cloud SQL):**
```python
# Via Unix socket (recommended)
DATABASE_URL = "postgresql://openinbox:password@/openinbox_dev?host=/cloudsql/project-id:us-central1:chilihead-opsmanager"

# Or via Private IP
DATABASE_URL = "postgresql://openinbox:password@10.0.0.3:5432/openinbox_dev"
```

#### Schema Compatibility
- **Zero changes required**: Cloud SQL PostgreSQL 15 is 100% compatible
- Keep Alembic migrations as-is
- SQLAlchemy code unchanged

### 6.3 Gmail Integration (OAuth 2.0 → Google Identity Platform)

#### Current Implementation
```python
# Current: routes/oauth.py
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# OAuth flow
credentials = Credentials.from_authorized_user_info(token_data)
service = build('gmail', 'v1', credentials=credentials)
```

#### New Implementation (Enhanced)
```python
# New: With Google Identity Platform
from google.auth.transport.requests import Request
from google.oauth2.id_token import verify_oauth2_token
import google.auth

# Cloud Run receives authenticated requests
id_token = request.headers.get('Authorization').split('Bearer ')[1]
claims = verify_oauth2_token(id_token, Request())

# Use service account with domain-wide delegation
credentials = service_account.Credentials.from_service_account_file(
    'service-account-key.json',
    scopes=['https://www.googleapis.com/auth/gmail.readonly'],
    subject=claims['email']  # Impersonate user
)

service = build('gmail', 'v1', credentials=credentials)
```

**Benefits:**
- No user OAuth flow needed (use domain-wide delegation)
- Service account manages all Gmail access
- Better for enterprise/team use

### 6.4 Frontend Hosting Options

#### Option A: Vercel (Recommended)
**Pros:**
- Zero-config Next.js hosting
- Edge network (fast globally)
- Automatic HTTPS
- Preview deployments
- Free tier generous

**Cons:**
- Not pure Google ecosystem
- Vendor lock-in risk

#### Option B: Firebase Hosting
**Pros:**
- Pure Google solution
- CDN included
- Free SSL
- Firebase SDK integration

**Cons:**
- Manual Next.js config
- Less optimized for Next.js

#### Option C: Cloud Run (SSR)
**Pros:**
- Same service as backend
- Full control
- Auto-scaling

**Cons:**
- More expensive
- Slower cold starts

**Recommendation:** Use **Firebase Hosting** with Cloud Run backend for 100% Google solution.

### 6.5 Secrets Management

#### Current (.env files)
```bash
# server/.env
OPENAI_API_KEY=sk-...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

#### New (Secret Manager)
```python
# services/secrets.py
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8')

# Usage
GEMINI_API_KEY = get_secret("gemini-api-key")
```

**Benefits:**
- Centralized secret management
- Automatic rotation support
- Access logging
- No secrets in code/env files

---

## 7. Database Strategy

### Cloud SQL Configuration

#### Instance Specs
```yaml
Instance Type: db-f1-micro (Development)
  - vCPUs: 0.6 shared
  - RAM: 614 MB
  - Storage: 10 GB SSD
  - Cost: ~$7/month

Instance Type: db-g1-small (Production)
  - vCPUs: 1 shared
  - RAM: 1.7 GB
  - Storage: 20 GB SSD
  - Cost: ~$25/month
```

#### Terraform Configuration
```hcl
# infrastructure/database.tf
resource "google_sql_database_instance" "chilihead_db" {
  name             = "chilihead-opsmanager"
  database_version = "POSTGRES_15"
  region           = "us-central1"

  settings {
    tier = "db-g1-small"
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
    }

    maintenance_window {
      day          = 7  # Sunday
      hour         = 3  # 3 AM
      update_track = "stable"
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }
}

resource "google_sql_database" "openinbox_dev" {
  name     = "openinbox_dev"
  instance = google_sql_database_instance.chilihead_db.name
}

resource "google_sql_user" "app_user" {
  name     = "openinbox"
  instance = google_sql_database_instance.chilihead_db.name
  password = random_password.db_password.result
}
```

### Migration Checklist
- [ ] Export data from Docker PostgreSQL
- [ ] Create Cloud SQL instance
- [ ] Configure private IP networking
- [ ] Import data to Cloud SQL
- [ ] Update connection strings
- [ ] Test application connectivity
- [ ] Enable automated backups
- [ ] Set up monitoring/alerts
- [ ] Document rollback procedure

---

## 8. Authentication & Security

### Google Identity Platform Setup

#### OAuth 2.0 Configuration
```yaml
OAuth Client:
  - Type: Web application
  - Authorized redirect URIs:
    - https://your-domain.com/oauth/callback
    - http://localhost:3001/oauth/callback (dev)
  - Scopes:
    - https://www.googleapis.com/auth/gmail.readonly
    - https://www.googleapis.com/auth/calendar
    - https://www.googleapis.com/auth/tasks
    - openid
    - email
    - profile
```

#### Service Account (Domain-Wide Delegation)
For enterprise Gmail access without per-user OAuth:

```yaml
Service Account:
  - Name: chilihead-opsmanager-sa
  - Roles:
    - Cloud SQL Client
    - Secret Manager Secret Accessor
    - Storage Object Viewer
  - Domain-Wide Delegation:
    - Enable for Gmail API
    - Authorized scopes: gmail.readonly, calendar, tasks
```

#### IAM Roles
```yaml
Cloud Run Service:
  - Service Account: chilihead-opsmanager-sa@project.iam.gserviceaccount.com
  - Permissions:
    - cloudsql.instances.connect
    - secretmanager.versions.access
    - storage.objects.get
    - aiplatform.endpoints.predict

Users:
  - Role: Cloud Run Invoker
  - Authenticated via Google Identity
```

### Security Best Practices

1. **No Secrets in Code**
   - Use Secret Manager for all sensitive data
   - Rotate secrets quarterly

2. **Private Networking**
   - Cloud SQL on private IP (no public internet)
   - VPC Service Controls

3. **Least Privilege**
   - Service accounts with minimal permissions
   - No user credentials in backend

4. **Encryption**
   - Data at rest: Automatic (Cloud SQL)
   - Data in transit: TLS 1.3 (Cloud Run)

5. **Audit Logging**
   - Enable Cloud Audit Logs
   - Monitor API access patterns

---

## 9. AI/ML Integration (Gemini)

### Gemini API Setup

#### API Key Configuration
```python
# config/gemini.py
import google.generativeai as genai
from google.cloud import secretmanager

def get_gemini_client():
    """Initialize Gemini client with API key from Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    api_key_secret = f"projects/{PROJECT_ID}/secrets/gemini-api-key/versions/latest"
    api_key = client.access_secret_version(name=api_key_secret).payload.data.decode()
    
    genai.configure(api_key=api_key)
    return genai
```

#### Model Selection Strategy

| Task | Model | Reasoning |
|------|-------|-----------|
| Email Triage | Gemini 2.0 Flash | Speed + Cost |
| Complex Analysis | Gemini 2.0 Pro | Accuracy |
| Chat Assistant | Gemini 2.0 Flash | Real-time |
| Daily Digest | Gemini 2.0 Flash | Batch processing |
| Task Extraction | Gemini 2.0 Flash + Function Calling | Structured output |

### Prompt Engineering for Gemini

#### System Instructions (Gemini-Optimized)
```python
AUBS_SYSTEM_INSTRUCTION = """
You are AUBS (Auburn Hills Assistant), an operations AI for Chili's Restaurant #605.

CORE CAPABILITIES:
1. Email Analysis: Understand restaurant operations emails
2. Task Extraction: Identify actionable items with deadlines
3. Priority Assessment: Categorize urgency (URGENT/HIGH/NORMAL/FYI)
4. Context Awareness: Know restaurant lingo and operations

RESPONSE FORMAT:
- Use markdown headings
- Be concise but complete
- Extract specific deadlines
- Provide actionable next steps

PERSONALITY:
Professional, efficient, supportive. No patronizing language.
"""
```

#### Function Declarations
```python
# services/gemini_functions.py
from google.generativeai.types import FunctionDeclaration, Schema

extract_tasks_declaration = FunctionDeclaration(
    name="extract_actionable_tasks",
    description="Extract specific tasks from email with deadlines and priority",
    parameters=Schema(
        type="object",
        properties={
            "tasks": Schema(
                type="array",
                items=Schema(
                    type="object",
                    properties={
                        "action": Schema(type="string", description="Action verb + description"),
                        "due_date": Schema(type="string", description="ISO 8601 date or 'ASAP'"),
                        "priority": Schema(type="string", enum=["URGENT", "HIGH", "NORMAL", "FYI"]),
                        "estimated_duration": Schema(type="string", description="e.g., '15 min', '1 hour'"),
                        "details": Schema(type="string", description="WHO/WHAT/WHERE details")
                    },
                    required=["action", "priority"]
                )
            ),
            "priority_level": Schema(type="string", enum=["URGENT", "HIGH", "NORMAL", "FYI"]),
            "summary": Schema(type="string", description="Brief analysis")
        },
        required=["tasks", "priority_level", "summary"]
    )
)
```

### Migration Strategy for AI Components

#### Phase 1: Parallel Testing (Week 1-2)
- Run both OpenAI and Gemini side-by-side
- Compare outputs for 100+ emails
- Measure latency, quality, cost
- Adjust prompts for Gemini quirks

#### Phase 2: Gradual Rollout (Week 3-4)
- 25% of emails → Gemini
- Monitor quality metrics
- User feedback collection
- Increase to 50%, then 100%

#### Phase 3: Full Cutover (Week 5)
- Remove OpenAI dependency
- Update all code paths
- Final testing

### Cost Comparison

#### OpenAI Costs (Current)
```
Email Analysis:
- Average: 1,500 tokens input + 500 output
- GPT-4o: $5/1M input, $15/1M output
- 100 emails/day = 150k input + 50k output/month
- Cost: $0.75 + $0.75 = $1.50/month (low volume)

Chat Assistant:
- Average: 500 input + 300 output per message
- 50 messages/day = 750k input + 450k output/month
- Cost: $3.75 + $6.75 = $10.50/month

Total OpenAI: ~$12/month (current low usage)
Total OpenAI: ~$80-120/month (projected high usage)
```

#### Gemini Costs (Projected)
```
Email Analysis:
- Gemini 2.0 Flash: $0.075/1M input, $0.30/1M output
- Same volume: 150k input + 50k output/month
- Cost: $0.01 + $0.015 = $0.025/month

Chat Assistant:
- Same volume: 750k input + 450k output/month
- Cost: $0.056 + $0.135 = $0.19/month

Total Gemini: ~$0.22/month (current low usage)
Total Gemini: ~$25-40/month (projected high usage)

SAVINGS: 50-60% at high volume
```

---

## 10. Frontend Migration

### Firebase Hosting Setup

#### Project Structure
```
client/
├── .firebaserc
├── firebase.json
├── next.config.js (updated)
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── components/
├── public/
└── package.json
```

#### Firebase Configuration
```json
{
  "hosting": {
    "public": "out",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "/api/:path*",
        "function": "api"
      },
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(jpg|jpeg|gif|png|svg|webp|js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000, immutable"
          }
        ]
      }
    ]
  }
}
```

#### Next.js Configuration
```javascript
// next.config.js
module.exports = {
  output: 'export',  // Static export for Firebase Hosting
  images: {
    unoptimized: true  // Firebase doesn't support Next.js image optimization
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://api-xxxxx.run.app'
  }
}
```

#### Deployment Commands
```bash
# Build Next.js app
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting

# Or use GitHub Actions for CI/CD
```

### API Client Updates

#### Current (Axios)
```typescript
// Unchanged - just update base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});
```

#### Add Google Identity
```typescript
// lib/auth.ts
import { GoogleAuthProvider, signInWithPopup } from 'firebase/auth';

const signInWithGoogle = async () => {
  const provider = new GoogleAuthProvider();
  provider.addScope('https://www.googleapis.com/auth/gmail.readonly');
  provider.addScope('https://www.googleapis.com/auth/calendar');
  
  const result = await signInWithPopup(auth, provider);
  const idToken = await result.user.getIdToken();
  
  // Send to backend
  apiClient.defaults.headers['Authorization'] = `Bearer ${idToken}`;
};
```

---

## 11. API Structure

### Cloud Run Deployment

#### Dockerfile
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Cloud Run expects PORT env var
ENV PORT=8080

# Run with gunicorn for production
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 0 app:app
```

#### Cloud Build Configuration
```yaml
# cloudbuild.yaml
steps:
  # Build container
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/chilihead-api:$SHORT_SHA', '.']
  
  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/chilihead-api:$SHORT_SHA']
  
  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'chilihead-api'
      - '--image=gcr.io/$PROJECT_ID/chilihead-api:$SHORT_SHA'
      - '--region=us-central1'
      - '--platform=managed'
      - '--allow-unauthenticated'
      - '--set-env-vars=PROJECT_ID=$PROJECT_ID'
      - '--add-cloudsql-instances=$PROJECT_ID:us-central1:chilihead-opsmanager'

images:
  - 'gcr.io/$PROJECT_ID/chilihead-api:$SHORT_SHA'
```

#### Terraform Cloud Run Service
```hcl
# infrastructure/cloud_run.tf
resource "google_cloud_run_service" "chilihead_api" {
  name     = "chilihead-api"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/chilihead-api:latest"
        
        ports {
          container_port = 8080
        }

        env {
          name  = "DATABASE_URL"
          value = "postgresql://..."
        }

        env {
          name = "GEMINI_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.gemini_key.secret_id
              key  = "latest"
            }
          }
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }

      service_account_name = google_service_account.chilihead_sa.email
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
        "autoscaling.knative.dev/minScale" = "0"
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.chilihead_db.connection_name
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_binding" "noauth" {
  service  = google_cloud_run_service.chilihead_api.name
  location = google_cloud_run_service.chilihead_api.location
  role     = "roles/run.invoker"
  members  = ["allUsers"]
}
```

---

## 12. Implementation Phases

### Phase 0: Preparation (Week 1)
**Goals:** Environment setup, dependencies, planning

**Tasks:**
- [ ] Create GCP project (`chilihead-opsmanager`)
- [ ] Enable required APIs:
  - Gemini AI API
  - Cloud Run API
  - Cloud SQL API
  - Secret Manager API
  - Cloud Build API
  - Identity Platform API
- [ ] Set up billing account
- [ ] Install Google Cloud SDK locally
- [ ] Set up GitHub repository for new version
- [ ] Document current system behavior (baseline)

**Deliverables:**
- GCP project configured
- Local development environment ready
- Migration plan finalized

---

### Phase 1: Database Migration (Week 2)
**Goals:** Move PostgreSQL from Docker to Cloud SQL

**Tasks:**
- [ ] Create Cloud SQL PostgreSQL 15 instance
- [ ] Configure private IP networking
- [ ] Export data from Docker PostgreSQL
- [ ] Import to Cloud SQL
- [ ] Test connection from local machine
- [ ] Update DATABASE_URL in .env
- [ ] Verify all queries work
- [ ] Set up automated backups
- [ ] Document rollback procedure

**Success Criteria:**
- All data successfully migrated
- Zero data loss
- Query performance ≥ current
- Automated backups enabled

**Rollback Plan:**
- Keep Docker PostgreSQL running in parallel for 2 weeks
- Can revert DATABASE_URL instantly

---

### Phase 2: Backend Migration (Week 3-4)
**Goals:** Migrate FastAPI to Cloud Run, integrate Gemini

#### Week 3: Gemini Integration
**Tasks:**
- [ ] Replace OpenAI client with Gemini client
- [ ] Update `services/smart_assistant.py` → `services/gemini_assistant.py`
- [ ] Implement function calling for task extraction
- [ ] Parallel testing (OpenAI vs Gemini)
- [ ] Adjust prompts for Gemini quirks
- [ ] Measure latency & quality

#### Week 4: Cloud Run Deployment
**Tasks:**
- [ ] Create Dockerfile
- [ ] Test container locally
- [ ] Set up Cloud Build pipeline
- [ ] Deploy to Cloud Run (staging)
- [ ] Configure Cloud SQL connection
- [ ] Set up Secret Manager for API keys
- [ ] Configure custom domain
- [ ] Load testing (100 concurrent requests)
- [ ] Deploy to production

**Success Criteria:**
- API response time <2s (p95)
- All endpoints functional
- Zero downtime deployment
- Cost <$10/month (low traffic)

**Rollback Plan:**
- Keep FastAPI running locally/VPS for 1 week
- Can switch frontend to old backend URL

---

### Phase 3: Frontend Migration (Week 5)
**Goals:** Deploy Next.js to Firebase Hosting

**Tasks:**
- [ ] Update API base URL to Cloud Run endpoint
- [ ] Configure Firebase Hosting
- [ ] Build static export
- [ ] Deploy to Firebase (staging)
- [ ] Test all features
- [ ] Set up custom domain
- [ ] Configure SSL certificate
- [ ] Deploy to production

**Success Criteria:**
- All pages load <2s
- API calls successful
- Mobile responsive
- HTTPS enabled

**Rollback Plan:**
- Keep current frontend deployment for 1 week
- Can revert DNS instantly

---

### Phase 4: Integration Testing (Week 6)
**Goals:** End-to-end testing, optimization

**Tasks:**
- [ ] Test email triage flow (100 emails)
- [ ] Test operations chat (50 messages)
- [ ] Test task management (CRUD operations)
- [ ] Test delegations system
- [ ] Test calendar integration
- [ ] Load testing (simulate 1000 users)
- [ ] Security audit
- [ ] Performance optimization
- [ ] Bug fixes

**Success Criteria:**
- All features working
- No critical bugs
- Performance meets targets
- Security audit passed

---

### Phase 5: Monitoring & Optimization (Week 7-8)
**Goals:** Production monitoring, cost optimization

**Tasks:**
- [ ] Set up Cloud Monitoring dashboards
- [ ] Configure alerting (errors, latency, cost)
- [ ] Analyze Gemini token usage
- [ ] Optimize prompts for cost
- [ ] Review Cloud SQL query performance
- [ ] Implement caching strategy
- [ ] Document operational procedures
- [ ] Create runbook

**Success Criteria:**
- Monitoring dashboards live
- Alerts configured
- Cost <$50/month
- Documentation complete

---

### Phase 6: Decommission Old System (Week 9)
**Goals:** Shut down old infrastructure

**Tasks:**
- [ ] Verify new system stable (30-day uptime)
- [ ] Export final backup from old system
- [ ] Shut down Docker PostgreSQL container
- [ ] Remove old VPS/hosting (if applicable)
- [ ] Archive old codebase
- [ ] Update documentation
- [ ] Celebrate! 🎉

---

## 13. Risk Analysis & Mitigation

### High-Risk Items

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data loss during migration | Low | Critical | Full backup before migration, parallel running for 2 weeks |
| Gemini quality degradation | Medium | High | Parallel testing, gradual rollout, fallback to OpenAI |
| Cost overrun | Medium | Medium | Set billing alerts, monitor token usage, optimize prompts |
| Cloud Run cold starts | Medium | Medium | Set min instances to 1, optimize container size |
| Gmail API rate limits | Low | Medium | Implement exponential backoff, caching |
| Security vulnerabilities | Low | Critical | Security audit, IAM least privilege, Secret Manager |

### Medium-Risk Items

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Frontend deployment issues | Medium | Low | Test staging first, use Firebase preview channels |
| Database connection issues | Low | Medium | Connection pooling, retry logic, health checks |
| Gemini API outage | Low | Medium | Implement circuit breaker, fallback gracefully |
| Learning curve (Gemini) | High | Low | Extensive testing, documentation |

### Rollback Strategy

**Database Migration:**
- Keep Docker PostgreSQL running for 2 weeks
- Can revert connection string in seconds

**Backend Migration:**
- Keep old FastAPI running for 1 week
- Frontend can switch backend URL via env var

**Frontend Migration:**
- Keep old deployment for 1 week
- DNS change takes 5 minutes

**Gemini Migration:**
- Keep OpenAI client code commented for 1 month
- Can uncomment and redeploy in 10 minutes

---

## 14. Cost Analysis

### Current Costs (Estimated)

| Service | Provider | Cost/Month |
|---------|----------|------------|
| Compute (VPS) | Self-hosted/Vercel | $5-10 |
| Database (Docker) | Self-hosted | $0 (local) |
| OpenAI API | OpenAI | $80-120 (projected) |
| Gmail API | Google | $0 (free tier) |
| Twilio SMS | Twilio | $5 |
| **Total** | | **$90-135** |

### Projected Costs (Google Cloud)

#### Development/Low Traffic
| Service | Tier | Cost/Month |
|---------|------|------------|
| Cloud Run | Free tier (2M requests) | $0 |
| Cloud SQL | db-f1-micro | $7 |
| Gemini API | Free tier (60 requests/min) | $0 |
| Cloud Storage | 5 GB | $0.10 |
| Secret Manager | 10 secrets | $0.06 |
| Cloud Logging | 50 GB | $0 (free tier) |
| Cloud Monitoring | Basic | $0 (free tier) |
| Firebase Hosting | 10 GB/month | $0 (free tier) |
| **Total** | | **~$7-10** |

#### Production/High Traffic
| Service | Tier | Cost/Month |
|---------|------|------------|
| Cloud Run | 500k requests | $10 |
| Cloud SQL | db-g1-small | $25 |
| Gemini API | 10M tokens/month | $15 |
| Cloud Storage | 50 GB | $1 |
| Secret Manager | 50 secrets | $0.30 |
| Cloud Logging | 200 GB | $10 |
| Cloud Monitoring | 50 metrics | $5 |
| Firebase Hosting | 50 GB transfer | $0 |
| Twilio SMS | Same | $5 |
| **Total** | | **~$71** |

### Cost Savings Summary

| Scenario | Current | Google Cloud | Savings |
|----------|---------|--------------|---------|
| Development | $10-20 | $7-10 | 30-50% |
| Low Traffic | $50-80 | $30-40 | 40% |
| High Traffic | $120-150 | $71-90 | 40% |

**Annual Savings:** $500-700/year

---

## 15. Timeline & Milestones

### Gantt Chart
```
Week 1  [■■■■■■■■■■] Phase 0: Preparation
Week 2  [■■■■■■■■■■] Phase 1: Database Migration
Week 3  [■■■■■■■■■■] Phase 2a: Gemini Integration
Week 4  [■■■■■■■■■■] Phase 2b: Cloud Run Deployment
Week 5  [■■■■■■■■■■] Phase 3: Frontend Migration
Week 6  [■■■■■■■■■■] Phase 4: Integration Testing
Week 7  [■■■■■■■■■■] Phase 5: Monitoring Setup
Week 8  [■■■■■■■■■■] Phase 5: Optimization
Week 9  [■■■■■■■■■■] Phase 6: Decommission Old System
```

### Key Milestones

| Week | Milestone | Success Criteria |
|------|-----------|------------------|
| 1 | GCP Environment Ready | All APIs enabled, billing configured |
| 2 | Database Migrated | All data in Cloud SQL, zero loss |
| 4 | Backend on Cloud Run | API accessible, <2s response time |
| 5 | Frontend on Firebase | All pages working, HTTPS enabled |
| 6 | Full System Test | 100% feature parity |
| 8 | Production Ready | 99.9% uptime, monitoring live |
| 9 | Old System Decommissioned | Clean cutover complete |

---

## 16. Success Criteria

### Technical Metrics

| Metric | Current | Target | Measurement Method |
|--------|---------|--------|-------------------|
| API Response Time (p95) | 3-5s | <2s | Cloud Monitoring |
| Email Processing Time | 10-15s | 5-8s | Application logs |
| Database Query Time (p95) | 50-100ms | <50ms | Cloud SQL metrics |
| System Uptime | 99.5% | 99.95% | Cloud Monitoring |
| Cold Start Time | N/A | <1s | Cloud Run metrics |
| Error Rate | <1% | <0.5% | Application logs |

### Business Metrics

| Metric | Current | Target | Measurement Method |
|--------|---------|--------|-------------------|
| Monthly Cost | $90-135 | $50-90 | GCP Billing |
| Email Triage Accuracy | 90% | ≥90% | Manual review |
| Task Extraction Recall | 85% | ≥85% | Manual review |
| User Satisfaction | N/A | 4.5/5 | Survey |
| Bug Report Rate | ~10/month | <5/month | Issue tracker |

### Operational Metrics

| Metric | Current | Target | Measurement Method |
|--------|---------|--------|-------------------|
| Deployment Time | 15-20 min | <5 min | CI/CD logs |
| Time to Resolve Issues | ~2 hours | <1 hour | Incident tracking |
| Documentation Coverage | 60% | 90% | Code review |
| Test Coverage | 40% | 70% | pytest coverage |

### Definition of Success
✅ **Migration is successful when:**
1. All features working with 100% parity
2. Performance targets met or exceeded
3. Cost reduced by 30%
4. Zero critical bugs after 30 days
5. User satisfaction ≥4.5/5
6. Team comfortable with new stack

---

## 17. Appendix: Code Examples

### A. Complete Gemini Service Implementation

See the full implementation in the companion file: `google_migration_gemini_service.py`

Key features:
- Gemini 2.0 Flash integration
- Function calling for structured task extraction
- AUBS personality system
- Email thread analysis
- Daily digest generation

### B. Deployment Scripts

**deploy.sh** - One-command deployment to Cloud Run
**cloudbuild.yaml** - Automated CI/CD pipeline
**Dockerfile** - Production container image

### C. Infrastructure as Code

**Terraform modules** for:
- Cloud SQL database
- Cloud Run service
- VPC networking
- Secret Manager
- IAM roles and service accounts

---

## Next Steps

1. **Review this PRD** with stakeholders
2. **Get approval** for budget and timeline
3. **Set up GCP project** and begin Phase 0
4. **Start migration** following the phased approach
5. **Use Google AI Studio** to prototype Gemini prompts

---

**Document Status:** Draft  
**Last Updated:** November 19, 2025  
**Next Review:** Upon approval  

---

*Built with ❤️ for operational excellence at Chili's Auburn Hills #605*
