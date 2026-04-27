from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .db import SessionLocal
from .crud import get_top_repos

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
def top_repos(limit: int = 10, db: Session = Depends(get_db)):
    results = get_top_repos(db, limit)
    return [{"repo": r[0], "count": r[1]} for r in results]
