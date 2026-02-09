"""Streamlit Dashboard - Marketing Automation Performance."""

import streamlit as st
import httpx
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="Marketing Automation Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Dashboard de Performance - Marketing Automation")

# Sidebar filters
st.sidebar.header("Filtros")
date_range = st.sidebar.date_input(
    "Período",
    value=(datetime.now() - timedelta(days=30), datetime.now()),
)
channel_filter = st.sidebar.multiselect(
    "Canais",
    ["WhatsApp", "Instagram", "Facebook", "Google Ads", "Site"],
    default=["WhatsApp", "Instagram", "Facebook", "Google Ads", "Site"],
)

# KPI Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Leads", "—", help="Total de leads no período")
with col2:
    st.metric("Conversões", "—", help="Leads convertidos em clientes")
with col3:
    st.metric("Taxa de Conversão", "—", help="% de leads convertidos")
with col4:
    st.metric("Tempo Médio de Fechamento", "—", help="Tempo médio em dias")

st.divider()

# Charts placeholders
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Leads por Canal")
    st.info("Conecte ao banco de dados para visualizar os dados reais.")

with col_right:
    st.subheader("Conversões por Mês")
    st.info("Conecte ao banco de dados para visualizar os dados reais.")

st.divider()

st.subheader("Atendimentos por Canal")
st.info("Dados serão carregados quando o sistema estiver conectado ao PostgreSQL.")

st.divider()

st.subheader("Comparativo Histórico")
st.info("Relatórios comparativos ano a ano serão implementados na Fase 4.")

# Footer
st.caption("Marketing Automation Dashboard v1.0 | Fase 1 - MVP")
