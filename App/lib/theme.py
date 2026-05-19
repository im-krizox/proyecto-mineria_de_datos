"""Tema visual de la app — soporta modo oscuro (gris casi negro) y modo claro.

El modo se fija con :func:`apply` al inicio de cada ejecucion de la app.
Las vistas leen los tokens de color (``T.BG``, ``T.TEXT``, ...) en tiempo de
render, por lo que basta con llamar ``apply`` antes de dibujar nada.
"""
import re


def compact(html: str) -> str:
    """Colapsa whitespace para que el parser markdown no rompa el HTML."""
    return re.sub(r"\s+", " ", html).strip()


# --- Colores de enfasis (fijos en ambos modos) ------------------------------
AMBER       = "#f5a623"   # acento principal — combina con el gris casi negro
AMBER_DIM   = "#b45309"   # acento atenuado
EMERALD     = "#2dd4a7"   # positivo
ROSE        = "#f4607a"   # negativo / alerta
SKY         = "#54b6f0"   # info / azul frio
VIOLET      = "#a78bfa"   # categorico extra
SLATE       = "#8a8f99"   # gris neutro

# --- Paletas Plotly ---------------------------------------------------------
CATEGORICAL = [AMBER, SKY, EMERALD, VIOLET, ROSE, SLATE, "#fbbf24", "#22d3ee"]
SEQ_AMBER   = ["#3a2a08", "#5c3f0a", "#7a530c", "#a06a0e", "#c98711",
               "#f5a623", "#f7b94f", "#f9cd83", "#fbe0b3"]
DIVERGING   = ["#2dd4a7", "#7ee0c4", "#bdeede", "#fbe0b3", "#f7b94f",
               "#f5a623", "#f4607a"]


# --- Paletas de neutros por modo --------------------------------------------
PALETTES = {
    "dark": {
        # Gris oscuro casi negro
        "BG":         "#0d0d0f",
        "BG_CARD":    "#161619",
        "BG_ELEV":    "#202024",
        "BORDER":     "#2a2a30",
        "BORDER_HI":  "#3d3d46",
        "TEXT":       "#ededf0",
        "TEXT_DIM":   "#a3a3ad",
        "TEXT_MUTED": "#71717a",
        "GLOW":       ("radial-gradient(1100px 560px at 6% -12%, "
                       "rgba(245,166,35,0.07), transparent 60%), "
                       "radial-gradient(900px 480px at 96% 0%, "
                       "rgba(84,182,240,0.05), transparent 60%), "),
        "BTN_TEXT":   "#1a1300",
        "SHADOW":     "0 1px 3px rgba(0,0,0,0.4)",
    },
    "light": {
        "BG":         "#f6f6f7",
        "BG_CARD":    "#ffffff",
        "BG_ELEV":    "#ededef",
        "BORDER":     "#e3e3e7",
        "BORDER_HI":  "#cacad2",
        "TEXT":       "#1a1a1f",
        "TEXT_DIM":   "#55555f",
        "TEXT_MUTED": "#8b8b95",
        "GLOW":       ("radial-gradient(1100px 560px at 6% -12%, "
                       "rgba(245,166,35,0.10), transparent 60%), "
                       "radial-gradient(900px 480px at 96% 0%, "
                       "rgba(84,182,240,0.08), transparent 60%), "),
        "BTN_TEXT":   "#1a1300",
        "SHADOW":     "0 1px 3px rgba(20,20,30,0.08)",
    },
}

# Tokens de neutros — se reasignan con apply(). Por defecto, modo oscuro.
MODE       = "dark"
BG         = PALETTES["dark"]["BG"]
BG_CARD    = PALETTES["dark"]["BG_CARD"]
BG_ELEV    = PALETTES["dark"]["BG_ELEV"]
BORDER     = PALETTES["dark"]["BORDER"]
BORDER_HI  = PALETTES["dark"]["BORDER_HI"]
TEXT       = PALETTES["dark"]["TEXT"]
TEXT_DIM   = PALETTES["dark"]["TEXT_DIM"]
TEXT_MUTED = PALETTES["dark"]["TEXT_MUTED"]
GLOW       = PALETTES["dark"]["GLOW"]
BTN_TEXT   = PALETTES["dark"]["BTN_TEXT"]
SHADOW     = PALETTES["dark"]["SHADOW"]


