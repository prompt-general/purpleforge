# PurpleForge

Detection validation layer for attack technique execution.

## Milestone 1: Execution Tracking (Completed)

- [x] CLI Wrapper for Stratus Red Team
- [x] Celery + Redis for async technique execution
- [x] Execution tracking & metadata persistence in PostgreSQL 16
- [x] FastAPI REST API (v1)
- [x] Dockerized Deployment

## Quick Start (with Docker)

1. **Install requirements** (if running locally):
   ```bash
   pip install -r requirements.txt
   ```

2. **Run infrastructure & application**:
   ```bash
   docker-compose up -d --build
   ```

3. **Initialize database** (if needed):
   ```bash
   docker-compose exec api python -m app.db.init_db
   ```

4. **Access the API**:
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
