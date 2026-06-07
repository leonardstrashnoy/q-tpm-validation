import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import numpy as np

st.set_page_config(page_title="Q-TPM Dashboard", layout="wide")

DB_PATH = "qtpm_validation.db"

def init_and_populate_db():
    """Create DB and generate synthetic data if missing or empty."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS worldlines (
            halo_id INTEGER PRIMARY KEY,
            snapshot INTEGER,
            mass REAL,
            stellar_mass REAL,
            local_density REAL,
            recent_growth REAL,
            star_fraction REAL,
            formation_snap INTEGER,
            major_mergers INTEGER,
            curvature REAL,
            path_curvature REAL,
            expedient INTEGER,
            ruling_guide INTEGER,
            analytical INTEGER,
            revisionist INTEGER,
            value_driven INTEGER,
            global INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()

    # Check if we need to populate
    count = c.execute("SELECT COUNT(*) FROM worldlines").fetchone()[0]
    if count == 0:
        st.info("Generating 400 synthetic halos for first run (this may take a moment)...")
        np.random.seed(42)
        data = []
        for i in range(400):
            log_mass = np.random.normal(11.5, 1.2)
            mass = 10 ** log_mass
            star_frac = max(0.008, min(0.09, np.random.beta(2, 5) * 0.12))
            stellar = mass * star_frac
            local_density = max(0.1, np.random.lognormal(0.3, 0.8))
            recent_growth = max(0.01, np.random.beta(2, 4) * 0.5)
            formation_snap = int(np.random.beta(1.5, 2.5) * 80 + 10)
            major_mergers = int(np.random.poisson(3.2))
            curvature = max(0.01, np.random.beta(2, 6) * 0.22)
            path_curv = max(0.005, np.random.beta(2, 7) * 0.15)

            pathways = {
                "expedient": int(recent_growth > 0.22 and local_density < 1.2),
                "ruling_guide": int(major_mergers <= 2),
                "analytical": int(star_frac > 0.035),
                "revisionist": int(curvature > 0.085),
                "value_driven": int(formation_snap < 38),
                "global": int(major_mergers > 5 or local_density > 2.8),
            }

            row = {
                "halo_id": 10000 + i,
                "snapshot": 99,
                "mass": round(mass, 2),
                "stellar_mass": round(stellar, 2),
                "local_density": round(local_density, 3),
                "recent_growth": round(recent_growth, 4),
                "star_fraction": round(star_frac, 4),
                "formation_snap": formation_snap,
                "major_mergers": major_mergers,
                "curvature": round(curvature, 5),
                "path_curvature": round(path_curv, 5),
                **pathways,
                "created_at": datetime.now().isoformat()
            }
            data.append(row)

        for row in data:
            c.execute("""
                INSERT OR REPLACE INTO worldlines VALUES
                (:halo_id, :snapshot, :mass, :stellar_mass, :local_density,
                 :recent_growth, :star_fraction, :formation_snap, :major_mergers,
                 :curvature, :path_curvature,
                 :expedient, :ruling_guide, :analytical, :revisionist,
                 :value_driven, :global, :created_at)
            """, row)
        conn.commit()
        st.success(f"Database ready with {len(data)} halos.")

    conn.close()
    return None  # connection closed after init; data loaded separately via load_data()

# Ensure DB exists and is populated (works both locally and on Streamlit Cloud)
init_and_populate_db()

@st.cache_data(ttl=3600)
def load_data():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    df = pd.read_sql("SELECT * FROM worldlines", conn)
    conn.close()
    return df

df = load_data()

st.title("🧬 Q-TPM 4D Block Space Validation Dashboard")

# Sidebar filters
pathway_cols = ["expedient", "ruling_guide", "analytical", "revisionist", "value_driven", "global"]
selected = st.sidebar.multiselect("Active Pathways", pathway_cols, default=pathway_cols)

filtered = df.copy()
for p in selected:
    filtered = filtered[filtered[p] == 1]

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["Overview", "Pathway Analysis", "Proposition Validation"])

with tab1:
    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Halos", len(filtered))
    c2.metric("Avg Curvature", f"{filtered['curvature'].mean():.4f}")
    c3.metric("Revisionist %", f"{filtered['revisionist'].mean()*100:.1f}%")
    c4.metric("Interference %", f"{((filtered['expedient'] + filtered['global']) > 1).mean()*100:.1f}%")

    # Charts
    st.subheader("Pathway Activation")
    activation = filtered[pathway_cols].mean().reset_index()
    activation.columns = ["Pathway", "Rate"]
    fig = px.bar(activation, x="Pathway", y="Rate")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Curvature vs Density")
    fig2 = px.scatter(filtered, x="local_density", y="curvature", color="revisionist")
    st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(filtered[["halo_id", "mass", "curvature"] + pathway_cols], use_container_width=True)

with tab2:
    st.subheader("Pathway Correlations")
    corr = filtered[pathway_cols].corr()
    fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r")
    st.plotly_chart(fig_corr, use_container_width=True)

    st.subheader("Pathway Distribution by Mass Quartile")
    filtered["mass_q"] = pd.qcut(filtered["mass"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    for p in pathway_cols:
        fig_p = px.box(filtered, x="mass_q", y="curvature", color=p)
        st.plotly_chart(fig_p, use_container_width=True)

with tab3:
    st.subheader("Formal Proposition Tests (from analyze_propositions.sql)")

    conn = sqlite3.connect(DB_PATH)

    # Prop 1
    st.markdown("### Proposition 1: Non-commutativity (Revisionist effect on curvature)")
    prop1 = pd.read_sql("""
        SELECT 
            revisionist,
            ROUND(AVG(curvature), 4) AS avg_curvature,
            COUNT(*) AS n
        FROM worldlines
        GROUP BY revisionist;
    """, conn)
    st.dataframe(prop1)

    # Prop 2
    st.markdown("### Proposition 2: Pathway interference")
    prop2 = pd.read_sql("""
        SELECT 
            (expedient + global) AS interfering_pathways,
            ROUND(AVG(curvature), 4) AS avg_curvature,
            COUNT(*) AS n
        FROM worldlines
        GROUP BY interfering_pathways
        ORDER BY interfering_pathways;
    """, conn)
    st.dataframe(prop2)

    # Prop 3
    st.markdown("### Proposition 3: Value-driven stability")
    prop3 = pd.read_sql("""
        SELECT 
            value_driven,
            ROUND(AVG(path_curvature), 5) AS stability,
            ROUND(AVG(local_density), 2) AS avg_density,
            COUNT(*) AS n
        FROM worldlines
        GROUP BY value_driven;
    """, conn)
    st.dataframe(prop3)

    # Prop 4
    st.markdown("### Proposition 4: Global halos in dense environments")
    prop4 = pd.read_sql("""
        SELECT 
            global,
            ROUND(AVG(local_density), 2) AS mean_density,
            ROUND(MAX(local_density), 2) AS max_density,
            COUNT(*) AS n
        FROM worldlines
        GROUP BY global;
    """, conn)
    st.dataframe(prop4)

    # Prop 5
    st.markdown("### Proposition 5: Analytical + Ruling-guide interaction")
    prop5 = pd.read_sql("""
        SELECT 
            analytical,
            ruling_guide,
            COUNT(*) AS count,
            ROUND(AVG(star_fraction), 3) AS avg_stellar_yield,
            ROUND(AVG(curvature), 4) AS avg_curvature
        FROM worldlines
        GROUP BY analytical, ruling_guide
        ORDER BY count DESC;
    """, conn)
    st.dataframe(prop5)

    conn.close()

st.sidebar.markdown("---")
st.sidebar.subheader("📦 Datasets")

# Current active dataset
conn = sqlite3.connect(DB_PATH)
current_count = conn.execute("SELECT COUNT(*) FROM worldlines").fetchone()[0]
conn.close()

st.sidebar.markdown(f"""
**Current Active**
- `qtpm_validation.db`  
  Source: Synthetic (realistic distributions)  
  Halos: **{current_count}**
