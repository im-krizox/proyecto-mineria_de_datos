"""Vista 3 — Pronóstico de demanda y alertas tempranas."""
import pandas as pd
import streamlit as st

from .. import charts as C
from .. import data as D
from .. import theme as T


CATEGORIAS = ["bed_bath_table", "health_beauty", "sports_leisure",
              "furniture_decor", "computers_accessories"]


def render():
    series = D.load_series_diaria()
    alertas = D.load_alertas()
    metricas = D.load_metricas_series()

    # ---- Selector de categoría ----------------------------------------
    st.markdown(T.section("Pronóstico de ventas y avisos tempranos",
                           badge="Próximos días",
                           meta="14 días hacia adelante · 5 categorías principales"),
                 unsafe_allow_html=True)

    c1, c2 = st.columns([1, 3])
    with c1:
        categoria = st.selectbox(
            "Categoría",
            options=CATEGORIAS,
            format_func=lambda s: s.replace("_", " ").title(),
        )
    with c2:
        st.write("")  # spacer
        m = metricas[metricas["categoria"] == categoria]
        if not m.empty:
            naive = m[m["modelo"].str.contains("Naïve|Naive", regex=True)]
            sarima = m[m["modelo"].str.contains("SARIMA")]
            chips = []
            if not sarima.empty:
                chips.append(T.chip(f"Error del pronóstico inteligente: {sarima['sMAPE_%'].iloc[0]:.2f}%", "info"))
            if not naive.empty:
                chips.append(T.chip(f"Error del método simple: {naive['sMAPE_%'].iloc[0]:.2f}%", "neutral"))
            if not sarima.empty and not naive.empty:
                d = naive['sMAPE_%'].iloc[0] - sarima['sMAPE_%'].iloc[0]
                chips.append(T.chip(
                    f"Mejora: {d:+.2f} puntos", "ok" if d > 0 else "warn"))
            st.markdown(" ".join(chips), unsafe_allow_html=True)

    # ---- KPIs de alertas de la categoría --------------------------------
    al_cat = alertas[alertas["categoria"] == categoria].copy()
    n_stockout = int((al_cat["tipo"] == "STOCKOUT").sum())
    n_sobre    = int((al_cat["tipo"] == "SOBRE-STOCK").sum())
    n_ok       = int((al_cat["tipo"] == "OK").sum())
    n_total    = len(al_cat)

    st.markdown(T.kpi_grid(
        T.kpi_card("Días en riesgo de quedarse sin stock", str(n_stockout),
                    delta="hay que reabastecer", delta_dir="down"),
        T.kpi_card("Días con riesgo de inventario de más", str(n_sobre),
                    delta="conviene promocionar", delta_dir="neutral"),
        T.kpi_card("Días dentro de lo normal", str(n_ok),
                    delta="todo bajo control", delta_dir="up"),
        T.kpi_card("Días analizados en total", str(n_total)),
    ), unsafe_allow_html=True)

    # ---- Gráfica principal --------------------------------------------
    hist = pd.DataFrame({
        "fecha": series["fecha"],
        "demanda": series[categoria],
    })
    st.plotly_chart(
        C.forecast_chart(hist, al_cat, categoria.replace("_", " ").title()),
        use_container_width=True, theme=None,
    )

    # ---- Tabla de alertas accionables ---------------------------------
    st.markdown(T.section("Avisos para tomar acción · próximos 14 días",
                           badge="Operación",
                           meta=f"{n_total} días"),
                 unsafe_allow_html=True)

    if al_cat.empty:
        st.info("No hay avisos para esta categoría.")
    else:
        tabla = al_cat.sort_values("fecha")[
            ["fecha", "tipo", "lim_inf", "lim_sup",
             "p10_hist", "p90_hist", "mensaje"]
        ].rename(columns={
            "fecha":     "Fecha",
            "tipo":      "Tipo de aviso",
            "lim_inf":   "Mínimo esperado",
            "lim_sup":   "Máximo esperado",
            "p10_hist":  "Mínimo histórico",
            "p90_hist":  "Máximo histórico",
            "mensaje":   "Acción recomendada",
        })
        tabla["Fecha"] = tabla["Fecha"].dt.strftime("%Y-%m-%d")
        st.dataframe(
            tabla, use_container_width=True, hide_index=True,
            column_config={
                "Mínimo esperado":  st.column_config.NumberColumn(format="%.1f"),
                "Máximo esperado":  st.column_config.NumberColumn(format="%.1f"),
                "Mínimo histórico": st.column_config.NumberColumn(format="%.1f"),
                "Máximo histórico": st.column_config.NumberColumn(format="%.1f"),
            },
        )

    # ---- Comparativa de modelos ---------------------------------------
    st.markdown(T.section("Qué tan bien predice el sistema en cada categoría",
                           badge="Comparativa",
                           meta="error de los últimos 30 días"),
                 unsafe_allow_html=True)
    piv = (metricas.pivot(index="categoria", columns="modelo", values="sMAPE_%")
                    .reset_index()
                    .rename(columns={"categoria": "Categoría"}))
    piv["Categoría"] = piv["Categoría"].str.replace("_", " ").str.title()
    st.dataframe(piv, use_container_width=True, hide_index=True,
                  column_config={col: st.column_config.NumberColumn(format="%.2f%%")
                                  for col in piv.columns if col != "Categoría"})
