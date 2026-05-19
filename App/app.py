"""Smart Supply Chain — Streamlit dashboard.

Entry point. Arma la navegación lateral (Inicio / Tablero), el conmutador de
tema (oscuro / claro) e inyecta el CSS del tema antes de delegar cada vista a
su módulo en `lib/views/`.

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
    inicio, overview, prediccion, pronostico, sellers, calidad, agente,
)


# ---- Page config -----------------------------------------------------------
st.set_page_config(
    page_title="Smart Supply Chain · Nexus Supply",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Smart Supply Chain — UNAM Minería de Datos 2026",
    },
)


# ---- Sidebar: navegación + tema --------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="side-brand">Nexus Supply · 2016 – 2018</div>'
        '<div class="side-title">Smart Supply Chain</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="side-cap">Navegación</div>', unsafe_allow_html=True)
    page = st.radio(
        "Sección", ["Inicio", "Tablero de análisis"],
        label_visibility="collapsed",
    )
    st.markdown('<div class="side-cap">Apariencia</div>', unsafe_allow_html=True)
    modo_claro = st.toggle("Modo claro", value=False, key="modo_claro")


# ---- Tema activo (oscuro por defecto) --------------------------------------
T.apply("light" if modo_claro else "dark")
st.markdown(T.css(), unsafe_allow_html=True)


# ---- Páginas ---------------------------------------------------------------
if page == "Inicio":
    inicio.render()
else:
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