""")

# Future / alternative datasets
st.sidebar.markdown("""
**Future / Potential Datasets**
- `qtpm_tng_real.db` — IllustrisTNG (TNG100-1) — requires valid API key
- `qtpm_cosmosim.db` — CosmoSim / Uchuu merger trees — planned
- Bolshoi / MultiDark — planned
- EAGLE / Horizon Run — planned
- Full TNG300-1 + TNG50-1 — planned (larger volume / higher resolution)
""")

st.sidebar.caption("Q-TPM Synthetic Validation v0.2")
# --- Help Section ---
with st.sidebar.expander("❓ Help & Pathway Guide", expanded=False):
    st.markdown("""
    **Q-TPM Ethical Pathways** (mapped to halo properties)

    - **Expedient** — Egoism: rapid recent growth + isolation  
    - **Ruling-guide** — Deontology: strict merger rules  
    - **Analytical** — Utilitarianism: high stellar conversion  
    - **Revisionist** — Relativism: high curvature/variance  
    - **Value-driven** — Virtue ethics: early formation + quiescence  
    - **Global** — Ethics of care: dense environment + many mergers

    **Propositions tested in Tab 3**
    1. Non-commutativity (Revisionist effect)
    2. Pathway interference
    3. Value-driven stability
    4. Global halos in dense environments
    5. Analytical + Ruling-guide interaction

    *Data is synthetic but uses realistic cosmological distributions.*
    """)

st.sidebar.caption("Q-TPM Synthetic Validation v0.3")
