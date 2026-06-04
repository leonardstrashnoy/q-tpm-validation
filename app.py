import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Q-TPM Worldline Explorer", layout="wide")
st.title("Q-TPM 4D Block Space Validation Dashboard")

# Load data
@st.cache_data
def load_data():
    conn = sqlite3.connect("qtpm_validation.db")
    df = pd.read_sql("SELECT * FROM worldlines", conn)
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("Filters")
min_density = st.sidebar.slider("Min Local Density", 0.0, 5.0, 0.0)
max_density = st.sidebar.slider("Max Local Density", 0.0, 5.0, 5.0)
pathway_filter = st.sidebar.multiselect(
    "Show only these pathways active",
    ["expedient", "ruling_guide", "analytical", "revisionist", "value_driven", "global"]
)

# Apply filters
filtered = df[(df["local_density"] >= min_density) & (df["local_density"] <= max_density)]
if pathway_filter:
    for p in pathway_filter:
        filtered = filtered[filtered[p] == 1]

st.write(f"**Showing {len(filtered)} / {len(df)} halos**")

# === KPI Cards ===
col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg Curvature", f"{filtered['curvature'].mean():.4f}")
col2.metric("Revisionist %", f"{filtered['revisionist'].mean()*100:.1f}%")
col3.metric("High Interference %", f"{((filtered['expedient'] + filtered['global']) > 0).mean()*100:.1f}%")
col4.metric("Avg Stellar Fraction", f"{filtered['star_fraction'].mean():.3f}")

# === Pathway Activation ===
st.subheader("Pathway Activation Rates")
pathways = ["expedient", "ruling_guide", "analytical", "revisionist", "value_driven", "global"]
activation = filtered[pathways].mean().reset_index()
activation.columns = ["Pathway", "Activation Rate"]
fig = px.bar(activation, x="Pathway", y="Activation Rate", color="Activation Rate")
st.plotly_chart(fig, use_container_width=True)

# === Proposition Tests ===
st.subheader("Proposition Validation")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Prop 1: Non-commutativity (Revisionist curvature)**")
    rev = filtered[filtered["revisionist"] == 1]["curvature"]
    non_rev = filtered[filtered["revisionist"] == 0]["curvature"]
    st.write(f"Revisionist: {rev.mean():.4f} | Others: {non_rev.mean():.4f}")

with col2:
    st.markdown("**Prop 2: Interference Effect**")
    filtered["interference"] = filtered["expedient"] + filtered["global"]
    int_groups = filtered.groupby("interference")["curvature"].mean()
    st.write(int_groups)

# === Scatter: Curvature vs Density ===
st.subheader("Curvature vs Local Density")
fig2 = px.scatter(
    filtered, 
    x="local_density", 
    y="curvature", 
    color="revisionist",
    hover_data=["halo_id", "major_mergers"],
    title="Worldline Curvature vs Environment"
)
st.plotly_chart(fig2, use_container_width=True)

# === Data Table ===
st.subheader("Worldline Data")
st.dataframe(filtered[["halo_id", "mass", "local_density", "curvature", "star_fraction"] + pathways], 
             use_container_width=True, height=400)

# Footer
st.caption("Q-TPM 4D Block Space Validation | Synthetic data demo")