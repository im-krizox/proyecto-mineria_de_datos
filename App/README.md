# Smart Supply Chain · Predictive Ops Dashboard

Interfaz web del proyecto final de Minería de Datos (Grupo 2805, UNAM).
Construida en **Streamlit + Plotly** sobre los outputs de los notebooks 02–08.

## Arquitectura

```
App/
├── app.py                  # Entry point (hero + tabs)
├── .streamlit/
│   └── config.toml         # Tema oscuro (primary #f59e0b sobre #0b1220)
└── lib/
    ├── theme.py            # Paleta, CSS global, helpers (hero, kpi_card, chip)
    ├── data.py             # Carga cacheada de los CSVs + modelo joblib
    ├── charts.py           # Gráficos Plotly con template propio
    └── views/
        ├── overview.py     # KPIs ejecutivos, tendencia mensual, top categorías
        ├── prediccion.py   # Calculadora del modelo v2 (RF tuneado)
        ├── pronostico.py   # SARIMA por categoría + alertas STOCKOUT/SOBRE-STOCK
        ├── sellers.py      # Explorador de clusters K-Means
        └── calidad.py      # Trazabilidad de limpieza, bug-fix y enriquecimiento
```

## Vistas

| # | Vista | Insumos |
|---|---|---|
| 1 | Visión general | `04_tad_pedidos_enriquecido.csv`, `02_tad_ventas.csv` |
| 2 | Predicción de retraso | `Modelado/_modelo/rf_v2_pipeline.joblib`, `08_*.csv` |
| 3 | Pronóstico de demanda | `07_series_demanda_diaria.csv`, `07_alertas_inventario.csv`, `07_metricas_series_tiempo.csv` |
| 4 | Segmentación de sellers | `06_seller_agg_clusters.csv`, `06_perfil_clusters.csv` |
| 5 | Calidad de datos | `04_dim_calendario.csv` + métricas de cubo |

## Prerrequisitos

1. Dependencias instaladas en `.venv` (desde la raíz del proyecto):

   ```bash
   .venv/bin/python -m pip install -r requirements.txt
   ```

2. Notebook 08 ejecutado para producir el pipeline serializado:

   ```bash
   cd Modelado
   ../.venv/bin/python3.14 -m nbconvert --to notebook --execute \
       08_modelo_supervisado_v2.ipynb --output 08_modelo_supervisado_v2.ipynb
   ```

   Esto crea `Modelado/_modelo/rf_v2_pipeline.joblib` (~107 MB).

## Ejecución

Desde la raíz del proyecto:

```bash
.venv/bin/python -m streamlit run App/app.py
```

La app abrirá en `http://localhost:8501`. El primer arranque tarda ~5 s (carga del modelo y los CSVs); los reruns posteriores son instantáneos gracias al cacheo (`@st.cache_data`, `@st.cache_resource`).

### Variables de entorno (opcional)

| Variable | Default | Propósito |
|---|---|---|
| `CSV_DIR` | `<repo>/CSV` | Ubicación de los CSVs producidos por los notebooks |
| `GEMINI_API_KEY` | — | Clave de Google AI Studio para el agente conversacional (alternativa a `secrets.toml`) |
| `GEMINI_MODEL` | `gemini-3-flash-lite` | Modelo de Gemini a usar (override) |
| `GEMINI_DEBUG` | — | Si está definido, muestra warnings en la UI cuando falla la llamada al LLM |

## Agente conversacional (vista "Asistente")

El asistente combina **dos motores**:

1. **Motor LLM (Gemini)** — para las preguntas escritas en el `chat_input`.
   Inyecta como contexto un snapshot textual de los datos del proyecto
   (KPIs, retraso por estado, top categorías, clusters, alertas, métricas
   del modelo, factores, errores SARIMA) y responde con un JSON
   estructurado `{text, viz, viz_hint}`. Si pide una visualización,
   reusamos el handler equivalente del motor rule-based para adjuntar la
   gráfica/tabla/chips.
2. **Motor rule-based** (`lib/agent.py`) — para los **botones** de
   sugerencias y follow-ups. Es determinista, gratis e instantáneo.
   También sirve como **fallback** automático cuando no hay clave de
   Gemini configurada o falla la llamada.

### Configurar la clave de Gemini

#### Local

1. Genera una API key gratuita en https://aistudio.google.com/apikey
2. Copia el template y pega la clave:

   ```bash
   cp App/.streamlit/secrets.toml.example App/.streamlit/secrets.toml
   # editar App/.streamlit/secrets.toml y poner la api_key real
   ```

   El archivo `secrets.toml` está en `.gitignore` — nunca se sube al repo.

#### Streamlit Community Cloud

En el dashboard del deploy, abre **Settings → Secrets** y pega:

```toml
[gemini]
api_key = "AIza..."
model = "gemini-3-flash-lite"
```

Streamlit re-arranca la app automáticamente al guardar.

#### Sin clave (modo offline)

La vista detecta la ausencia de clave y conmuta a "modo respuestas rápidas":
la caja de chat sigue funcionando, pero todas las respuestas vienen del
motor rule-based determinista. No se rompe nada.

## Tema visual

Paleta inspirada en terminales financieras profesionales:

| Token | Color | Uso |
|---|---|---|
| `BG` | `#0b1220` | Fondo principal |
| `BG_CARD` | `#111827` | Cards y paneles |
| `AMBER` | `#f59e0b` | Acento primario (números clave, primary action) |
| `EMERALD` | `#10b981` | Positivo (OK, riesgo bajo, P10 histórico) |
| `ROSE` | `#ef4444` | Alerta (STOCKOUT, riesgo alto, P90 histórico) |
| `SKY` | `#38bdf8` | Información (series históricas, métricas v1) |

Tipografía:
- **Inter** (cuerpo + headings)
- **JetBrains Mono** (números, labels, etiquetas técnicas)

Sin emojis en toda la app; los estados se representan con chips (`OK`, `WARN`, `ALERT`, `INFO`) y símbolos profesionales.

## Capturas para la presentación

Para exportar capturas en alta resolución:
1. Abrir cada tab y esperar a que cargue todo el contenido.
2. Usar la captura nativa de macOS (`Cmd+Shift+4` → `Space`) o el plugin de Chrome *Full Page Screen Capture*.
3. Las gráficas Plotly tienen también botón nativo de descarga PNG en su barra de herramientas (hover sobre la gráfica).
