import pandas as pd
import streamlit as st
from sqlalchemy import text

from app.db import engine

st.set_page_config(page_title="GH Signal Dashboard", layout="wide")
st.title("GH Signal — live ingestion dashboard")


@st.cache_data(ttl=30)
def load_events() -> pd.DataFrame:
    with engine.connect() as conn:
        df = pd.read_sql(
            text("SELECT id, type, actor, repo, created_at FROM events"),
            conn,
        )
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    return df


col_refresh, col_count = st.columns([1, 4])
if col_refresh.button("Refresh"):
    st.cache_data.clear()

df = load_events()
col_count.metric("Total events in DB", f"{len(df):,}")

if df.empty:
    st.warning(
        "No events in the database yet. Start `python -m ingestion.fetch_events` and reload."
    )
    st.stop()

st.subheader("Event types")
st.bar_chart(df["type"].value_counts())

col_repos, col_actors = st.columns(2)
with col_repos:
    st.subheader("Top 10 repos")
    st.bar_chart(df["repo"].value_counts().head(10))
with col_actors:
    st.subheader("Top 10 actors")
    st.bar_chart(df["actor"].value_counts().head(10))
