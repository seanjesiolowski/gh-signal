from datetime import datetime, timezone, timedelta

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


@st.cache_data(ttl=30)
def load_trending_languages(hours: int = 24, limit: int = 10) -> pd.DataFrame:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    with engine.connect() as conn:
        return pd.read_sql(
            text("""
                SELECT repos.language, COUNT(events.id) AS count
                FROM events
                JOIN repos ON repos.name = events.repo
                WHERE events.created_at >= :cutoff
                  AND repos.language IS NOT NULL
                GROUP BY repos.language
                ORDER BY count DESC
                LIMIT :limit
            """),
            conn,
            params={"cutoff": cutoff, "limit": limit},
        )


@st.cache_data(ttl=30)
def load_trending_topics(hours: int = 24, limit: int = 20) -> pd.DataFrame:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    with engine.connect() as conn:
        return pd.read_sql(
            text("""
                SELECT topic, COUNT(events.id) AS count
                FROM events
                JOIN repos ON repos.name = events.repo
                CROSS JOIN LATERAL json_array_elements_text(repos.topics) AS topic
                WHERE events.created_at >= :cutoff
                  AND repos.topics IS NOT NULL
                  AND repos.topics::text != '[]'
                GROUP BY topic
                ORDER BY count DESC
                LIMIT :limit
            """),
            conn,
            params={"cutoff": cutoff, "limit": limit},
        )


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

col_lang, col_topics = st.columns(2)
with col_lang:
    st.subheader("Trending languages (last 24 h)")
    lang_df = load_trending_languages()
    if lang_df.empty:
        st.info("No language data yet — run the enricher.")
    else:
        st.bar_chart(lang_df.set_index("language")["count"])
with col_topics:
    st.subheader("Trending topics (last 24 h)")
    topics_df = load_trending_topics()
    if topics_df.empty:
        st.info("No topic data yet — run the enricher.")
    else:
        st.bar_chart(topics_df.set_index("topic")["count"])
