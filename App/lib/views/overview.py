"""Vista 1 — Visión general / KPIs ejecutivos."""
import streamlit as st

from .. import charts as C
from .. import data as D
from .. import theme as T


def fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def fmt_money(v: float) -> str:
    if v >= 1e9:
        return f"R$ {v/1e9:.2f}"
    if v >= 1e6:
        return f"R$ {v/1e6:.2f}"
    if v >= 1e3:
        return f"R$ {v/1e3:.1f}"
    return f"R$ {v:.0f}"


def render():
    k = D.kpi_globales()

    # ---- KPI grid -----------------------------------------------------
    money_unit = "B" if k["gmv"] >= 1e9 else ("M" if k["gmv"] >= 1e6 else "K")
    st.markdown(T.kpi_grid(
        T.kpi_card("Pedidos totales",   fmt_int(k["n_pedidos"]),
                    delta=f'{k["rango_fechas"][0].year}-{k["rango_fechas"][1].year}',
                    delta_dir="neutral"),
        T.kpi_card("Ítems vendidos",    fmt_int(k["n_items"])),
        T.kpi_card("GMV (price+freight)", fmt_money(k["gmv"]), unit=money_unit),
        T.kpi_card("Sellers activos",   fmt_int(k["n_sellers"])),
        T.kpi_card("Productos únicos",  fmt_int(k["n_productos"])),
        T.kpi_card("Tasa de retraso",
                    f'{k["tasa_retraso"]*100:.2f}',
                    unit="%",
                    delta=f'Items {k["tasa_retraso_items"]*100:.2f}%',
                    delta_dir="neutral"),
    ), unsafe_allow_html=True)

    st.markdown(T.callout(
        "El indicador clave del negocio es la <strong>tasa de retraso</strong>: "
        "6.57% global. Las vistas siguientes desglosan dónde ocurren los retrasos, "
        "qué sellers son críticos y qué se espera para los próximos 14 días."
    ), unsafe_allow_html=True)

    # ---- Tendencia mensual -------------------------------------------
    st.markdown(T.section("Volumen y tasa de retraso por mes",
                           badge="Serie 01",
                           meta="fuente: tad_pedidos"),
                 unsafe_allow_html=True)
    st.plotly_chart(C.line_tendencia_mensual(D.retraso_por_mes()),
                     use_container_width=True, theme=None)

    # ---- Top categorías + Estados -------------------------------------
    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown(T.section("Top categorías por ingresos",
                               badge="Serie 02",
                               meta="fuente: tad_ventas"),
                     unsafe_allow_html=True)
        st.plotly_chart(C.bar_categorias(D.top_categorias(10), "ingresos"),
                         use_container_width=True, theme=None)
    with c2:
        st.markdown(T.section("Top estados por tasa de retraso",
                               badge="Serie 03",
                               meta="customer_state"),
                     unsafe_allow_html=True)
        st.plotly_chart(C.bar_estado_retraso(D.retraso_por_estado(), top_n=12),
                         use_container_width=True, theme=None)