def apply(mode: str = "dark") -> None:
    """Fija el modo activo y reasigna los tokens de neutros del modulo."""
    global MODE, BG, BG_CARD, BG_ELEV, BORDER, BORDER_HI
    global TEXT, TEXT_DIM, TEXT_MUTED, GLOW, BTN_TEXT, SHADOW
    mode = mode if mode in PALETTES else "dark"
    p = PALETTES[mode]
    MODE = mode
    BG, BG_CARD, BG_ELEV = p["BG"], p["BG_CARD"], p["BG_ELEV"]
    BORDER, BORDER_HI = p["BORDER"], p["BORDER_HI"]
    TEXT, TEXT_DIM, TEXT_MUTED = p["TEXT"], p["TEXT_DIM"], p["TEXT_MUTED"]
    GLOW, BTN_TEXT, SHADOW = p["GLOW"], p["BTN_TEXT"], p["SHADOW"]


def plotly_template() -> dict:
    """Plotly template alineado con el modo activo."""
    return {
        "layout": {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor":  "rgba(0,0,0,0)",
            "font": {
                "family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                "color":  TEXT,
                "size":   13,
            },
            "title": {
                "font": {"family": "Inter, sans-serif", "color": TEXT, "size": 15},
                "x": 0.01, "xanchor": "left",
                "pad": {"t": 8, "b": 4},
            },
            "colorway": CATEGORICAL,
            "xaxis": {
                "gridcolor": BORDER, "zerolinecolor": BORDER,
                "linecolor": BORDER, "tickcolor": BORDER,
                "tickfont": {"color": TEXT_DIM, "size": 11},
                "title": {"font": {"color": TEXT_DIM, "size": 12}},
            },
            "yaxis": {
                "gridcolor": BORDER, "zerolinecolor": BORDER,
                "linecolor": BORDER, "tickcolor": BORDER,
                "tickfont": {"color": TEXT_DIM, "size": 11},
                "title": {"font": {"color": TEXT_DIM, "size": 12}},
            },
            "legend": {
                "font": {"color": TEXT, "size": 12},
                "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
            },
            "hoverlabel": {
                "bgcolor": BG_ELEV, "bordercolor": BORDER_HI,
                "font":    {"color": TEXT, "family": "Inter, sans-serif"},
            },
            "margin": {"l": 56, "r": 24, "t": 48, "b": 48},
        }
    }


# --- CSS global (plantilla con placeholders %(TOKEN)s) ----------------------
_CSS_TEMPLATE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: %(TEXT)s;
}

.stApp { background: %(GLOW)s %(BG)s; }

/* --- Ancho completo ---------------------------------------------------- */
.block-container {
    max-width: 100%% !important;
    padding-top: 1.4rem; padding-bottom: 3rem;
    padding-left: 2.6rem; padding-right: 2.6rem;
}
header[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }

/* --- Sidebar ----------------------------------------------------------- */
[data-testid="stSidebar"] {
    background: %(BG_CARD)s;
    border-right: 1px solid %(BORDER)s;
}
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: %(TEXT)s; letter-spacing: -0.01em;
}
.side-brand {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.20em; text-transform: uppercase;
    color: %(AMBER)s; font-weight: 700; margin-bottom: 2px;
}
.side-title {
    font-size: 17px; font-weight: 700; color: %(TEXT)s;
    line-height: 1.2; margin-bottom: 16px;
}
.side-cap {
    color: %(TEXT_MUTED)s; font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase;
    font-weight: 600; margin: 10px 0 4px 0;
}

