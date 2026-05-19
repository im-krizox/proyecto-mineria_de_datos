"""Vista 4 — Segmentación de sellers (K-Means)."""
import pandas as pd
import streamlit as st

from .. import charts as C
from .. import data as D
from .. import theme as T


CLUSTER_COLORS = {
    "Vendedores grandes y confiables": T.AMBER,
    "Vendedores medianos regionales":  T.SKY,
    "Vendedores pequeños en riesgo":   T.ROSE,
}


def render():
    clu = D.load_clusters()
    perf = D.load_perfil_clusters()

    st.markdown(T.section("Tipos de vendedores en la plataforma",
                           badge="Sección 04",
                           meta=f"{len(clu):,} vendedores · 3 grupos"),
                 unsafe_allow_html=True)

    st.markdown(T.callout(
        f"Los <strong>{len(clu):,} vendedores</strong> de la plataforma se "
        "acomodan en tres grupos naturales, según cuánto venden, qué tan "
        "caros son sus productos, qué tan bien entregan, qué tan contentos "
        "quedan sus clientes y a cuántos estados llegan. A cada grupo le "
        "conviene una estrategia diferente para mantener inventario."
    ), unsafe_allow_html=True)

    st.markdown(T.method_note(
        "Los grupos se forman con <strong>K-Means</strong>, un algoritmo de "
        "agrupamiento: compara a los vendedores entre sí y los junta por "
        "<strong>parecido</strong> en su comportamiento, sin que nadie defina "
        "las categorías de antemano. Los nombres de cada grupo y su estrategia "
        "se asignan después, interpretando el perfil que resultó. Sirve para "
        "tratar a cada tipo de vendedor con la política de inventario que le "
        "corresponde.",
        label="Cómo se obtienen estos grupos",
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
            kind = ("ok" if "grandes" in label
                     else "info" if "medianos" in label else "alert")
            card = T.compact(
                f'<div class="kpi" style="border-left:3px solid {color};">'
                f'<div class="label">Grupo {row["cluster"] + 1} · {row["n_sellers"]:,} vendedores</div>'
                f'<div class="value" style="font-size:18px; line-height:1.3;">{label}</div>'
                f'<div style="{metrics_style}">'
                f'<div>Pedidos en promedio: <strong style="color:{T.TEXT};">{row["n_pedidos"]:.0f}</strong></div>'
                f'<div>Ingresos en promedio: <strong style="color:{T.TEXT};">R$ {row["ingresos_totales"]:,.0f}</strong></div>'
                f'<div>Entregas con retraso: <strong style="color:{T.TEXT};">{row["tasa_retraso"]*100:.2f}%</strong></div>'
                f'<div>Calificación: <strong style="color:{T.TEXT};">{row["review_promedio"]:.2f}</strong> / 5</div>'
                f'<div>Llega a: <strong style="color:{T.TEXT};">{row["n_estados_clientes"]:.0f}</strong> estados</div>'
                f'</div>'
                f'<div style="margin-top:10px;">{T.chip("Recomendación", kind)}</div>'
                f'<div style="color:{T.TEXT_DIM}; font-size:12.5px; margin-top:6px;'
                f' line-height:1.45;">{row["estrategia_reabastecimiento"]}</div>'
                f'</div>'
            )
            st.markdown(card, unsafe_allow_html=True)

    # ---- Scatter -----------------------------------------------------
    st.markdown(T.section("Mapa de vendedores: retraso vs ingresos",
                           badge="Visualización",
                           meta="cada círculo es un vendedor · tamaño = pedidos"),
                 unsafe_allow_html=True)
    palette = [CLUSTER_COLORS.get(label, T.SLATE)
                for label in sorted(clu["etiqueta"].unique())]
    st.plotly_chart(C.scatter_sellers(clu, palette),
                     use_container_width=True, theme=None)

    # ---- Tabla buscable ----------------------------------------------
    st.markdown(T.section("Buscar vendedores",
                           badge="Detalle",
                           meta="usa los filtros para acotar"),
                 unsafe_allow_html=True)
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        cluster_sel = st.multiselect(
            "Grupo", options=clu["etiqueta"].unique().tolist(),
            default=clu["etiqueta"].unique().tolist(),
        )
    with f2:
        min_ped = st.number_input("Mínimo de pedidos", min_value=0, value=0, step=10)
    with f3:
        busqueda = st.text_input("Buscar vendedor (primeros caracteres del ID)", "")

    flt = clu[clu["etiqueta"].isin(cluster_sel) & (clu["n_pedidos"] >= min_ped)]
    if busqueda:
        flt = flt[flt["seller_id"].str.startswith(busqueda)]

    show_cols = ["seller_id", "etiqueta", "n_pedidos", "ingresos_totales",
                 "ticket_promedio", "tasa_retraso", "review_promedio",
                 "n_estados_clientes", "estrategia_reabastecimiento"]
    tabla = flt[show_cols].copy()
    tabla["tasa_retraso"] = tabla["tasa_retraso"] * 100
    tabla = tabla.rename(columns={
        "seller_id":            "Vendedor",
        "etiqueta":             "Grupo",
        "n_pedidos":            "Pedidos",
        "ingresos_totales":     "Ingresos (R$)",
        "ticket_promedio":      "Precio promedio",
        "tasa_retraso":         "% con retraso",
        "review_promedio":      "Calificación",
        "n_estados_clientes":   "Estados a los que llega",
        "estrategia_reabastecimiento": "Recomendación",
    })
    st.dataframe(
        tabla.sort_values("Ingresos (R$)", ascending=False),
        use_container_width=True, hide_index=True, height=400,
        column_config={
            "% con retraso":   st.column_config.NumberColumn(format="%.2f"),
            "Calificación":    st.column_config.NumberColumn(format="%.2f"),
            "Ingresos (R$)":   st.column_config.NumberColumn(format="%.0f"),
            "Precio promedio": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    st.caption(f"Mostrando {len(flt):,} de {len(clu):,} vendedores después de aplicar filtros.")
