"""Vista 4 — Segmentación de sellers (K-Means)."""
import pandas as pd
import streamlit as st

from .. import charts as C
from .. import data as D
from .. import theme as T


CLUSTER_COLORS = {
    "Power-seller confiable": T.AMBER,
    "Mediano regional":       T.SKY,
    "Cola larga inestable":   T.ROSE,
}


def render():
    clu = D.load_clusters()
    perf = D.load_perfil_clusters()

    st.markdown(T.section("Segmentación operativa de sellers",
                           badge="K-Means · k=3",
                           meta=f"{len(clu):,} sellers"),
                 unsafe_allow_html=True)

    st.markdown(T.callout(
        "Los <strong>3,095 sellers</strong> de Olist se agrupan en tres clusters "
        "operativos según volumen, ticket, servicio, satisfacción y alcance. "
        "Cada cluster recibe una estrategia diferenciada de reabastecimiento."
    ), unsafe_allow_html=True)

    # ---- Tarjetas por cluster ----------------------------------------
    cols = st.columns(3)
    perf_sorted = perf.sort_values("n_sellers", ascending=False)
    metrics_style = (f"margin-top:10px; display:flex; flex-direction:column;"
                      f" gap:4px; font-family:'JetBrains Mono',monospace;"
                      f" font-size:11.5px; color:{T.TEXT_DIM};")
    for i, (_, row) in enumerate(perf_sorted.iterrows()):
        with cols[i]:
            label = row["etiqueta"]
            color = CLUSTER_COLORS.get(label, T.AMBER)
            kind = ("ok" if "Power" in label
                     else "info" if "Mediano" in label else "alert")
            card = T.compact(
                f'<div class="kpi" style="border-left:3px solid {color};">'
                f'<div class="label">Cluster {row["cluster"]} · {row["n_sellers"]:,} sellers</div>'
                f'<div class="value" style="font-size:18px; line-height:1.3;">{label}</div>'
                f'<div style="{metrics_style}">'
                f'<div>Pedidos prom: <strong style="color:{T.TEXT};">{row["n_pedidos"]:.0f}</strong></div>'
                f'<div>Ingresos prom: <strong style="color:{T.TEXT};">R$ {row["ingresos_totales"]:,.0f}</strong></div>'
                f'<div>Tasa retraso: <strong style="color:{T.TEXT};">{row["tasa_retraso"]*100:.2f}%</strong></div>'
                f'<div>Review: <strong style="color:{T.TEXT};">{row["review_promedio"]:.2f}</strong> / 5</div>'
                f'<div>Alcance: <strong style="color:{T.TEXT};">{row["n_estados_clientes"]:.0f}</strong> estados</div>'
                f'</div>'
                f'<div style="margin-top:10px;">{T.chip("Estrategia", kind)}</div>'
                f'<div style="color:{T.TEXT_DIM}; font-size:12.5px; margin-top:6px;'
                f' line-height:1.45;">{row["estrategia_reabastecimiento"]}</div>'
                f'</div>'
            )
            st.markdown(card, unsafe_allow_html=True)

    # ---- Scatter -----------------------------------------------------
    st.markdown(T.section("Distribución de sellers (tasa de retraso × ingresos)",
                           badge="Cluster map",
                           meta="size = # pedidos"),
                 unsafe_allow_html=True)
    palette = [CLUSTER_COLORS.get(label, T.SLATE)
                for label in sorted(clu["etiqueta"].unique())]
    st.plotly_chart(C.scatter_sellers(clu, palette),
                     use_container_width=True, theme=None)

    # ---- Tabla buscable ----------------------------------------------
    st.markdown(T.section("Explorador de sellers",
                           badge="Detail",
                           meta="filtros activos"),
                 unsafe_allow_html=True)
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        cluster_sel = st.multiselect(
            "Cluster", options=clu["etiqueta"].unique().tolist(),
            default=clu["etiqueta"].unique().tolist(),
        )
    with f2:
        min_ped = st.number_input("Pedidos mínimos", min_value=0, value=0, step=10)
    with f3:
        busqueda = st.text_input("Buscar por seller_id (prefijo)", "")

    flt = clu[clu["etiqueta"].isin(cluster_sel) & (clu["n_pedidos"] >= min_ped)]
    if busqueda:
        flt = flt[flt["seller_id"].str.startswith(busqueda)]

    show_cols = ["seller_id", "etiqueta", "n_pedidos", "ingresos_totales",
                 "ticket_promedio", "tasa_retraso", "review_promedio",
                 "n_estados_clientes", "estrategia_reabastecimiento"]
    tabla = flt[show_cols].copy()
    tabla["tasa_retraso"] = tabla["tasa_retraso"] * 100
    tabla = tabla.rename(columns={
        "seller_id":            "Seller",
        "etiqueta":             "Cluster",
        "n_pedidos":            "Pedidos",
        "ingresos_totales":     "Ingresos (R$)",
        "ticket_promedio":      "Ticket prom",
        "tasa_retraso":         "Retraso %",
        "review_promedio":      "Review",
        "n_estados_clientes":   "Alcance",
        "estrategia_reabastecimiento": "Estrategia",
    })
    st.dataframe(
        tabla.sort_values("Ingresos (R$)", ascending=False),
        use_container_width=True, hide_index=True, height=400,
        column_config={
            "Retraso %":      st.column_config.NumberColumn(format="%.2f"),
            "Review":         st.column_config.NumberColumn(format="%.2f"),
            "Ingresos (R$)":  st.column_config.NumberColumn(format="%.0f"),
            "Ticket prom":    st.column_config.NumberColumn(format="%.2f"),
        },
    )
    st.caption(f"{len(flt):,} de {len(clu):,} sellers tras filtros.")
