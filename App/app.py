"""Smart Supply Chain — Streamlit dashboard.

Entry point. Inyecta el tema visual, arma el hero y delega cada vista a su
módulo en `lib/views/`.

Ejecutar con:
    streamlit run App/app.py
o
    python -m streamlit run App/app.py
desde la raíz del proyecto.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from lib import theme as T  # noqa: E402
from lib.views import (   # noqa: E402
    overview, prediccion, pronostico, sellers, calidad,
)


# ---- Page config -----------------------------------------------------------
st.set_page_config(
    page_title="Smart Supply Chain · Predictive Ops",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "Smart Supply Chain — UNAM Minería de Datos 2026",
    },
)
st.markdown(T.CSS, unsafe_allow_html=True)


# ---- Hero ------------------------------------------------------------------
st.markdown(T.hero(
    eyebrow="Smart Supply Chain · Nexus Supply · 2016 – 2018",
    title="Predictive Operations Dashboard",
    subtitle=("Plataforma de inteligencia operativa sobre el dataset Olist. "
              "Diagnóstico de la cadena de suministro, modelo de predicción "
              "de retraso (Random Forest v2), pronóstico SARIMA de demanda y "
              "segmentación K-Means de sellers — todo en un solo cockpit."),
), unsafe_allow_html=True)


# ---- Tabs ------------------------------------------------------------------
tabs = st.tabs([
    "Visión general",
    "Predicción de retraso",
    "Pronóstico de demanda",
    "Segmentación de sellers",
    "Calidad de datos",
])

with tabs[0]:
    overview.render()
with tabs[1]:
    prediccion.render()
with tabs[2]:
    pronostico.render()
with tabs[3]:
    sellers.render()
with tabs[4]:
    calidad.render()
