"""Render an architecture diagram for gh-signal as a PNG."""
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent.parent / "docs" / "architecture.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
ACCENT = "#2f81f7"
GREEN = "#3fb950"
ORANGE = "#d29922"
PURPLE = "#a371f7"
RED = "#f85149"

fig, ax = plt.subplots(figsize=(13, 8.5), dpi=160)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 13)
ax.set_ylim(0, 8.5)
ax.set_axis_off()


def box(x, y, w, h, label, sub, color):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.04,rounding_size=0.18",
        linewidth=2, edgecolor=color, facecolor="#161b22",
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h * 0.62, label,
            ha="center", va="center", color=FG, fontsize=12, fontweight="bold")
    ax.text(x + w / 2, y + h * 0.28, sub,
            ha="center", va="center", color=MUTED, fontsize=9)


def arrow(x1, y1, x2, y2, label="", color=MUTED, curve=0.0, label_offset=(0, 0.2)):
    a = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=16,
        linewidth=1.6, color=color,
        connectionstyle=f"arc3,rad={curve}",
    )
    ax.add_patch(a)
    if label:
        mx, my = (x1 + x2) / 2 + label_offset[0], (y1 + y2) / 2 + label_offset[1]
        ax.text(mx, my, label, ha="center", va="center",
                color=color, fontsize=8.5, style="italic")


# Title
ax.text(6.5, 8.05, "gh-signal", ha="center", color=FG, fontsize=22, fontweight="bold")
ax.text(6.5, 7.65,
        "Real-time pipeline that ingests GitHub public events and surfaces what devs are building in",
        ha="center", color=MUTED, fontsize=10.5)

# External source
box(0.4, 5.6, 3.0, 1.1, "GitHub Events API", "api.github.com/events", ACCENT)

# Ingestor
box(5.0, 5.6, 3.0, 1.1, "Ingestor", "ingestion/fetch_events.py", ORANGE)

# Postgres
box(9.6, 5.6, 3.0, 1.1, "PostgreSQL 16", "github_events  •  port 5433", GREEN)

# FastAPI
box(0.4, 2.5, 3.0, 1.1, "FastAPI", "app/main.py  •  :8000", PURPLE)

# Dashboard
box(5.0, 2.5, 3.0, 1.1, "Streamlit Dashboard", "dashboard.py  •  :8501", PURPLE)

# Tests / CI
box(9.6, 2.5, 3.0, 1.1, "pytest + CI", "tests/  •  GitHub Actions", RED)

# Consumers
box(2.7, 0.5, 3.0, 1.0, "REST clients", "GET /top-repos", MUTED)
box(6.3, 0.5, 3.0, 1.0, "Browser", "localhost:8501", MUTED)

# Arrows: source -> ingestor -> db
arrow(3.4, 6.15, 5.0, 6.15, "poll every ~60s", ACCENT)
arrow(8.0, 6.15, 9.6, 6.15, "upsert events", ORANGE)

# DB -> FastAPI and DB -> Dashboard (read paths)
arrow(9.7, 5.6, 3.4, 3.6, "SQLAlchemy read", GREEN, curve=-0.18, label_offset=(0, -0.25))
arrow(10.6, 5.6, 6.5, 3.6, "SQL read", GREEN, curve=-0.12, label_offset=(0.2, 0.0))

# DB -> tests (validates schema/queries)
arrow(11.5, 5.6, 11.1, 3.6, "integration tests", RED, curve=0.0)

# FastAPI -> REST clients
arrow(1.9, 2.5, 3.7, 1.5, "JSON", PURPLE, curve=0.1)

# Dashboard -> Browser
arrow(6.5, 2.5, 7.3, 1.5, "HTTP", PURPLE, curve=-0.1)

# Compose grouping note
ax.text(6.5, 4.55,
        "── all services orchestrated via docker-compose.yml ──",
        ha="center", color=MUTED, fontsize=9, style="italic")

# Legend
legend_handles = [
    mpatches.Patch(color=ACCENT, label="External source"),
    mpatches.Patch(color=ORANGE, label="Ingestion"),
    mpatches.Patch(color=GREEN,  label="Storage"),
    mpatches.Patch(color=PURPLE, label="Serving"),
    mpatches.Patch(color=RED,    label="Quality / CI"),
]
leg = ax.legend(handles=legend_handles, loc="lower left",
                bbox_to_anchor=(0.005, 0.0), frameon=False,
                fontsize=8.5, labelcolor=FG, ncol=5,
                handlelength=1.2, handleheight=1.0, columnspacing=1.4)

plt.savefig(OUT, dpi=160, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
print(f"wrote {OUT}")
