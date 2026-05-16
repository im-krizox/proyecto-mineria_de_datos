"""Tema visual de la app — terminal financiera oscura con acento ámbar."""
import re


def compact(html: str) -> str:
    """Colapsa whitespace para que el parser markdown no rompa el HTML."""
    return re.sub(r"\s+", " ", html).strip()


# --- Paleta -----------------------------------------------------------------
BG          = "#0b1220"   # fondo principal
BG_CARD     = "#111827"   # cards / paneles
BG_ELEV     = "#1f2937"   # elementos elevados (hover, headers de tabla)
BORDER      = "#1f2937"   # bordes sutiles
BORDER_HI   = "#334155"   # bordes hover

TEXT        = "#e5e7eb"   # texto principal
TEXT_DIM    = "#9ca3af"   # texto secundario
TEXT_MUTED  = "#6b7280"   # texto terciario (captions)

AMBER       = "#f59e0b"   # acento principal
AMBER_DIM   = "#b45309"   # acento atenuado
EMERALD     = "#10b981"   # positivo
ROSE        = "#ef4444"   # negativo / alerta
SKY         = "#38bdf8"   # info / azul frío
VIOLET      = "#a78bfa"   # categórico extra
SLATE       = "#64748b"   # gris neutro

# --- Paletas Plotly ---------------------------------------------------------
CATEGORICAL = [AMBER, SKY, EMERALD, VIOLET, ROSE, SLATE, "#fbbf24", "#22d3ee"]
SEQ_AMBER   = ["#451a03", "#78350f", "#92400e", "#b45309", "#d97706",
               "#f59e0b", "#fbbf24", "#fcd34d", "#fde68a"]
DIVERGING   = ["#10b981", "#34d399", "#a7f3d0", "#fde68a", "#fbbf24",
               "#f59e0b", "#ef4444"]


def plotly_template():
    """Plotly template alineado con la paleta del dashboard."""
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


# --- CSS global -------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: %(TEXT)s;
}

.stApp {
    background:
      radial-gradient(1200px 600px at 5%% -10%%, rgba(245,158,11,0.08), transparent 60%%),
      radial-gradient(900px 500px at 95%% 0%%, rgba(56,189,248,0.05), transparent 60%%),
      %(BG)s;
}

/* --- Top hero ---------------------------------------------------------- */
.hero {
    border-bottom: 1px solid %(BORDER)s;
    padding: 0 0 18px 0;
    margin-bottom: 22px;
    display: flex; flex-direction: column; gap: 4px;
}
.hero .eyebrow {
    color: %(AMBER)s;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 600;
}
.hero h1 {
    font-size: 30px;
    font-weight: 700;
    color: %(TEXT)s;
    margin: 0; line-height: 1.1;
    letter-spacing: -0.01em;
}
.hero .subtitle {
    color: %(TEXT_DIM)s;
    font-size: 14px;
    max-width: 720px;
}

/* --- KPI cards --------------------------------------------------------- */
.kpi-grid {
    display: grid; gap: 16px;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    margin: 8px 0 24px 0;
}
.kpi {
    background: linear-gradient(180deg, %(BG_CARD)s 0%%, rgba(17,24,39,0.6) 100%%);
    border: 1px solid %(BORDER)s;
    border-radius: 10px;
    padding: 18px 20px;
    position: relative;
    transition: border-color 0.2s ease, transform 0.2s ease;
}
.kpi:hover { border-color: %(BORDER_HI)s; transform: translateY(-1px); }
.kpi .label {
    color: %(TEXT_MUTED)s;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 8px;
}
.kpi .value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 28px;
    font-weight: 600;
    color: %(TEXT)s;
    letter-spacing: -0.01em;
    line-height: 1;
}
.kpi .unit {
    font-family: 'Inter', sans-serif;
    color: %(TEXT_DIM)s; font-size: 14px; font-weight: 500;
    margin-left: 4px;
}
.kpi .delta { font-size: 12px; margin-top: 6px; font-family: 'JetBrains Mono', monospace; }
.kpi .delta.up { color: %(EMERALD)s; }
.kpi .delta.down { color: %(ROSE)s; }
.kpi .delta.neutral { color: %(TEXT_DIM)s; }
.kpi .accent {
    position: absolute; left: 0; top: 18px; bottom: 18px;
    width: 3px; background: %(AMBER)s; border-radius: 0 2px 2px 0;
}

/* --- Section heading --------------------------------------------------- */
.section {
    display: flex; align-items: baseline; gap: 12px;
    margin: 28px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid %(BORDER)s;
}
.section h2 {
    font-size: 18px; font-weight: 600; color: %(TEXT)s;
    margin: 0; letter-spacing: -0.01em;
}
.section .badge {
    font-family: 'JetBrains Mono', monospace;
    color: %(AMBER)s;
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.18em; text-transform: uppercase;
}
.section .meta {
    margin-left: auto; color: %(TEXT_MUTED)s;
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
}

/* --- Tabs -------------------------------------------------------------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; border-bottom: 1px solid %(BORDER)s;
    margin-bottom: 14px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: %(TEXT_DIM)s;
    border: none;
    border-radius: 6px 6px 0 0;
    padding: 10px 18px;
    font-weight: 500; font-size: 13px;
    transition: all 0.18s ease;
}
.stTabs [data-baseweb="tab"]:hover { color: %(TEXT)s; background: rgba(245,158,11,0.05); }
.stTabs [aria-selected="true"] {
    color: %(AMBER)s !important;
    border-bottom: 2px solid %(AMBER)s !important;
    background: rgba(245,158,11,0.08) !important;
}

/* --- Buttons ----------------------------------------------------------- */
.stButton > button {
    background: %(AMBER)s; color: #1a1300; border: none;
    font-weight: 600; font-size: 13px;
    padding: 8px 18px; border-radius: 6px;
    letter-spacing: 0.02em;
    transition: background 0.15s ease;
}
.stButton > button:hover {
    background: #fbbf24; color: #1a1300;
}
.stButton > button:focus { box-shadow: none; outline: 1px solid %(AMBER)s; }

