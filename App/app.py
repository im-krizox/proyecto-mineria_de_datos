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
    overview, prediccion, pronostico, sellers, calidad, agente,
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
    title="Tablero de Operaciones Inteligente",
    subtitle=("Una vista clara y completa del negocio: cómo se comportan las "
              "ventas, dónde ocurren los retrasos en las entregas, qué se "
              "espera vender en las próximas dos semanas y qué tipo de "
              "vendedores tenemos. Todo en un mismo lugar, fácil de leer."),
), unsafe_allow_html=True)


# ---- Tabs ------------------------------------------------------------------
tabs = st.tabs([
    "Resumen del negocio",
    "Riesgo de retraso",
    "Pronóstico de ventas",
    "Tipos de vendedores",
    "Preparación de datos",
    "Asistente",
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
with tabs[5]:
    agente.render()