/* --- Hero / encabezado de pagina --------------------------------------- */
.hero {
    border-bottom: 1px solid %(BORDER)s;
    padding: 0 0 18px 0; margin-bottom: 22px;
    display: flex; flex-direction: column; gap: 6px;
}
.hero .eyebrow {
    color: %(AMBER)s; font-family: 'JetBrains Mono', monospace;
    font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase;
    font-weight: 600;
}
.hero h1 {
    font-size: 30px; font-weight: 700; color: %(TEXT)s;
    margin: 0; line-height: 1.12; letter-spacing: -0.01em;
}
.hero .subtitle { color: %(TEXT_DIM)s; font-size: 14px; max-width: 860px; }

/* --- KPI cards --------------------------------------------------------- */
.kpi-grid {
    display: grid; gap: 16px;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    margin: 8px 0 22px 0;
}
.kpi {
    background: %(BG_CARD)s;
    border: 1px solid %(BORDER)s;
    border-radius: 10px; padding: 18px 20px;
    position: relative; box-shadow: %(SHADOW)s;
    transition: border-color 0.2s ease, transform 0.2s ease;
}
.kpi:hover { border-color: %(BORDER_HI)s; transform: translateY(-1px); }
.kpi .label {
    color: %(TEXT_MUTED)s; font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase;
    font-weight: 600; margin-bottom: 8px;
}
.kpi .value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 27px; font-weight: 600; color: %(TEXT)s;
    letter-spacing: -0.01em; line-height: 1.05;
}
.kpi .unit {
    font-family: 'Inter', sans-serif; color: %(TEXT_DIM)s;
    font-size: 14px; font-weight: 500; margin-left: 4px;
}
.kpi .delta { font-size: 12px; margin-top: 6px; font-family: 'JetBrains Mono', monospace; }
.kpi .delta.up { color: %(EMERALD)s; }
.kpi .delta.down { color: %(ROSE)s; }
.kpi .delta.neutral { color: %(TEXT_DIM)s; }
.kpi .accent {
    position: absolute; left: 0; top: 18px; bottom: 18px;
    width: 3px; background: %(AMBER)s; border-radius: 0 2px 2px 0;
}
.kpi .hint {
    color: %(TEXT_DIM)s; font-size: 11.5px; margin-top: 8px;
    line-height: 1.45;
}

/* --- Section heading --------------------------------------------------- */
.section {
    display: flex; align-items: baseline; gap: 12px;
    margin: 28px 0 12px 0; padding-bottom: 8px;
    border-bottom: 1px solid %(BORDER)s;
}
.section h2 {
    font-size: 18px; font-weight: 600; color: %(TEXT)s;
    margin: 0; letter-spacing: -0.01em;
}
.section .badge {
    font-family: 'JetBrains Mono', monospace; color: %(AMBER)s;
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.16em; text-transform: uppercase;
}
.section .meta {
    margin-left: auto; color: %(TEXT_MUTED)s;
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
}

/* --- Tabs (barra a todo el ancho) -------------------------------------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px; border-bottom: 1px solid %(BORDER)s;
    margin-bottom: 18px; width: 100%%;
}
.stTabs [data-baseweb="tab"] {
    flex: 1 1 0; justify-content: center;
    background: transparent; color: %(TEXT_DIM)s;
    border: none; border-radius: 8px 8px 0 0;
    padding: 13px 18px; font-weight: 600; font-size: 13px;
    transition: all 0.18s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: %(TEXT)s; background: rgba(245,166,35,0.06);
}
.stTabs [aria-selected="true"] {
    color: %(AMBER)s !important;
    border-bottom: 2px solid %(AMBER)s !important;
    background: rgba(245,166,35,0.09) !important;
}

/* --- Buttons ----------------------------------------------------------- */
.stButton > button {
    background: %(AMBER)s; color: %(BTN_TEXT)s; border: none;
    font-weight: 600; font-size: 13px;
    padding: 8px 18px; border-radius: 6px; letter-spacing: 0.02em;
    transition: filter 0.15s ease;
}
.stButton > button:hover { filter: brightness(1.08); color: %(BTN_TEXT)s; }
.stButton > button:focus { box-shadow: none; outline: 1px solid %(AMBER)s; }

