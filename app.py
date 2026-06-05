import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Q-TPM Dashboard", layout="wide", page_icon="🧬")
st.title("🧬 Q-TPM 4D Block Space Validation Dashboard")

# Load data
@st.cache_data
def load_data():
    conn = sqlite3.connect("qtpm_validation.db")
    df = pd.read_sql("SELECT * FROM worldlines", conn)
    return df

df = load_data()

# Sidebar
st.sidebar.header("Filters")
pathway_cols = ["expedient", "ruling_guide", "analytical", "revisionist", "value_driven", "global"]

min_density = st.sidebar.slider("Min Density", float(df["local_density"].min()), float(df["local_density"].max()), 0.0)
max_density = st.sidebar.slider("Max Density", float(df["local_density"].min()), float(df["local_density"].max()), float(df["local_density"].max()))

selected_pathways = st.sidebar.multiselect("Active Pathways", pathway_cols, default=pathway_cols)

filtered = df[(df["local_density"] >= min_density) & (df["local_density"] <= max_density)]
for p in selected_pathways:
    filtered = filtered[filtered[p] == 1]

st.caption(f"Showing **{len(filtered)}** halos out of {len(df)}")

# === KPI Row ===
k1, k2, k3, k4 = st.columns(4)
k1.metric("Avg Curvature", f"{filtered['curvature'].mean():.4f}")
k2.metric("High Interference", f"{((filtered['expedient'] + filtered['global']) > 1).mean()*100:.1f}%")
k3.metric("Revisionist %", f"{filtered['revisionist'].mean()*100:.1f}%")
k4.metric("Value-Driven %", f"{filtered['value_driven'].mean()*100:.1f}%")

# === Row 1: Pathway Activation + Interference ===
col1, col2 = st.columns(2)

with col1:
    st.subheader("Pathway Activation Rate")
    activation = filtered[pathway_cols].mean().reset_index()
    activation.columns = ["Pathway", "Rate"]
    fig = px.bar(activation, x="Pathway", y="Rate", color="Rate", 
                 color_continuous_scale="Viridis")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Pathway Interference Effect")
    filtered["interference"] = filtered["expedient"] + filtered["global"]
    fig2 = px.box(filtered, x="interference", y="curvature", 
                  title="Curvature vs Number of Interfering Pathways")
    st.plotly_chart(fig2, use_container_width=True)

# === Row 2: Proposition Validation ===
st.subheader("Proposition Validation")

p1, p2, p3 = st.columns(3)

with p1:
    st.markdown("**Prop 1: Non-commutativity**")
    rev = filtered[filtered["revisionist"] == 1]["curvature"]
    non = filtered[filtered["revisionist"] == 0]["curvature"]
    st.write(f"Revisionist: `{rev.mean():.4f}`")
    st.write(f"Non-revisionist: `{non.mean():.4f}`")
    st.progress(min(rev.mean() / 0.2, 1.0))

with p2:
    st.markdown("**Prop 2: Interference**")
    int_high = filtered[filtered["interference"] >= 1]["curvature"].mean()
    int_low = filtered[filtered["interference"] == 0]["curvature"].mean()
    st.write(f"High interference: `{int_high:.4f}`")
    st.write(f"Low interference: `{int_low:.4f}`")

with p3:
    st.markdown("**Prop 3: Value-Driven Stability**")
    vd = filtered[filtered["value_driven"] == 1]["path_curvature"].mean()
    non_vd = filtered[filtered["value_driven"] == 0]["path_curvature"].mean()
    st.write(f"Value-driven: `{vd:.5f}`")
    st.write(f"Others: `{non_vd:.5f}`")

# === Row 3: Scatter + Distribution ===
col3, col4 = st.columns(2)

with col3:
    st.subheader("Curvature vs Environment")
    fig3 = px.scatter(filtered, x="local_density", y="curvature", 
                      color="revisionist", size="mass",
                      hover_data=["halo_id"], 
                      color_continuous_scale="RdBu")
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Curvature Distribution")
    fig4 = px.histogram(filtered, x="curvature", nbins=40, 
                        color_discrete_sequence=["#636EFA"])
    st.plotly_chart(fig4, use_container_width=True)

# === Data Table ===
st.subheader("Worldline Data")
st.dataframe(
    filtered[["halo_id", "mass", "local_density", "curvature", "star_fraction"] + pathway_cols],
    use_container_width=True,
    height=300
)

st.caption("Q-TPM Validation Dashboard • Synthetic Data")