"""Vista 5 — Calidad de datos y enriquecimiento."""
import streamlit as st

from .. import data as D
from .. import theme as T


def render():
    cal = D.load_calendario()
    ped = D.load_pedidos()
    ven = D.load_ventas_min()

    st.markdown(T.section("Trazabilidad de calidad y enriquecimiento",
                           badge="Data quality",
                           meta="Notebooks 01 · 02 · 03 · 04"),
                 unsafe_allow_html=True)

    st.markdown(T.callout(
        "Resumen de las decisiones de limpieza, validación del cubo, "
        "bug-fix de traducción de categorías y enriquecimiento exógeno con "
        "el calendario brasileño. Cada bloque enlaza con su notebook fuente."
    ), unsafe_allow_html=True)

    # ---- Resumen de limpieza ------------------------------------------
    st.markdown(T.kpi_grid(
        T.kpi_card("Tablas Olist limpiadas", "9",
                    delta="01_limpieza_datos_olist", delta_dir="neutral"),
        T.kpi_card("Duplicados eliminados (geo)", "261 831",
                    delta="98.1% reducción", delta_dir="up"),
        T.kpi_card("Filas geo válidas", "19 010",
                    delta="lat/lng dentro de BR", delta_dir="neutral"),
        T.kpi_card("Erratas categorías corregidas", "5",
                    delta="ortografía EN", delta_dir="neutral"),
    ), unsafe_allow_html=True)

    # ---- Validaciones del cubo ----------------------------------------
    st.markdown(T.section("Validaciones del Data Warehouse",
                           badge="ETL · cubo",
                           meta="02_etl_data_warehouse"),
                 unsafe_allow_html=True)

    validations = [
        ("Llaves únicas en todas las dimensiones", "100 %", "ok"),
        ("Integridad customer_id → dim_cliente", "100 %", "ok"),
        ("Integridad product_id → dim_producto", "100 %", "ok"),
        ("Integridad seller_id → dim_vendedor", "100 %", "ok"),
        ("Integridad fecha_key → dim_tiempo", "100 %", "ok"),
        ("Integridad pago_key → dim_pago (sentinela SIN_PAGO)", "100 %", "ok"),
        ("Suma price items vs fact_ventas", "R$ 13.59 M = R$ 13.59 M", "ok"),
        ("Suma freight_value items vs fact_ventas", "R$ 2.25 M = R$ 2.25 M", "ok"),
        ("Suma payment_value (pedidos con items)", "R$ 15.85 M = R$ 15.85 M", "ok"),
    ]
    cols = st.columns(3)
    for i, (name, val, kind) in enumerate(validations):
        with cols[i % 3]:
            card = T.compact(
                f'<div class="kpi" style="padding:14px 16px; margin-bottom:10px;">'
                f'<div class="label">{name}</div>'
                f'<div style="display:flex; align-items:center; gap:8px;">'
                f'<span class="value" style="font-size:14px;">{val}</span>'
                f'{T.chip("OK", kind)}'
                f'</div>'
                f'</div>'
            )
            st.markdown(card, unsafe_allow_html=True)

    # ---- Bug fix de traducción ----------------------------------------
    st.markdown(T.section("Bug-fix · product_category_name_english",
                           badge="Notebook 03",
                           meta="04_correccion_traduccion"),
                 unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    desc_style = (f"color:{T.TEXT_DIM}; font-size:12.5px; margin-top:8px;"
                   f" line-height:1.45;")
    with c1:
        st.markdown(T.compact(
            f'<div class="kpi" style="border-left:3px solid {T.ROSE};">'
            f'<div class="label">Antes del fix</div>'
            f'<div class="value" style="font-size:22px; color:{T.ROSE};">100 % nulos</div>'
            f'<div style="{desc_style}">'
            f'El merge se hacía contra <code>Esporte Lazer</code> (Title Case, '
            f'post-limpieza) mientras la tabla de traducción conserva '
            f'<code>esporte_lazer</code> (snake_case). 0 matches en 112,650 filas.'
            f'</div></div>'
        ), unsafe_allow_html=True)
    with c2:
        st.markdown(T.compact(
            f'<div class="kpi" style="border-left:3px solid {T.EMERALD};">'
            f'<div class="label">Después del fix</div>'
            f'<div class="value" style="font-size:22px; color:{T.EMERALD};">100 % cobertura</div>'
            f'<div style="{desc_style}">'
            f'Diccionario canónico de <strong style="color:{T.TEXT};">74 entradas</strong> '
            f'(71 oficiales + casa_conforto_2 + eletrodomesticos_2 + sin_categoria). '
            f'Conversión Title Case → snake_case en el join.'
            f'</div></div>'
        ), unsafe_allow_html=True)

    # ---- Enriquecimiento exógeno (calendario) -------------------------
    st.markdown(T.section("Enriquecimiento exógeno · Calendario BR",
                           badge="Notebook 04",
                           meta="holidays + Carnaval + retail"),
                 unsafe_allow_html=True)

    n_feriado    = int(cal["es_feriado_nacional"].sum())
    n_carnaval   = int(cal["es_carnaval"].sum())
    n_retail     = int(cal["es_evento_retail"].sum())
    n_no_laboral = int(cal["es_dia_no_laboral"].sum())

    st.markdown(T.kpi_grid(
        T.kpi_card("Días en el calendario", f"{len(cal):,}",
                    delta="2016-01-01 → 2018-12-31", delta_dir="neutral"),
        T.kpi_card("Feriados nacionales", str(n_feriado)),
        T.kpi_card("Días de Carnaval", str(n_carnaval)),
        T.kpi_card("Eventos retail (BF, CM, ...)", str(n_retail)),
    ), unsafe_allow_html=True)

    # Tasa de retraso por cohorte exógena (sanity)
    if "es_evento_retail" in ped.columns:
        cohortes = []
        media = ped["is_late_delivery"].mean()
        cohortes.append(("Media global",     media,                                            "neutral"))
        cohortes.append(("Feriado nacional", ped.loc[ped["es_feriado_nacional"] == 1, "is_late_delivery"].mean(), "warn"))
        cohortes.append(("Carnaval",         ped.loc[ped["es_carnaval"] == 1, "is_late_delivery"].mean(),         "warn"))
        cohortes.append(("Evento retail",    ped.loc[ped["es_evento_retail"] == 1, "is_late_delivery"].mean(),    "alert"))
        cohortes.append(("Fin de semana",    ped.loc[ped["es_fin_semana"] == 1, "is_late_delivery"].mean(),       "neutral"))

        st.markdown(T.section("Discriminatividad de las banderas exógenas",
                               badge="Validación",
                               meta="tasa de retraso por cohorte"),
                     unsafe_allow_html=True)
        cols = st.columns(len(cohortes))
        for i, (name, rate, kind) in enumerate(cohortes):
            with cols[i]:
                pct = rate * 100
                ratio = rate / media if media else 1
                arrow = "neutral"
                if ratio > 1.1: arrow = "down"
                elif ratio < 0.9: arrow = "up"
                st.markdown(T.compact(
                    f'<div class="kpi">'
                    f'<div class="label">{name}</div>'
                    f'<div class="value">{pct:.2f}<span class="unit">%</span></div>'
                    f'<div class="delta {arrow}">×{ratio:.2f} vs media</div>'
                    f'</div>'
                ), unsafe_allow_html=True)

    # ---- Banderas de calidad de reviews -------------------------------
    st.markdown(T.section("Banderas de calidad de reviews",
                           badge="Notebook 01",
                           meta="conservadas como atributos"),
                 unsafe_allow_html=True)
    flags = [
        ("flag_short_message",           int(ped["flag_short_message"].sum()),
         "Mensajes de 1–3 caracteres (probable ruido)"),
        ("flag_answer_before_creation",  int(ped["flag_answer_before_creation"].sum()),
         "Respuesta del seller antes de la creación del review (errata)"),
        ("flag_review_id_duplicated",    int(ped["flag_review_id_duplicated"].sum()),
         "review_id duplicado entre pedidos"),
        ("flag_review_id_multi_order",   int(ped["flag_review_id_multi_order"].sum()),
         "review_id asociado a múltiples pedidos"),
    ]
    cols = st.columns(2)
    for i, (name, count, desc) in enumerate(flags):
        with cols[i % 2]:
            st.markdown(T.compact(
                f'<div class="kpi">'
                f'<div class="label">{name}</div>'
                f'<div class="value">{count:,}</div>'
                f'<div style="color:{T.TEXT_DIM}; font-size:12px;'
                f' margin-top:6px;">{desc}</div>'
                f'</div>'
            ), unsafe_allow_html=True)
