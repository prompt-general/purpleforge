# PurpleForge

Detection validation layer for attack technique execution.

## Milestone 1: Execution Tracking (Completed)

- [x] CLI Wrapper for Stratus Red Team
- [x] Celery + Redis for async technique execution
- [x] Execution tracking & metadata persistence in PostgreSQL 16
- [x] FastAPI REST API (v1)
- [x] Dockerized Deployment

## Milestone 2: Chains & Cleanup

- [x] DAG-based attack chain execution
- [x] Conditional branching logic
- [x] Cleanup verification and failure aborts

## Milestone 3: Cleanup Verification (Completed)

- [x] Store cleanup status per execution
- [x] Block chain completion when cleanup fails

## Milestone 4: Collaboration & RBAC

- [x] Multi-tenant exercise management
- [x] Comments, audit logs, role-based access control

## Spec 3 – Enterprise Platform

### M1: Campaign Ingestion
- [x] STIX-like campaign importer

### M2: Auto-chain Generation
- [x] Environment/asset-aware filtering
- [x] Linear DAG builder

### M3: Risk Scoring Engine
- [x] Risk = Likelihood × Impact × Detection Gap
- [x] Snapshot reporting

### M4: Stack Integrations
- [x] Webhook, Jira, ServiceNow, SOAR, Splunk connectors
- [x] Event broadcasting & ticket creation

### M5: Executive Reporting (Completed)
- [x] Overview metrics & full executive report API
- [x] Frontend dashboard tab

The platform now supports end-to-end adversary simulation, risk intelligence, and enterprise integrations.

## Next Steps
- Continuous scheduling and trend analytics
- Hardening: sandbox isolation, ephemeral credentials
- Expand executive UI or add export features

## Quick Start (with Docker)

1. **Install requirements** (if running locally):
   ```bash
   pip install -r requirements.txt
   ```

2. **Run infrastructure & application (Automatically initializes DB)**:
   ```bash
   docker-compose up -d --build
   ```

3. **Access the API**:
   - Web API: `http://localhost:8000`
   - Interactive Docs (Swagger): `http://localhost:8000/docs`

## Usage Examples

### 1. Register a Technique
```bash
curl -X POST "http://localhost:8000/api/v1/techniques/" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Stop CloudTrail Logging",
       "description": "Simulates stopping an AWS CloudTrail trail",
       "mitre_id": "aws.defense-evasion.cloudtrail-stop"
     }'
```

### 2. Trigger an Execution (Async)
```bash
curl -X POST "http://localhost:8000/api/v1/executions/" \
     -H "Content-Type: application/json" \
     -d '{"technique_id": 1}'
```

### 3. Check Status
```bash
curl "http://localhost:8000/api/v1/executions/1"
```

## Architecture
- **FastAPI**: Core REST API
- **Celery + Redis**: Task queue for simulation detonation
- **PostgreSQL 16**: Persistence of techniques and execution metadata
- **Stratus Red Team**: The underlying engine for simulated attacks
