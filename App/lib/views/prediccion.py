"""Vista 2 — Calculadora de probabilidad de retraso (modelo v2)."""
import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st

from .. import charts as C
from .. import data as D
from .. import theme as T


# Nombres legibles para los factores del modelo (columnas técnicas -> negocio).
FEATURE_LABELS = {
    "seller_tasa_retraso_hist": "Historial de retraso del vendedor",
    "delivery_days_estimated":  "Días prometidos de entrega",
    "mes":                      "Mes del año",
    "distancia_km":             "Distancia vendedor – cliente",
    "seller_review_promedio":   "Calificación del vendedor",
    "dias_a_proximo_evento":    "Días para la próxima fecha especial",
    "payment_value":            "Monto del pago",
    "dia":                      "Día del mes",
    "trimestre":                "Trimestre del año",
    "dia_semana_num":           "Día de la semana",
    "payment_installments":     "Número de mensualidades",
    "anio":                     "Año de la compra",
    "num_items":                "Cantidad de productos del pedido",
    "seller_cluster":           "Tipo de vendedor",
    "es_fin_semana":            "Compra en fin de semana",
    "es_evento_retail":         "Compra en día de oferta",
    "es_feriado_nacional":      "Compra en feriado",
    "es_carnaval":              "Compra en Carnaval",
    "en_ventana_pre_evento_7d": "Semana previa a una fecha especial",
}


