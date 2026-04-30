api: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
ingestor: python -m ingestion.fetch_events
enricher: python -m ingestion.enrich_repos
dashboard: streamlit run dashboard.py --server.address 0.0.0.0 --server.port $PORT --server.headless true