/* --- Inputs ------------------------------------------------------------ */
.stSelectbox label, .stSlider label, .stNumberInput label,
.stCheckbox label, .stRadio label, .stTextInput label, .stDateInput label,
.stMultiSelect label {
    color: %(TEXT_DIM)s !important;
    font-size: 11px !important; font-weight: 600 !important;
    letter-spacing: 0.05em; text-transform: uppercase;
}
.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div,
.stTextInput div[data-baseweb="input"], .stNumberInput div[data-baseweb="input"] {
    background: %(BG_CARD)s !important;
    border-color: %(BORDER)s !important;
    color: %(TEXT)s !important;
}
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="menu"], [data-baseweb="popover"] ul {
    background: %(BG_CARD)s !important;
    border: 1px solid %(BORDER)s !important;
}
[data-baseweb="menu"] li { color: %(TEXT)s !important; }

/* --- Dataframes -------------------------------------------------------- */
[data-testid="stDataFrame"] {
    border: 1px solid %(BORDER)s; border-radius: 8px;
    background: %(BG_CARD)s;
}

/* --- Metrics nativas --------------------------------------------------- */
[data-testid="stMetric"] {
    background: %(BG_CARD)s; border: 1px solid %(BORDER)s;
    border-radius: 10px; padding: 14px 16px;
}
[data-testid="stMetricLabel"] {
    color: %(TEXT_MUTED)s !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important; letter-spacing: 0.14em;
    text-transform: uppercase; font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    color: %(TEXT)s !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
}

/* --- Alert chips ------------------------------------------------------- */
.chip {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 10px; border-radius: 999px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; font-weight: 600;
    letter-spacing: 0.10em; text-transform: uppercase;
    border: 1px solid;
}
.chip.alert  { color: %(ROSE)s;    border-color: rgba(244,96,122,0.45);  background: rgba(244,96,122,0.10); }
.chip.warn   { color: %(AMBER)s;   border-color: rgba(245,166,35,0.45);  background: rgba(245,166,35,0.10); }
.chip.ok     { color: %(EMERALD)s; border-color: rgba(45,212,167,0.45);  background: rgba(45,212,167,0.10); }
.chip.info   { color: %(SKY)s;     border-color: rgba(84,182,240,0.45);  background: rgba(84,182,240,0.10); }
.chip.neutral{ color: %(TEXT_DIM)s;border-color: %(BORDER_HI)s;          background: rgba(138,143,153,0.10); }

/* --- Insight callout --------------------------------------------------- */
.callout {
    background: %(BG_CARD)s; border: 1px solid %(BORDER)s;
    border-left: 3px solid %(AMBER)s; border-radius: 6px;
    padding: 14px 18px; color: %(TEXT_DIM)s;
    font-size: 13px; line-height: 1.55; margin: 8px 0 16px 0;
}
.callout strong { color: %(TEXT)s; }

/* --- Nota de metodo (como se obtiene) ---------------------------------- */
.method {
    background: %(BG_ELEV)s; border: 1px solid %(BORDER)s;
    border-radius: 8px; padding: 13px 16px; margin: 6px 0 18px 0;
}
.method .mlabel {
    font-family: 'JetBrains Mono', monospace; color: %(SKY)s;
    font-size: 9.5px; letter-spacing: 0.16em; text-transform: uppercase;
    font-weight: 700; margin-bottom: 5px;
}
.method .mtext { color: %(TEXT_DIM)s; font-size: 12.5px; line-height: 1.55; }
.method .mtext strong { color: %(TEXT)s; }

/* --- Probability dial helper ------------------------------------------- */
.dial {
    background: %(BG_CARD)s; border: 1px solid %(BORDER)s;
    border-radius: 10px; padding: 22px; text-align: center;
}
.dial .label {
    color: %(TEXT_MUTED)s; font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase;
    margin-bottom: 10px; font-weight: 600;
}
.dial .desc { color: %(TEXT_DIM)s; font-size: 12px; margin-top: 10px; }

