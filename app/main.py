from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from .db import SessionLocal
from .crud import get_top_repos, get_trending_languages

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "GitHub Events API is running"}

@app.get("/top-repos")
def top_repos(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    results = get_top_repos(db, limit)
    return [{"repo": r[0], "count": r[1]} for r in results]


@app.get("/languages/trending")
def languages_trending(
    window: int = Query(24, ge=1, le=24 * 30),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    results = get_trending_languages(db, window, limit)
    return [{"language": r[0], "count": r[1]} for r in results]