def _pretty_feature(name: str) -> str:
    """Convierte el nombre técnico de una variable a lenguaje de negocio."""
    if name in FEATURE_LABELS:
        return FEATURE_LABELS[name]
    if name.startswith("customer_state_"):
        return f"Estado del cliente: {name.split('_')[-1]}"
    if name.startswith("geo_state_"):
        return f"Estado de entrega: {name.split('_')[-1]}"
    if name.startswith("payment_type_"):
        return f"Pago con {name.split('_')[-1]}"
    return name.replace("_", " ").capitalize()


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

    # ---- Encabezado + cómo funciona el modelo ------------------------
    st.markdown(T.section("Riesgo de entregas tardías",
                           badge="Sección 02",
                           meta="modelo predictivo entrenado con pedidos reales"),
                 unsafe_allow_html=True)

    st.markdown(T.method_note(
        "Esta sección usa un modelo de <strong>Random Forest</strong> "
        "(bosque aleatorio): combina cientos de árboles de decisión que, para "
        "cada pedido, <strong>votan</strong> si llegará tarde o no; la "
        "proporción de votos es la probabilidad de retraso que verás abajo. "
        "El modelo aprendió de unos <strong>69 000 pedidos históricos</strong> "
        "y se evaluó con otros <strong>30 000 que nunca había visto</strong>, "
        "para confirmar que funciona con pedidos nuevos. Sirve para anticipar "
        "qué envíos conviene vigilar antes de que se retrasen.",
        label="Cómo funciona esta sección",
    ), unsafe_allow_html=True)

    # ---- Bandeja superior con métricas del modelo --------------------
    m = metrics
    st.markdown(T.kpi_grid(
        T.kpi_card("Retrasos que el modelo detecta",
                    f'{m["recall_1"]*100:.0f}', unit="de cada 100",
                    hint="De cada 100 pedidos que de verdad llegan tarde, el "
                         "modelo logra identificar esta cantidad."),
        T.kpi_card("Aciertos al avisar un retraso",
                    f'{m["precision_1"]*100:.0f}', unit="de cada 100",
                    hint="De cada 100 veces que el modelo marca un pedido como "
                         "riesgoso, acierta en esta cantidad."),
        T.kpi_card("Calidad general del modelo",
                    f'{m["f1_1"]:.2f}', unit="de 1.0",
                    delta="versión anterior: 0.23", delta_dir="up",
                    hint="Puntaje de 0 a 1 que equilibra cuántos retrasos "
                         "detecta y cuántas veces acierta. Más alto es mejor."),
        T.kpi_card("Capacidad de distinguir riesgo",
                    f'{m["roc_auc"]:.2f}', unit="de 1.0",
                    delta="versión anterior: 0.72", delta_dir="up",
                    hint="De 0.5 (equivale a adivinar) a 1.0 (perfecto): qué "
                         "tan bien separa los pedidos riesgosos de los seguros."),
    ), unsafe_allow_html=True)

    st.markdown(T.callout(
        "<strong>Calculadora de riesgo de retraso</strong> — define abajo un "
        "pedido y el sistema estima qué tan probable es que llegue tarde. "
        "La línea gris del medidor marca el promedio del negocio "
        "({:.1%} de los pedidos llega tarde); por encima de esa línea, el "
        "pedido es más riesgoso que lo normal.".format(base_rate)
    ), unsafe_allow_html=True)

    # ---- Formulario y resultado --------------------------------------
    st.markdown(T.section("Calcula el riesgo de retraso de un pedido",
                           badge="Versión 2",
                           meta="modelo afinado automáticamente"),
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
                "Tipo de día de la compra",
                options=cat_vals["tipo_evento_compra"],
            )
            seller_cluster_label = st.selectbox(
                "Tipo de vendedor",
                options=["Vendedores grandes y confiables",
                         "Vendedores medianos regionales",
                         "Vendedores pequeños en riesgo"],
            )
        with c2:
            fecha = st.date_input("Fecha de compra",
                                    value=dt.date(2018, 6, 15),
                                    min_value=dt.date(2016, 1, 1),
                                    max_value=dt.date(2018, 12, 31))
            delivery_days_estimated = st.slider(
                "Días prometidos de entrega", 3, 60, 14, 1)
            num_items = st.slider("Cuántos productos lleva el pedido", 1, 12, 1, 1)
            payment_installments = st.slider("Mensualidades del pago", 0, 24, 1, 1)
            payment_value = st.number_input("Monto del pago (R$)",
                                              min_value=10.0, value=120.0, step=5.0)

        c3, c4 = st.columns(2)
        with c3:
            seller_state = st.selectbox(
                "Estado del vendedor",
                options=sorted(coords_sel["seller_state"].dropna().unique().tolist()),
                index=0,
            )
        with c4:
            es_feriado = st.checkbox("Día feriado nacional", False)
            es_carnaval = st.checkbox("Día de Carnaval", False)
            es_evento_retail = st.checkbox("Día de oferta especial (Black Friday, Cyber Monday...)", False)

    # ---- Derivar features ---------------------------------------------
    cli = coords_cli.set_index("customer_state").loc[customer_state]
    sel = coords_sel.set_index("seller_state").loc[seller_state]
    distancia_km = D.haversine_km(cli["geo_lat"], cli["geo_lng"],
                                    sel["seller_geo_lat"], sel["seller_geo_lng"])

    # Estadísticas por cluster derivadas en vivo de 06_seller_agg_clusters.csv
    # (media real sobre los sellers de cada grupo); sin constantes hardcodeadas.
    cstats = D.cluster_stats().set_index("etiqueta")
    cluster_num_map = {lbl: int(cstats.loc[lbl, "cluster"])
                       for lbl in cstats.index}
    cluster_retraso_map = {lbl: float(cstats.loc[lbl, "tasa_retraso"])
                           for lbl in cstats.index}
    cluster_review_map = {lbl: float(cstats.loc[lbl, "review_promedio"])
                          for lbl in cstats.index}

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
            f'<div class="label">Resumen para el negocio</div>'
            f'<div style="display:flex; align-items:center; gap:10px;">'
            f'{T.chip(label, kchip)}'
            f'<span style="font-family:\'JetBrains Mono\'; color:{T.TEXT_DIM};">'
            f'comparado con el promedio = '
            f'<strong style="color:{T.TEXT};">{multiplier:.2f}×</strong>'
            f'</span>'
            f'</div>'
            f'<div class="desc">Distancia entre vendedor y cliente: '
            f'<strong style="color:{T.TEXT};">{distancia_km:.0f} km</strong>.<br/>'
            f'La línea gris del medidor marca el promedio del negocio '
            f'({base_rate:.2%}).'
            f'</div>'
            f'</div>'
        )
        st.markdown(block, unsafe_allow_html=True)

    # ---- Importancias --------------------------------------------------
    st.markdown(T.section("Qué factores pesan más al predecir un retraso",
                           badge="Explicación",
                           meta="los 12 factores más influyentes"),
                 unsafe_allow_html=True)
    st.markdown(T.method_note(
        "El modelo no decide al azar: aprende qué información ayuda a "
        "anticipar un retraso. La barra muestra cuánto pesa cada factor en "
        "esa decisión; entre más larga, más influye. El historial del "
        "vendedor suele ser el factor más determinante.",
        label="Cómo leer esta gráfica",
    ), unsafe_allow_html=True)
    imp = D.load_importancias().copy()
    imp["feature"] = imp["feature"].map(_pretty_feature)
    st.plotly_chart(C.bar_importancias(imp, top=12),
                     use_container_width=True, theme=None)

    # ---- Comparación v1 vs v2 ------------------------------------------
    st.markdown(T.section("Mejora del modelo: versión 1 vs versión 2",
                           badge="Comparativa",
                           meta="probado con datos nuevos"),
                 unsafe_allow_html=True)
    st.markdown(T.method_note(
        "El modelo se construyó en dos etapas. La versión 1 fue un primer "
        "intento más simple; la versión 2 (la que está en uso) añadió el "
        "historial del vendedor, la distancia y el calendario, y casi duplicó "
        "su calidad general. La gráfica compara ambas con datos que no se "
        "usaron para entrenar.",
        label="Por qué hay dos versiones",
    ), unsafe_allow_html=True)
    cmp = D.load_comparacion_v1v2()
    keep = ["Árbol decisión (v1)", "Árbol GridSearch (v1)",
            "Random Forest (baseline)", "Random Forest (GridSearchCV)"]
    st.plotly_chart(C.bar_compare_v1v2(cmp[cmp["modelo"].isin(keep)]),
                     use_container_width=True, theme=None)
