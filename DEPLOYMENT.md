# Deployment Guide

PurpleForge relies on Docker and Docker Compose to easily orchestrate the backend API, the Celery async task workers, and the necessary data stores (PostgreSQL and Redis). 

## Prerequisites
- Docker Engine 20.10+
- Docker Compose v2+

## Architecture overview
The provided `docker-compose.yml` spins up 4 services:
1. `db`: PostgreSQL 16
2. `redis`: Redis 7
3. `api`: The FastAPI web server
4. `worker`: Scalable Celery instances (defaults to 2 replicas)

## Running the Application
To start the application, use the interactive terminal or your system terminal to run:
```bash
docker-compose up -d --build
```
> **Note:** The `docker-entrypoint.sh` script currently polls the database on launch. When the `db` container becomes healthy, the entrypoint will automatically initialize the database objects.

## Using the API
The API binds automatically to `localhost` on port `8000`. You can test it by visiting `http://localhost:8000/docs` in your browser.

## Managing the Execution Logs
If you want to view the stdout/stderr associated with the Celery processes to monitor the detonate executions:
```bash
docker-compose logs -f worker
```

## Teardown
To cleanly shut down your environment while retaining the persisted PostgreSQL data volume:
```bash
docker-compose down
```
If you wish to fully wipe the data and start from scratch, include the `-v` flag:
```bash
docker-compose down -v
```
