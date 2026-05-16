"""Vista 2 — Calculadora de probabilidad de retraso (modelo v2)."""
import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st

from .. import charts as C
from .. import data as D
from .. import theme as T


def _build_row(schema, form: dict) -> pd.DataFrame:
    """Convierte un dict de inputs en una fila compatible con el pipeline."""
    base = {c: 0 for c in schema["num_features"]}
    base.update({c: "" for c in schema["cat_features"]})
    base.update(form)
    return pd.DataFrame([base])


def render():
    pipeline, schema = D.load_model()
    base_rate = schema["base_rate"]
    metrics = schema["metrics_test"]
    cat_vals = schema["cat_values"]
    coords_cli = D.coords_por_estado()
    coords_sel = D.coords_seller_por_estado()
    perfil = D.load_perfil_clusters()

    # ---- Bandeja superior con métricas del modelo --------------------
    st.markdown(T.kpi_grid(
        T.kpi_card("F1 (clase tarde)",  f'{metrics["f1_1"]:.3f}',
                    delta=f'v1: 0.230 → +{(metrics["f1_1"]-0.23)/0.23*100:.0f}%',
                    delta_dir="up"),
        T.kpi_card("Precision₁", f'{metrics["precision_1"]:.3f}',
                    delta="vs 0.150 (v1)", delta_dir="up"),
        T.kpi_card("Recall₁", f'{metrics["recall_1"]:.3f}',
                    delta="vs 0.600 (v1)", delta_dir="down"),
        T.kpi_card("ROC-AUC", f'{metrics["roc_auc"]:.3f}',
                    delta="vs 0.720 (v1)", delta_dir="up"),
        T.kpi_card("PR-AUC", f'{metrics["pr_auc"]:.3f}',
                    delta="vs 0.170 (v1)", delta_dir="up"),
    ), unsafe_allow_html=True)

    st.markdown(T.callout(
        "<strong>Random Forest tuneado v2</strong> — calculadora de probabilidad "
        "de retraso para un pedido hipotético. La línea de referencia gris en el "
        "gauge indica la tasa base global ({:.2%}).".format(base_rate)
    ), unsafe_allow_html=True)

    # ---- Formulario y resultado --------------------------------------
    st.markdown(T.section("Calculadora de retraso por pedido",
                           badge="Modelo v2",
                           meta="Random Forest · GridSearchCV"),
                 unsafe_allow_html=True)

    form_col, result_col = st.columns([1.3, 1])

    with form_col:
        c1, c2 = st.columns(2)
        with c1:
            customer_state = st.selectbox(
                "Estado del cliente",
                options=cat_vals["customer_state"],
                index=cat_vals["customer_state"].index("SP")
                       if "SP" in cat_vals["customer_state"] else 0,
            )
            payment_type = st.selectbox(
                "Tipo de pago",
                options=cat_vals["payment_type"],
                index=cat_vals["payment_type"].index("credit_card")
                       if "credit_card" in cat_vals["payment_type"] else 0,
            )
            tipo_evento_compra = st.selectbox(
                "Tipo de evento de la compra",
                options=cat_vals["tipo_evento_compra"],
            )
            seller_cluster_label = st.selectbox(
                "Cluster del seller",
                options=["Power-seller confiable", "Mediano regional",
                         "Cola larga inestable"],
            )
        with c2:
            fecha = st.date_input("Fecha de compra",
                                    value=dt.date(2018, 6, 15),
                                    min_value=dt.date(2016, 1, 1),
                                    max_value=dt.date(2018, 12, 31))
            delivery_days_estimated = st.slider(
                "Días estimados de entrega", 3, 60, 14, 1)
            num_items = st.slider("# Items en el pedido", 1, 12, 1, 1)
            payment_installments = st.slider("Cuotas (installments)", 0, 24, 1, 1)
            payment_value = st.number_input("Valor del pago (R$)",
                                              min_value=10.0, value=120.0, step=5.0)

        c3, c4 = st.columns(2)
        with c3:
            seller_state = st.selectbox(
                "Estado del seller",
                options=sorted(coords_sel["seller_state"].dropna().unique().tolist()),
                index=0,
            )
        with c4:
            es_feriado = st.checkbox("Día feriado nacional", False)
            es_carnaval = st.checkbox("Día de Carnaval", False)
            es_evento_retail = st.checkbox("Día de evento retail (BF, CM, ...)", False)

    # ---- Derivar features ---------------------------------------------
    cli = coords_cli.set_index("customer_state").loc[customer_state]
    sel = coords_sel.set_index("seller_state").loc[seller_state]
    distancia_km = D.haversine_km(cli["geo_lat"], cli["geo_lng"],
                                    sel["seller_geo_lat"], sel["seller_geo_lng"])

    cluster_num_map = {"Power-seller confiable": 1, "Mediano regional": 0,
                        "Cola larga inestable": 2}
    cluster_retraso_map = {"Power-seller confiable": 0.0669,
                            "Mediano regional": 0.0381,
                            "Cola larga inestable": 0.1699}
    cluster_review_map = {"Power-seller confiable": 4.09,
                           "Mediano regional": 4.55,
                           "Cola larga inestable": 2.42}

    es_fin = fecha.weekday() >= 5

    form = {
        "mes": fecha.month, "trimestre": (fecha.month - 1) // 3 + 1,
        "dia": fecha.day, "dia_semana_num": fecha.weekday(), "anio": fecha.year,
        "num_items": num_items, "payment_installments": payment_installments,
        "payment_value": payment_value,
        "delivery_days_estimated": delivery_days_estimated,
        "es_feriado_nacional": int(es_feriado),
        "es_carnaval": int(es_carnaval),
        "es_evento_retail": int(es_evento_retail),
        "es_dia_no_laboral": int(es_feriado or es_carnaval or es_fin),
        "es_fin_semana": int(es_fin),
        "dias_a_proximo_evento": 0 if es_evento_retail else 7,
        "en_ventana_pre_evento_3d": 0, "en_ventana_pre_evento_7d": 0,
        "flag_short_message": 0, "flag_answer_before_creation": 0,
        "flag_review_id_duplicated": 0, "flag_review_id_multi_order": 0,
        "seller_cluster": cluster_num_map[seller_cluster_label],
        "seller_tasa_retraso_hist": cluster_retraso_map[seller_cluster_label],
        "seller_review_promedio": cluster_review_map[seller_cluster_label],
        "distancia_km": distancia_km,
        "customer_state": customer_state, "geo_state": customer_state,
        "payment_type": payment_type, "tipo_evento_compra": tipo_evento_compra,
    }
    row = _build_row(schema, form)

    prob = float(pipeline.predict_proba(row)[0, 1])
    multiplier = prob / base_rate

    # ---- Panel derecho de resultado -----------------------------------
    with result_col:
        kind = "low" if prob < 0.15 else "medium" if prob < 0.30 else "high"
        label = ("Riesgo bajo" if kind == "low"
                  else "Riesgo moderado" if kind == "medium"
                  else "Riesgo alto")

        st.plotly_chart(C.gauge_prob(prob, base_rate),
                         use_container_width=True, theme=None,
                         config={"displayModeBar": False})

        kchip = "ok" if kind == "low" else "warn" if kind == "medium" else "alert"
        block = T.compact(
            f'<div class="dial" style="text-align:left;">'
            f'<div class="label">Lectura ejecutiva</div>'
            f'<div style="display:flex; align-items:center; gap:10px;">'
            f'{T.chip(label, kchip)}'
            f'<span style="font-family:\'JetBrains Mono\'; color:{T.TEXT_DIM};">'
            f'multiplicador vs media = '
            f'<strong style="color:{T.TEXT};">{multiplier:.2f}×</strong>'
            f'</span>'
            f'</div>'
            f'<div class="desc">Distancia estimada seller↔cliente: '
            f'<strong style="color:{T.TEXT};">{distancia_km:.0f} km</strong>.<br/>'
            f'La línea gris en el gauge marca la tasa de retraso global '
            f'({base_rate:.2%}).'
            f'</div>'
            f'</div>'
        )
        st.markdown(block, unsafe_allow_html=True)

    # ---- Importancias --------------------------------------------------
    st.markdown(T.section("Importancia de variables — Random Forest tuneado",
                           badge="Explainability",
                           meta="Top 12"),
                 unsafe_allow_html=True)
    st.plotly_chart(C.bar_importancias(D.load_importancias(), top=12),
                     use_container_width=True, theme=None)

    # ---- Comparación v1 vs v2 ------------------------------------------
    st.markdown(T.section("Comparación de modelos: v1 vs v2",
                           badge="Benchmarks",
                           meta="80/20 estratificado"),
                 unsafe_allow_html=True)
    cmp = D.load_comparacion_v1v2()
    keep = ["Árbol decisión (v1)", "Árbol GridSearch (v1)",
            "Random Forest (baseline)", "Random Forest (GridSearchCV)"]
    st.plotly_chart(C.bar_compare_v1v2(cmp[cmp["modelo"].isin(keep)]),
                     use_container_width=True, theme=None)
