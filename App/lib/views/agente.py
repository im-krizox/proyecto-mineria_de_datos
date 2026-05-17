"""Vista 6 — Agente conversacional sobre los datos del negocio."""
from __future__ import annotations

import streamlit as st

from .. import agent as A
from .. import theme as T


# ---------------------------------------------------------------------------
#  CSS local de la vista
# ---------------------------------------------------------------------------

_CHAT_CSS = f"""
<style>
.chat-bubble {{
    background: {T.BG_CARD};
    border: 1px solid {T.BORDER};
    border-radius: 10px;
    padding: 14px 18px;
    margin: 6px 0;
    color: {T.TEXT};
    font-size: 13.5px;
    line-height: 1.6;
}}
.chat-bubble.user {{
    background: rgba(245,158,11,0.08);
    border-color: rgba(245,158,11,0.35);
    border-left: 3px solid {T.AMBER};
}}
.chat-bubble.assistant {{
    border-left: 3px solid {T.SKY};
}}
.chat-bubble .who {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.18em;
    text-transform: uppercase; font-weight: 600;
    margin-bottom: 8px;
}}
.chat-bubble.user .who {{ color: {T.AMBER}; }}
.chat-bubble.assistant .who {{ color: {T.SKY}; }}
.chat-bubble p {{ margin: 6px 0; }}
.chat-bubble ul {{ margin: 6px 0 6px 18px; padding: 0; }}
.chat-bubble li {{ margin: 3px 0; }}
.chip-row {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0 4px 0; }}
.followup-label {{
    color: {T.TEXT_MUTED};
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.16em;
    text-transform: uppercase; font-weight: 600;
    margin: 14px 0 6px 0;
}}
.suggestion-grid .stButton > button {{
    background: {T.BG_CARD} !important;
    color: {T.TEXT_DIM} !important;
    border: 1px solid {T.BORDER} !important;
    font-weight: 500 !important; font-size: 12px !important;
    text-align: left !important;
    padding: 8px 14px !important;
    width: 100%;
    white-space: normal !important;
    line-height: 1.4 !important;
}}
.suggestion-grid .stButton > button:hover {{
    border-color: {T.AMBER} !important;
    color: {T.TEXT} !important;
    background: rgba(245,158,11,0.06) !important;
}}
</style>
"""


# ---------------------------------------------------------------------------
#  Sugerencias iniciales (cuando aún no hay historial)
# ---------------------------------------------------------------------------

SUGERENCIAS_INICIO = [
    "¿Cómo va el negocio?",
    "¿Qué estados tienen más entregas tardías?",
    "¿Qué tan certero es el sistema para predecir retrasos?",
    "¿En qué categorías hay riesgo de quedarnos sin stock?",
    "¿Qué tipos de vendedores tenemos?",
    "¿Qué se espera vender en salud y belleza?",
    "¿Cuánto mejoró el modelo respecto a la versión 1?",
    "¿Los feriados afectan los retrasos?",
]


# ---------------------------------------------------------------------------
#  Helpers de render
# ---------------------------------------------------------------------------

def _bubble(who: str, text_md: str, kind: str) -> None:
    """Render markdown content inside a chat bubble shell."""
    label = "Tú" if kind == "user" else "Asistente"
    st.markdown(
        f'<div class="chat-bubble {kind}">'
        f'<div class="who">{label}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    # Streamlit no soporta markdown completo dentro de un div HTML;
    # lo dibujamos justo después como un st.markdown para que parse listas.
    st.markdown(text_md)


def _render_response(resp: A.AgentResponse) -> None:
    """Dibuja la respuesta del agente: texto, chips, tabla y/o gráfica."""
    with st.container():
        st.markdown(
            '<div class="chat-bubble assistant"><div class="who">Asistente</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(resp.text)

        if resp.chips:
            chips_html = "".join(T.chip(label, kind) for label, kind in resp.chips)
            st.markdown(f'<div class="chip-row">{chips_html}</div>',
                         unsafe_allow_html=True)

        if resp.chart is not None:
            st.plotly_chart(resp.chart, use_container_width=True, theme=None)

        if resp.table is not None and not resp.table.empty:
            col_config = {}
            if resp.table_config:
                for col, cfg in resp.table_config.items():
                    if "format" in cfg:
                        col_config[col] = st.column_config.NumberColumn(
                            format=cfg["format"])
            st.dataframe(resp.table, use_container_width=True,
                          hide_index=True, height=min(380, 42 + 36 * len(resp.table)),
                          column_config=col_config)


def _render_user_message(text: str) -> None:
    st.markdown(
        '<div class="chat-bubble user"><div class="who">Tú</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(text)


# ---------------------------------------------------------------------------
#  Render principal
# ---------------------------------------------------------------------------

def _handle_query(query: str) -> None:
    """Procesa un mensaje del usuario y lo agrega al historial."""
    resp = A.route(query)
    st.session_state.chat_history.append(("user", query, None))
    st.session_state.chat_history.append(("assistant", None, resp))
    st.session_state.last_followups = resp.followups


def render():
    st.markdown(_CHAT_CSS, unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "last_followups" not in st.session_state:
        st.session_state.last_followups = []

    # ---- Encabezado ---------------------------------------------------
    st.markdown(T.section("Conversa con los datos del negocio",
                           badge="Asistente",
                           meta="responde sobre ventas, retrasos, inventario y vendedores"),
                 unsafe_allow_html=True)

    st.markdown(T.callout(
        "Escribe una pregunta como si se la hicieras a un analista del equipo. "
        "El asistente entiende preguntas sobre el negocio, los retrasos en "
        "entregas, los tipos de vendedores, los avisos de inventario para los "
        "próximos días y la <strong>certeza de las predicciones</strong>. "
        "Si no sabes por dónde empezar, usa las sugerencias de abajo."
    ), unsafe_allow_html=True)

    # ---- Botón limpiar -----------------------------------------------
    col_clear, _ = st.columns([1, 4])
    with col_clear:
        if st.button("Limpiar conversación", key="agente_clear",
                      disabled=not st.session_state.chat_history):
            st.session_state.chat_history = []
            st.session_state.last_followups = []
            st.rerun()

    # ---- Sugerencias iniciales (si no hay historial) -----------------
    if not st.session_state.chat_history:
        st.markdown('<div class="followup-label">Prueba con una de estas preguntas</div>',
                     unsafe_allow_html=True)
        st.markdown('<div class="suggestion-grid">', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, sugg in enumerate(SUGERENCIAS_INICIO):
            with cols[i % 2]:
                if st.button(sugg, key=f"sugg_inicio_{i}"):
                    _handle_query(sugg)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ---- Historial ---------------------------------------------------
    for entry in st.session_state.chat_history:
        kind, text, resp = entry
        if kind == "user":
            _render_user_message(text)
        else:
            _render_response(resp)

    # ---- Sugerencias de seguimiento (después de la última respuesta) -
    if st.session_state.last_followups:
        st.markdown('<div class="followup-label">Sigue preguntando</div>',
                     unsafe_allow_html=True)
        st.markdown('<div class="suggestion-grid">', unsafe_allow_html=True)
        cols = st.columns(min(3, len(st.session_state.last_followups)))
        for i, sugg in enumerate(st.session_state.last_followups):
            with cols[i % len(cols)]:
                if st.button(sugg, key=f"sugg_followup_{i}_{len(st.session_state.chat_history)}"):
                    _handle_query(sugg)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ---- Caja de entrada ---------------------------------------------
    query = st.chat_input("Escribe tu pregunta…")
    if query:
        _handle_query(query)
        st.rerun()
