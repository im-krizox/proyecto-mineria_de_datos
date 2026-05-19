"""Página de Inicio — presentación del tablero y guía de sus secciones."""
import streamlit as st

from .. import data as D
from .. import theme as T


_MESES = {1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo",
          6: "junio", 7: "julio", 8: "agosto", 9: "septiembre",
          10: "octubre", 11: "noviembre", 12: "diciembre"}


def _fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def _fmt_mes(ts) -> str:
    return f"{_MESES.get(ts.month, ts.month)} de {ts.year}"


def _fmt_money(v: float) -> str:
    if v >= 1e6:
        return f"R$ {v/1e6:.1f} M"
    if v >= 1e3:
        return f"R$ {v/1e3:.0f} K"
    return f"R$ {v:.0f}"


# Cada tarjeta describe una sección del Tablero y el método que la sustenta.
SECCIONES = [
    ("01 · Resumen del negocio",
     "Indicadores generales del negocio: cuántos pedidos hubo, cuánto se "
     "vendió, qué categorías generan más ingresos y qué porcentaje de "
     "entregas llegó tarde.",
     "Estadística descriptiva"),
    ("02 · Riesgo de retraso",
     "Una calculadora que estima qué tan probable es que un pedido llegue "
     "tarde, según el vendedor, la distancia, la fecha y el tipo de pago.",
     "Random Forest"),
    ("03 · Pronóstico de ventas",
     "Anticipa la demanda de las próximas dos semanas para las categorías "
     "principales y avisa cuándo conviene reabastecer o frenar inventario.",
     "SARIMA · series de tiempo"),
    ("04 · Tipos de vendedores",
     "Agrupa a los vendedores en perfiles con comportamiento parecido, cada "
     "uno con una estrategia de inventario recomendada.",
     "K-Means · agrupamiento"),
    ("05 · Preparación de datos",
     "Muestra cómo se limpió y verificó la información, y qué datos extra "
     "(feriados, Carnaval, ofertas) se sumaron para enriquecer el análisis.",
     "Proceso ETL"),
    ("06 · Asistente",
     "Permite preguntar en lenguaje natural sobre el negocio y recibir "
     "respuestas con cifras y gráficas del propio tablero.",
     "Modelo de lenguaje + reglas"),
]


def _feat_card(tag: str, desc: str, algo: str) -> str:
    titulo = tag.split(" · ", 1)[1]
    numero = tag.split(" · ", 1)[0]
    return T.compact(
        f'<div class="feat">'
        f'<div class="ftag">{numero}</div>'
        f'<h3>{titulo}</h3>'
        f'<p>{desc}</p>'
        f'<span class="algo">{algo}</span>'
        f'</div>'
    )


def render():
    k = D.kpi_globales()
    desde, hasta = k["rango_fechas"]

    # ---- Hero ---------------------------------------------------------
    st.markdown(T.hero(
        eyebrow="Smart Supply Chain · Nexus Supply",
        title="Tablero de Operaciones Inteligente",
        subtitle=(
            "Una herramienta de apoyo a la decisión para la cadena de "
            "suministro de Nexus Supply. Reúne en un solo lugar el estado del "
            "negocio, el riesgo de entregas tardías, el pronóstico de demanda "
            "y el perfil de los vendedores, de modo que el equipo comercial "
            "pueda actuar a tiempo y con datos, no con suposiciones."
        ),
    ), unsafe_allow_html=True)

    # ---- Contexto -----------------------------------------------------
    st.markdown(T.callout(
        "Este tablero se construyó sobre la operación real de un negocio de "
        f"comercio electrónico en Brasil entre <strong>{_fmt_mes(desde)}</strong> y "
        f"<strong>{_fmt_mes(hasta)}</strong>. A partir de esos pedidos se "
        "entrenaron modelos que <strong>anticipan</strong> lo que puede pasar: "
        "qué pedidos corren riesgo de retrasarse y cuánto se venderá en los "
        "próximos días. El objetivo es pasar de mirar el pasado a prepararse "
        "para lo que viene."
    ), unsafe_allow_html=True)

    # ---- Snapshot rápido ----------------------------------------------
    st.markdown(T.section("El negocio en cifras",
                           badge="Panorama",
                           meta="datos consolidados del periodo"),
                 unsafe_allow_html=True)
    st.markdown(T.kpi_grid(
        T.kpi_card("Pedidos analizados", _fmt_int(k["n_pedidos"])),
        T.kpi_card("Productos vendidos", _fmt_int(k["n_items"])),
        T.kpi_card("Ventas totales", _fmt_money(k["gmv"]),
                    hint="Incluye el precio del producto y el envío."),
        T.kpi_card("Vendedores en la plataforma", _fmt_int(k["n_sellers"])),
        T.kpi_card("Entregas con retraso",
                    f'{k["tasa_retraso"]*100:.1f}', unit="%",
                    hint="Porcentaje de pedidos que llegaron después de la "
                         "fecha prometida."),
    ), unsafe_allow_html=True)

    # ---- Qué incluye el tablero ---------------------------------------
    st.markdown(T.section("Qué encontrarás en el tablero",
                           badge="Guía",
                           meta="seis secciones · abre 'Tablero de análisis'"),
                 unsafe_allow_html=True)
    st.markdown(
        '<div style="display:grid; gap:16px; margin:8px 0 8px 0;'
        ' grid-template-columns:repeat(auto-fit,minmax(300px,1fr));">'
        + "".join(_feat_card(tag, desc, algo)
                  for tag, desc, algo in SECCIONES)
        + '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(T.method_note(
        "Cada sección indica con una etiqueta azul el método que la sustenta. "
        "Los nombres técnicos (<strong>Random Forest</strong>, "
        "<strong>SARIMA</strong>, <strong>K-Means</strong>) se mantienen "
        "porque son los algoritmos estándar de la industria; dentro de cada "
        "sección se explica en lenguaje sencillo para qué sirve cada uno.",
        label="Sobre los métodos",
    ), unsafe_allow_html=True)
