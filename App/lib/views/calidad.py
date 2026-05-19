"""Vista 5 — Calidad de datos y enriquecimiento."""
import streamlit as st

from .. import data as D
from .. import theme as T


def render():
    cal = D.load_calendario()
    ped = D.load_pedidos()
    ven = D.load_ventas_min()

    st.markdown(T.section("Cómo limpiamos y preparamos la información",
                           badge="Sección 05",
                           meta="resumen del proceso"),
                 unsafe_allow_html=True)

    st.markdown(T.callout(
        "Antes de analizar nada, hay que asegurarse de que los datos sean "
        "confiables. Aquí mostramos qué limpiamos, qué errores encontramos y "
        "cómo agregamos información extra (como feriados y días de oferta) "
        "para que los análisis sean más certeros."
    ), unsafe_allow_html=True)

    st.markdown(T.method_note(
        "Esta sección documenta el <strong>proceso ETL</strong> (extraer, "
        "transformar y cargar): los datos originales se reunieron, se "
        "corrigieron errores y duplicados, y se verificó que todas las cifras "
        "cuadren entre sí. Es el cimiento de todo el tablero: sin datos "
        "limpios, ningún modelo ni gráfica sería confiable.",
        label="Cómo se obtiene esta sección",
    ), unsafe_allow_html=True)

    # ---- Resumen de limpieza ------------------------------------------
    st.markdown(T.kpi_grid(
        T.kpi_card("Archivos originales limpiados", "9",
                    delta="paso 1: limpieza", delta_dir="neutral"),
        T.kpi_card("Registros duplicados eliminados", "261 831",
                    delta="98.1% menos", delta_dir="up"),
        T.kpi_card("Ubicaciones válidas verificadas", "19 010",
                    delta="coordenadas dentro de Brasil", delta_dir="neutral"),
        T.kpi_card("Errores de ortografía corregidos", "5",
                    delta="en nombres de categorías", delta_dir="neutral"),
    ), unsafe_allow_html=True)

    # ---- Validaciones del cubo ----------------------------------------
    st.markdown(T.section("Comprobaciones de que todo cuadra",
                           badge="Verificación",
                           meta="ningún número se quedó suelto"),
                 unsafe_allow_html=True)

    validations = [
        ("Cada cliente, producto y vendedor tiene un código único", "100 %", "ok"),
        ("Todos los clientes están bien registrados", "100 %", "ok"),
        ("Todos los productos están bien registrados", "100 %", "ok"),
        ("Todos los vendedores están bien registrados", "100 %", "ok"),
        ("Todas las fechas están bien clasificadas", "100 %", "ok"),
        ("Todos los métodos de pago están bien clasificados", "100 %", "ok"),
        ("El total de ventas coincide entre archivos", "R$ 13.59 M = R$ 13.59 M", "ok"),
        ("El total de envíos coincide entre archivos", "R$ 2.25 M = R$ 2.25 M", "ok"),
        ("El total cobrado coincide con lo facturado", "R$ 15.85 M = R$ 15.85 M", "ok"),
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
    st.markdown(T.section("Corrección · traducción de categorías al inglés",
                           badge="Corrección",
                           meta="un detalle que perdía toda la información"),
                 unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    desc_style = (f"color:{T.TEXT_DIM}; font-size:12.5px; margin-top:8px;"
                   f" line-height:1.45;")
    with c1:
        st.markdown(T.compact(
            f'<div class="kpi" style="border-left:3px solid {T.ROSE};">'
            f'<div class="label">Antes de corregirlo</div>'
            f'<div class="value" style="font-size:22px; color:{T.ROSE};">100 % sin traducir</div>'
            f'<div style="{desc_style}">'
            f'Los nombres de categorías estaban escritos de forma distinta en '
            f'dos lugares (uno con espacios, otro con guiones bajos). '
            f'Ninguno coincidía, así que <strong>ninguna</strong> de las '
            f'112,650 filas se pudo traducir al inglés.'
            f'</div></div>'
        ), unsafe_allow_html=True)
    with c2:
        st.markdown(T.compact(
            f'<div class="kpi" style="border-left:3px solid {T.EMERALD};">'
            f'<div class="label">Después de corregirlo</div>'
            f'<div class="value" style="font-size:22px; color:{T.EMERALD};">100 % traducidas</div>'
            f'<div style="{desc_style}">'
            f'Armamos un diccionario con <strong style="color:{T.TEXT};">74 categorías</strong> '
            f'(las 71 oficiales más 3 variantes especiales) y unificamos el '
            f'formato. Ahora todas las categorías tienen su traducción.'
            f'</div></div>'
        ), unsafe_allow_html=True)

    # ---- Enriquecimiento exógeno (calendario) -------------------------
    st.markdown(T.section("Calendario brasileño · días especiales",
                           badge="Información extra",
                           meta="feriados, Carnaval y ofertas comerciales"),
                 unsafe_allow_html=True)

    n_feriado    = int(cal["es_feriado_nacional"].sum())
    n_carnaval   = int(cal["es_carnaval"].sum())
    n_retail     = int(cal["es_evento_retail"].sum())
    n_no_laboral = int(cal["es_dia_no_laboral"].sum())

    st.markdown(T.kpi_grid(
        T.kpi_card("Días totales considerados", f"{len(cal):,}",
                    delta="del 2016 al 2018", delta_dir="neutral"),
        T.kpi_card("Feriados nacionales", str(n_feriado)),
        T.kpi_card("Días de Carnaval", str(n_carnaval)),
        T.kpi_card("Días de ofertas (Black Friday, Cyber Monday...)", str(n_retail)),
    ), unsafe_allow_html=True)

    # Tasa de retraso por cohorte exógena (sanity)
    if "es_evento_retail" in ped.columns:
        cohortes = []
        media = ped["is_late_delivery"].mean()
        cohortes.append(("Promedio general",   media,                                            "neutral"))
        cohortes.append(("En feriado nacional", ped.loc[ped["es_feriado_nacional"] == 1, "is_late_delivery"].mean(), "warn"))
        cohortes.append(("En Carnaval",         ped.loc[ped["es_carnaval"] == 1, "is_late_delivery"].mean(),         "warn"))
        cohortes.append(("En día de oferta",    ped.loc[ped["es_evento_retail"] == 1, "is_late_delivery"].mean(),    "alert"))
        cohortes.append(("En fin de semana",    ped.loc[ped["es_fin_semana"] == 1, "is_late_delivery"].mean(),       "neutral"))

        st.markdown(T.section("¿Las fechas especiales realmente afectan los retrasos?",
                               badge="Validación",
                               meta="% de pedidos con retraso por tipo de día"),
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
                    f'<div class="delta {arrow}">×{ratio:.2f} vs promedio</div>'
                    f'</div>'
                ), unsafe_allow_html=True)

    # ---- Banderas de calidad de reviews -------------------------------
    st.markdown(T.section("Reseñas sospechosas que detectamos",
                           badge="Calidad de reseñas",
                           meta="señales para identificar reseñas poco confiables"),
                 unsafe_allow_html=True)
    flags = [
        ("Mensajes demasiado cortos",           int(ped["flag_short_message"].sum()),
         "Reseñas de solo 1 a 3 letras (probablemente sin contenido real)"),
        ("Respuestas antes que la reseña",  int(ped["flag_answer_before_creation"].sum()),
         "El vendedor respondió antes de que existiera la reseña (error de fecha)"),
        ("Mismo identificador de reseña repetido",    int(ped["flag_review_id_duplicated"].sum()),
         "La misma reseña aparece más de una vez"),
        ("Una reseña ligada a varios pedidos",   int(ped["flag_review_id_multi_order"].sum()),
         "Una reseña que está conectada a más de un pedido distinto"),
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
