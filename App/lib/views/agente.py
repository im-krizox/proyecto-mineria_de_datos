"""Vista 6 — Agente conversacional sobre los datos del negocio.

Entrada escrita -> Gemini (via :mod:`lib.llm`), con fallback automático al
motor rule-based si no hay API key configurada o la llamada falla.
Botones de sugerencias / follow-ups -> motor rule-based directo
(determinista, instantáneo, sin costo).
"""
from __future__ import annotations

import streamlit as st

from .. import agent as A
from .. import llm as L
from .. import theme as T


# ---------------------------------------------------------------------------
#  CSS local de la vista
# ---------------------------------------------------------------------------

def _chat_css() -> str:
    """Hoja de estilo del chat, construida con los tokens del tema activo."""
    return f"""
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
    background: rgba(245,166,35,0.08);
    border-color: rgba(245,166,35,0.35);
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
.fuente-tag {{
    display: inline-block;
    margin-top: 10px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9.5px; letter-spacing: 0.14em;
    text-transform: uppercase; font-weight: 600;
    padding: 2px 8px; border-radius: 4px;
    border: 1px solid {T.BORDER};
    color: {T.TEXT_MUTED};
}}
.fuente-tag.llm {{
    color: {T.SKY};
    border-color: rgba(84,182,240,0.45);
    background: rgba(84,182,240,0.08);
}}
.fuente-tag.rules {{
    color: {T.AMBER};
    border-color: rgba(245,166,35,0.45);
    background: rgba(245,166,35,0.06);
}}
.fuente-tag.error {{
    color: #f87171;
    border-color: rgba(248,113,113,0.55);
    background: rgba(248,113,113,0.08);
}}
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
    background: rgba(245,166,35,0.06) !important;
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


def _fuente_tag(resp: A.AgentResponse) -> str:
    """Etiqueta visual que dice si la respuesta vino de Gemini o de las reglas."""
    intent = (resp.intent or "").lower()
    if intent.startswith("llm:"):
        if intent.endswith(":viz_error") or ":unknown:" in intent:
            return '<span class="fuente-tag error">Gemini · viz fallida</span>'
        return '<span class="fuente-tag llm">Respuesta generada por Gemini</span>'
    if intent == "fallback":
        return '<span class="fuente-tag error">Modo rápido · sin match</span>'
    return '<span class="fuente-tag rules">Modo rápido · motor de reglas</span>'


def _render_response(resp: A.AgentResponse, idx: int = 0) -> None:
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
            st.plotly_chart(resp.chart, use_container_width=True, theme=None,
                             key=f"agente_chart_{idx}")

        if resp.table is not None and not resp.table.empty:
            col_config = {}
            if resp.table_config:
                for col, cfg in resp.table_config.items():
                    if "format" in cfg:
                        col_config[col] = st.column_config.NumberColumn(
                            format=cfg["format"])
            st.dataframe(resp.table, use_container_width=True,
                          hide_index=True, height=min(380, 42 + 36 * len(resp.table)),
                          column_config=col_config,
                          key=f"agente_table_{idx}")

        st.markdown(_fuente_tag(resp), unsafe_allow_html=True)


def _render_user_message(text: str) -> None:
    st.markdown(
        '<div class="chat-bubble user"><div class="who">Tú</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(text)


# ---------------------------------------------------------------------------
#  Render principal
# ---------------------------------------------------------------------------

def _handle_query(query: str, *, use_llm: bool) -> None:
    """Procesa un mensaje del usuario y lo agrega al historial.

    ``use_llm=True`` para preguntas escritas libres (llamada a Gemini con
    fallback rule-based). ``use_llm=False`` para los botones, que se
    benefician de la respuesta determinista del motor rule-based.
    """
    if use_llm:
        resp = L.answer_or_fallback(query, st.session_state.chat_history)
    else:
        # Botones: ruta determinista, sin tocar el estado de error de Gemini.
        resp = A.route(query)
    st.session_state.chat_history.append(("user", query, None))
    st.session_state.chat_history.append(("assistant", None, resp))
    st.session_state.last_followups = resp.followups


def render():
    st.markdown(_chat_css(), unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "last_followups" not in st.session_state:
        st.session_state.last_followups = []

    # ---- Encabezado ---------------------------------------------------
    llm_on = L.is_available()
    meta = ("respuestas generadas con LLM (Gemini) — botones quedan en modo rápido"
            if llm_on
            else "modo rápido determinista — sin clave de Gemini configurada")
    st.markdown(T.section("Conversa con los datos del negocio",
                           badge="Asistente",
                           meta=meta),
                 unsafe_allow_html=True)

    if llm_on:
        callout = (
            "Escribe una pregunta como si se la hicieras a un analista del equipo. "
            "El asistente entiende preguntas sobre el negocio, los retrasos en "
            "entregas, los tipos de vendedores, los avisos de inventario para los "
            "próximos días y la <strong>certeza de las predicciones</strong>. "
            "Las preguntas escritas se responden con un modelo de lenguaje sobre "
            "el snapshot de datos del proyecto; los botones dan respuestas "
            "rápidas predefinidas."
        )
    else:
        callout = (
            "Escribe una pregunta como si se la hicieras a un analista del equipo. "
            "El asistente entiende preguntas sobre el negocio, los retrasos en "
            "entregas, los tipos de vendedores, los avisos de inventario para los "
            "próximos días y la <strong>certeza de las predicciones</strong>. "
            "Si no sabes por dónde empezar, usa las sugerencias de abajo."
        )
    st.markdown(T.callout(callout), unsafe_allow_html=True)

    st.markdown(T.method_note(
        "El asistente combina dos métodos. Las preguntas escritas se responden "
        "con un <strong>modelo de lenguaje</strong> (Gemini), al que se le "
        "entrega un resumen con las cifras del tablero como única fuente: "
        "tiene instruido no inventar datos. Los botones usan un "
        "<strong>motor de reglas</strong> determinista, que da siempre la "
        "misma respuesta exacta. Si el modelo de lenguaje no está disponible, "
        "todo cae automáticamente al motor de reglas.",
        label="Cómo funciona el asistente",
    ), unsafe_allow_html=True)

    # ---- Diagnóstico de Gemini --------------------------------------
    last_err = st.session_state.get("_llm_last_error")
    if last_err and L.is_available():
        st.warning(
            f"La última pregunta no la respondió Gemini · motivo: {last_err}",
            icon=":material/warning:",
        )

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
                    _handle_query(sugg, use_llm=False)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ---- Historial ---------------------------------------------------
    for i, entry in enumerate(st.session_state.chat_history):
        kind, text, resp = entry
        if kind == "user":
            _render_user_message(text)
        else:
            _render_response(resp, idx=i)

    # ---- Sugerencias de seguimiento (después de la última respuesta) -
    if st.session_state.last_followups:
        st.markdown('<div class="followup-label">Sigue preguntando</div>',
                     unsafe_allow_html=True)
        st.markdown('<div class="suggestion-grid">', unsafe_allow_html=True)
        cols = st.columns(min(3, len(st.session_state.last_followups)))
        for i, sugg in enumerate(st.session_state.last_followups):
            with cols[i % len(cols)]:
                if st.button(sugg, key=f"sugg_followup_{i}_{len(st.session_state.chat_history)}"):
                    _handle_query(sugg, use_llm=False)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ---- Caja de entrada ---------------------------------------------
    placeholder = ("Escribe tu pregunta…"
                   if L.is_available()
                   else "Escribe tu pregunta… (modo respuestas rápidas)")
    query = st.chat_input(placeholder)
    if query:
        _handle_query(query, use_llm=True)
        st.rerun()
