# GitHub Events Pipeline 🚀

A real-time data pipeline that ingests public GitHub events, processes them, and exposes analytics via an API.

## Overview

This project builds a lightweight backend/data engineering system using the GitHub Events API. It demonstrates:

- API ingestion with rate limiting
- Idempotent data processing
- Relational data modeling
- Analytics queries over event streams
- REST API for insights

## Architecture

GitHub Events API
↓
Ingestion Service (Python)
↓
Processing Layer
↓
PostgreSQL Database
↓
FastAPI Server
↓
Analytics Endpoints

## Tech Stack

- Backend: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Ingestion: Python + Requests
- (Planned) Queue: Redis / Kafka
- (Planned) Orchestration: Airflow

## Features

### Data Ingestion
- Polls GitHub Events API every minute
- Handles duplicate events using upsert logic
- Extracts key fields: repo, actor, event type, timestamp

### Storage
- Normalized event schema
- Indexed fields for fast queries

### API Endpoints

#### `GET /top-repos`
Returns most active repositories by event count

#### `GET /`
Health check endpoint

## Example Response

```json
[
  {"repo": "torvalds/linux", "count": 42},
  {"repo": "microsoft/vscode", "count": 35}
]