/* --- Inputs ------------------------------------------------------------ */
.stSelectbox label, .stSlider label, .stNumberInput label,
.stCheckbox label, .stRadio label, .stTextInput label, .stDateInput label {
    color: %(TEXT_DIM)s !important;
    font-size: 11px !important; font-weight: 500 !important;
    letter-spacing: 0.06em; text-transform: uppercase;
}
.stSelectbox div[data-baseweb="select"] > div {
    background: %(BG_CARD)s !important;
    border-color: %(BORDER)s !important;
    color: %(TEXT)s !important;
}

/* --- Dataframes -------------------------------------------------------- */
[data-testid="stDataFrame"] {
    border: 1px solid %(BORDER)s; border-radius: 8px;
    background: %(BG_CARD)s;
}

/* --- Metrics native (for places where we use st.metric) ---------------- */
[data-testid="stMetric"] {
    background: %(BG_CARD)s;
    border: 1px solid %(BORDER)s;
    border-radius: 10px;
    padding: 14px 16px;
}
[data-testid="stMetricLabel"] {
    color: %(TEXT_MUTED)s !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important; letter-spacing: 0.16em;
    text-transform: uppercase; font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    color: %(TEXT)s !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
}

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

/* --- Alert chips ------------------------------------------------------- */
.chip {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 10px; border-radius: 999px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase;
    border: 1px solid;
}
.chip.alert  { color: %(ROSE)s;    border-color: rgba(239,68,68,0.4);   background: rgba(239,68,68,0.08); }
.chip.warn   { color: %(AMBER)s;   border-color: rgba(245,158,11,0.4);  background: rgba(245,158,11,0.08); }
.chip.ok     { color: %(EMERALD)s; border-color: rgba(16,185,129,0.4);  background: rgba(16,185,129,0.08); }
.chip.info   { color: %(SKY)s;     border-color: rgba(56,189,248,0.4);  background: rgba(56,189,248,0.08); }
.chip.neutral{ color: %(TEXT_DIM)s;border-color: %(BORDER_HI)s;         background: rgba(148,163,184,0.06); }

/* --- Insight callout --------------------------------------------------- */
.callout {
    background: %(BG_CARD)s;
    border: 1px solid %(BORDER)s;
    border-left: 3px solid %(AMBER)s;
    border-radius: 6px; padding: 14px 18px;
    color: %(TEXT_DIM)s; font-size: 13px; line-height: 1.55;
    margin: 8px 0 16px 0;
}
.callout strong { color: %(TEXT)s; }

/* --- Probability dial helper ------------------------------------------- */
.dial {
    background: %(BG_CARD)s; border: 1px solid %(BORDER)s;
    border-radius: 10px; padding: 22px;
    text-align: center;
}
.dial .label {
    color: %(TEXT_MUTED)s; font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase;
    margin-bottom: 10px; font-weight: 600;
}
.dial .value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 46px; font-weight: 700; letter-spacing: -0.02em;
    line-height: 1;
}
.dial .value.low    { color: %(EMERALD)s; }
.dial .value.medium { color: %(AMBER)s; }
.dial .value.high   { color: %(ROSE)s; }
.dial .desc { color: %(TEXT_DIM)s; font-size: 12px; margin-top: 10px; }

/* --- Tighten default padding ------------------------------------------- */
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1400px; }
header[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }

/* --- Scrollbar (webkit) ------------------------------------------------ */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: %(BG)s; }
::-webkit-scrollbar-thumb { background: %(BG_ELEV)s; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: %(BORDER_HI)s; }
</style>
""" % dict(
    BG=BG, BG_CARD=BG_CARD, BG_ELEV=BG_ELEV,
    BORDER=BORDER, BORDER_HI=BORDER_HI,
    TEXT=TEXT, TEXT_DIM=TEXT_DIM, TEXT_MUTED=TEXT_MUTED,
    AMBER=AMBER, EMERALD=EMERALD, ROSE=ROSE, SKY=SKY,
)


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
             delta: str = "", delta_dir: str = "neutral") -> str:
    """Renderiza una tarjeta KPI (string HTML)."""
    delta_html = ""
    if delta:
        sym = {"up": "+", "down": "-", "neutral": ""}.get(delta_dir, "")
        delta_html = f'<div class="delta {delta_dir}">{sym}{delta}</div>'
    unit_html = f'<span class="unit">{unit}</span>' if unit else ''
    return compact(
        f'<div class="kpi">'
        f'<div class="accent"></div>'
        f'<div class="label">{label}</div>'
        f'<div class="value">{value}{unit_html}</div>'
        f'{delta_html}'
        f'</div>'
    )


def kpi_grid(*cards: str) -> str:
    return compact(f'<div class="kpi-grid">{"".join(cards)}</div>')


def chip(text: str, kind: str = "neutral") -> str:
    return f'<span class="chip {kind}">{text}</span>'


def callout(text: str) -> str:
    return compact(f'<div class="callout">{text}</div>')