/* --- Tarjetas de la pagina de inicio ----------------------------------- */
.feat {
    background: %(BG_CARD)s; border: 1px solid %(BORDER)s;
    border-radius: 10px; padding: 18px 20px; height: 100%%;
    box-shadow: %(SHADOW)s;
}
.feat .ftag {
    font-family: 'JetBrains Mono', monospace; color: %(AMBER)s;
    font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase;
    font-weight: 700;
}
.feat h3 {
    font-size: 15px; font-weight: 700; color: %(TEXT)s;
    margin: 6px 0 6px 0;
}
.feat p { color: %(TEXT_DIM)s; font-size: 12.5px; line-height: 1.55; margin: 0; }
.feat .algo {
    display: inline-block; margin-top: 10px;
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    font-weight: 600; color: %(SKY)s;
    border: 1px solid rgba(84,182,240,0.40);
    background: rgba(84,182,240,0.08);
    padding: 3px 9px; border-radius: 999px;
}

/* --- Scrollbar (webkit) ------------------------------------------------ */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: %(BG)s; }
::-webkit-scrollbar-thumb { background: %(BG_ELEV)s; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: %(BORDER_HI)s; }
</style>
"""


def _tokens() -> dict:
    return dict(
        BG=BG, BG_CARD=BG_CARD, BG_ELEV=BG_ELEV,
        BORDER=BORDER, BORDER_HI=BORDER_HI,
        TEXT=TEXT, TEXT_DIM=TEXT_DIM, TEXT_MUTED=TEXT_MUTED,
        GLOW=GLOW, BTN_TEXT=BTN_TEXT, SHADOW=SHADOW,
        AMBER=AMBER, EMERALD=EMERALD, ROSE=ROSE, SKY=SKY,
    )


def css() -> str:
    """CSS global del tema, construido con los tokens del modo activo."""
    return _CSS_TEMPLATE % _tokens()


# --- Helpers de componentes -------------------------------------------------

def hero(eyebrow: str, title: str, subtitle: str) -> str:
    return compact(
        f'<div class="hero">'
        f'<div class="eyebrow">{eyebrow}</div>'
        f'<h1>{title}</h1>'
        f'<div class="subtitle">{subtitle}</div>'
        f'</div>'
    )


def section(title: str, badge: str = "", meta: str = "") -> str:
    badge_html = f'<span class="badge">{badge}</span>' if badge else ''
    meta_html  = f'<span class="meta">{meta}</span>' if meta else ''
    return compact(
        f'<div class="section">{badge_html}<h2>{title}</h2>{meta_html}</div>'
    )


def kpi_card(label: str, value: str, unit: str = "",
             delta: str = "", delta_dir: str = "neutral",
             hint: str = "") -> str:
    """Renderiza una tarjeta KPI (string HTML).

    ``hint`` agrega una linea de explicacion breve debajo del valor.
    """
    delta_html = ""
    if delta:
        sym = {"up": "+", "down": "-", "neutral": ""}.get(delta_dir, "")
        delta_html = f'<div class="delta {delta_dir}">{sym}{delta}</div>'
    unit_html = f'<span class="unit">{unit}</span>' if unit else ''
    hint_html = f'<div class="hint">{hint}</div>' if hint else ''
    return compact(
        f'<div class="kpi">'
        f'<div class="accent"></div>'
        f'<div class="label">{label}</div>'
        f'<div class="value">{value}{unit_html}</div>'
        f'{delta_html}{hint_html}'
        f'</div>'
    )


def kpi_grid(*cards: str) -> str:
    return compact(f'<div class="kpi-grid">{"".join(cards)}</div>')


def chip(text: str, kind: str = "neutral") -> str:
    return f'<span class="chip {kind}">{text}</span>'


def callout(text: str) -> str:
    return compact(f'<div class="callout">{text}</div>')


def method_note(text: str, label: str = "Cómo se obtiene") -> str:
    """Caja breve que explica de dónde sale un resultado (lenguaje ejecutivo)."""
    return compact(
        f'<div class="method">'
        f'<div class="mlabel">{label}</div>'
        f'<div class="mtext">{text}</div>'
        f'</div>'
    )
