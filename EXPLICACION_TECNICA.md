# Explicación Técnica — Proyecto *Smart Supply Chain*

> Dirigido a alguien con conocimientos generales de programación. Se explica a
> nivel de **módulos y funciones**, no línea por línea. Para el detalle de cifras
> y validaciones, ver `DOC/DOCUMENTACION_PROYECTO.md`.

---

## 1. Visión de arquitectura

El proyecto es un pipeline analítico *end-to-end* sobre el dataset público
**Olist (Brazilian E-Commerce)**, materializado en dos artefactos ejecutables:

- **8 notebooks** (`Modelado/01..08`) — pipeline de datos y modelado *batch*.
- **1 app Streamlit** (`App/`) — capa de presentación e interacción.

Principio de diseño central: **separación batch / serving**. Los notebooks
hacen todo el cómputo pesado (limpieza, ETL, entrenamiento) y **persisten
artefactos** (`CSV/*.csv`, `Modelado/_modelo/*.joblib`). La app **nunca
re-entrena ni recalcula**: solo lee esos artefactos. Esto mantiene la app
liviana (arranque ≈ 5 s) y reproducible.

### Diagrama de flujo de datos

```
                          ┌─────────────────────────────────────┐
   FUENTE EXTERNA          │  9 tablas crudas Olist (~1.4M filas) │
                          └──────────────────┬──────────────────┘
                                             │
                  [01_limpieza_datos_olist.ipynb]
                   · dedup, parseo de fechas, normalización texto
                   · imputación por mediana, banderas de calidad
                                             │
                                             ▼
                          ┌─────────────────────────────────────┐
                          │      9 tablas limpias (en memoria)   │
                          └──────────────────┬──────────────────┘
                                             │
                  [02_etl_data_warehouse.ipynb]
                   · esquema estrella (6 dims + 2 facts)
                   · feature engineering temporal/logístico
                   · validación del cubo (sumas, integridad ref.)
                   · LOAD a BigQuery (WRITE_TRUNCATE)
                                             │
                          ┌──────────────────┴───────────────────┐
                          ▼                                       ▼
              tad_pedidos.csv (99,441×42)           tad_ventas.csv (112,650×55)
                          │                                       │
                          │             [03_correccion_traduccion]│ fix categoría EN
                          │                                       ▼
                          │                          tad_ventas.csv (corregido)
                          │                                       │
        ┌─────────────────┼───────────────────┬───────────────────┤
        ▼                 ▼                   ▼                   ▼
[04_calendario]     [06_clustering]     [07_series_tiempo]   [05_EDA/modelo v1]
 dim_calendario      seller_agg_         series_demanda_      árbol decisión
 tad_pedidos_        clusters.csv        diaria.csv            F1=0.23
 enriquecido.csv     perfil_clusters     alertas_inventario
        │            (K-Means k=3)       (SARIMA)
        │                 │                   │
        └────────┬────────┘                   │
                 ▼                            │
        [08_modelo_supervisado_v2.ipynb]       │
         · features: seller cluster +          │
           distancia haversine + calendario    │
         · Random Forest tuneado (GridSearchCV)│
         · F1=0.39                             │
                 │                            │
                 ▼                            ▼
       rf_v2_pipeline.joblib            07_*.csv, 06_*.csv,
       rf_v2_schema.joblib              05_*.csv, 08_*.csv
                 │                            │
                 └──────────────┬─────────────┘
                                ▼
                  ┌──────────────────────────────┐
                  │   App/ (Streamlit + Plotly)   │
                  │   lib/data.py  → carga cacheada│
                  │   6 vistas + agente (LLM+reglas)│
                  └──────────────────────────────┘
                                │
                                ▼
                         Usuario final (navegador)
```

**Capa paralela:** las sábanas `tad_pedidos` y `tad_ventas` también se cargan a
**BigQuery** (`mineria-datos-493000.smart_supply_chain`) para alimentar Looker
Studio. Esa rama es independiente de la app Streamlit.

---

## 2. Capa de limpieza — `01_limpieza_datos_olist.ipynb`

**Propósito:** sanear las 9 tablas crudas de Olist; producir tablas limpias en
memoria para el ETL.

**Inputs/outputs:**
- Input: 9 CSV crudos de Olist (`DataFrame` por tabla).
- Output: 9 `DataFrame` limpios.

**Operaciones por tabla (resumen):**
- **Geolocation:** dedup (−261,831 filas), filtro de coordenadas fuera del
  *bounding box* de Brasil, agregación a nivel `zip_code_prefix` con
  `mean(lat,lng)` + `mode(city,state)`. 1,000,163 → 19,010 filas.
- **Products:** nulos de categoría → `Sin Categoria`; imputación numérica por
  **mediana** (robusta a outliers, preserva cola larga).
- **Orders:** parseo de 5 columnas a `datetime64`; **se conservan los `NaT`**
  de entrega para pedidos no entregados (decisión deliberada — no son errores).
- **Reviews:** errores tipográficos/inconsistencias no se eliminan; se
  codifican como **banderas booleanas** (`flag_short_message`,
  `flag_review_id_duplicated`, etc.) para no destruir información.

**Decisión de diseño:** política de *no destrucción* — donde un dato es
sospechoso pero no claramente inválido, se marca con una bandera en lugar de
eliminarse. Esto permite que pasos posteriores decidan.

**Limitaciones:** la imputación por mediana introduce sesgo hacia el centro de
la distribución; aceptable porque las columnas afectadas no son targets de
modelado.

---

## 3. Capa ETL / Data Warehouse — `02_etl_data_warehouse.ipynb`

**Propósito:** transformar las tablas limpias en un **modelo dimensional
(esquema estrella)** y dos *tablas planas* analíticas; cargar a BigQuery.

**Inputs/outputs:**
- Input: 9 `DataFrame` limpios.
- Output:
  - 6 dimensiones + 2 tablas de hechos (`fact_ventas` 112,650×21,
    `fact_pedidos` 99,441×17).
  - 2 sábanas: `tad_pedidos` (99,441×42, grano = pedido) y `tad_ventas`
    (112,650×55, grano = ítem de pedido).
  - 2 tablas en BigQuery (`bigquery.LoadJobConfig`, `WRITE_TRUNCATE`,
    `autodetect=True`).

**Feature engineering relevante:**
- Temporal: `fecha_key` (YYYYMMDD), `anio/mes/dia/trimestre`,
  `dia_semana_*`, `es_fin_semana`.
- Logístico: `delivery_days_real`, `delivery_days_estimated`,
  `delivery_delay_days`, `is_late_delivery` (target binario), `is_delivered`.
- Producto: `product_volume_cm3 = length × height × width`.
- Pago: agregación por pedido — `sum(payment_value)`, `max(installments)`,
  `mode(payment_type)`.

**Decisión de diseño:**
- `pago_key` **sintética** con sentinela `SIN_PAGO` (key=0) para pedidos sin
  registro de pago → integridad referencial 100 % sin perder filas.
- Esquema estrella en vez de copo de nieve: simplicidad para BI, las
  dimensiones no se normalizan más.

**Validación del cubo (batería de asserts):** unicidad de llaves en
dimensiones, integridad referencial al 100 % en las 5 FKs, y **conciliación de
totales monetarios** (`price`, `freight_value`, `payment_value`) entre origen y
`fact_ventas` — cuadran al centavo.

**Dependencias:** `pandas`, `google-cloud-bigquery`, `pandas-gbq`, `pyarrow`.
Credenciales GCP vía `SSC_CREDENTIALS` (ADC).

**Limitaciones:** la carga usa `WRITE_TRUNCATE` (reemplazo total); no hay
estrategia de carga incremental (`WRITE_APPEND`) — decisión consciente, fuera
de alcance.

---

## 4. Bug fix de traducción — `03_correccion_traduccion_categorias.ipynb`

**Propósito:** reparar `product_category_name_english`, 100 % nula en
`tad_ventas`.

**Causa raíz:** el `merge` del ETL unía `product_category_name` ya transformado
a Title Case (`Esporte Lazer`) contra la tabla de traducción en `snake_case`
(`esporte_lazer`) → join sin match, fallo silencioso.

**Solución:** backup previo (`_backup/tad_ventas_backup_pre_bugfix.csv`),
diccionario canónico de **74 entradas**, normalización Title Case → snake_case,
mapeo directo y asserts de calidad (conteo de filas, no-nulos, consistencia 1:1
PT↔EN). `tad_ventas.csv` se reescribe; estructura de 55 columnas inalterada.

**Lección de diseño:** los joins sobre claves transformadas son frágiles;
conviene unir sobre claves canónicas inmutables o validar la tasa de match
post-join.

---

## 5. Enriquecimiento exógeno — `04_enriquecimiento_calendario_brasil.ipynb`

**Propósito:** cumplir el requisito de **fuente exógena**; añadir contexto
calendárico de Brasil al dataset.

**Inputs/outputs:**
- Input: `tad_pedidos`, librería `holidays` (calendario BR), reglas de Carnaval
  y fechas retail.
- Output: `dim_calendario.csv` (1,096 días, 2016–2018) y
  `tad_pedidos_enriquecido.csv` (pedidos + banderas exógenas).

**Variables derivadas:** `es_feriado_nacional`, `es_carnaval`,
`es_evento_retail`, `es_dia_no_laboral`, `dias_a_proximo_evento`,
`en_ventana_pre_evento_3d/7d`.

**Validación:** las banderas son discriminativas sobre `is_late_delivery` —
Black Friday 16.92 % de retraso (2.58× la media global de 6.57 %), Cyber Monday
17.87 % (2.72×).

**Decisión de diseño:** reemplazar el proxy crudo `mes` (importancia 0.33 en el
árbol v1) por eventos causales reales.

---

## 6. Modelo supervisado v1 — `05_analisis_exploratorio_modelado.ipynb`

**Propósito:** EDA + primer modelo de clasificación binaria de
`is_late_delivery`.

**Tipo de modelo y justificación:** **Árbol de decisión** como modelo
principal, comparado contra Dummy (baseline) y Regresión logística. Elección
condicionada por una restricción académica: *solo arquitecturas vistas en
clase*.

**Diseño del pipeline:**
- `ColumnTransformer`: imputación (mediana / most-frequent) + `OneHotEncoder`
  para categóricas + escalado opcional.
- Split estratificado 70/30, `random_state=42`.
- Tuning: `GridSearchCV`, 90 combinaciones; mejor config
  `criterion=entropy, max_depth=5, min_samples_leaf=50, min_samples_split=50`.

**Tratamiento de fuga de información:** se excluyen explícitamente
`delivery_days_real`, `delivery_delay_days`, `review_score`, `is_bad_review`,
`is_good_review`, `order_delivered_customer_date` — variables conocidas solo
*después* de la entrega.

**Features más importantes (árbol ajustado):** `mes` (0.33), `trimestre`
(0.21), `delivery_days_estimated` (0.17), dummies de `customer_state`.

**Métricas y su significado:**
- Target con desbalance fuerte: **6.57 %** positivos. Por eso accuracy es
  engañosa (el Dummy logra 0.93) y se prioriza **F1 de la clase 1** y
  **PR-AUC**.
- Árbol: **F1₁ = 0.23**, Recall₁ = 0.60, Precision₁ = 0.15. Lectura de negocio:
  detecta 60 % de los retrasos reales pero el 85 % de sus alertas son falsos
  positivos.

**Limitación:** el modelo se apoya en proxies de estacionalidad
(`mes`/`trimestre`), no en señales causales. Esto motiva el v2.

---

## 7. Clustering de sellers — `06_clustering_sellers.ipynb`

**Propósito:** segmentación no supervisada de los 3,095 sellers para definir
estrategias de reabastecimiento diferenciadas.

**Inputs/outputs:**
- Input: `seller_agg` — tabla agregada, 1 fila/seller, 13 variables en 5
  dimensiones (volumen, ticket, servicio, satisfacción, alcance).
- Output: `06_seller_agg_clusters.csv` (sellers + etiqueta + estrategia),
  `06_perfil_clusters.csv` (resumen gerencial).

**Tipo de modelo y justificación:** **K-Means** (`k-means++`, `n_init=10`,
`random_state=42`). Elegido por simplicidad e interpretabilidad y por estar
dentro del temario.

**Pipeline:**
- `log1p` sobre variables monetarias y de conteo (reduce sesgo de cola larga).
- `StandardScaler` (K-Means es sensible a la escala — usa distancia euclídea).
- Selección de `k`: barrido `k ∈ {2..10}` evaluado con codo (inercia),
  silhouette y Davies-Bouldin; rango operativo restringido a 3–6. **k=3**.

**Resultado:** Cluster 1 *Power-seller confiable* (1,058), Cluster 0 *Mediano
regional* (1,541), Cluster 2 *Cola larga inestable* (496, review medio 2.42).

**Métricas en contexto:** silhouette modesto — esperable, los sellers forman un
continuo, no grumos nítidos; el valor del clustering es **operativo**
(estrategia diferenciada), no geométrico.

**Dependencia descendente:** la etiqueta de cluster y `seller_tasa_retraso_hist`
alimentan el modelo v2.

**Frecuencia de reentrenamiento:** trimestral o ante cambios grandes en el
catálogo de sellers.

---

## 8. Series de tiempo y alertas — `07_series_tiempo_y_alertas.ipynb`

**Propósito:** pronóstico de demanda diaria por categoría + sistema de alertas
tempranas de stockout / sobre-stock.

**Inputs/outputs:**
- Input: demanda diaria en ítems por `product_category_name_english`, top-5
  categorías, ventana de 730 días.
- Output: `07_series_demanda_diaria.csv`, `07_alertas_inventario.csv`,
  `07_metricas_series_tiempo.csv`.

**Tipo de modelo y justificación:** **SARIMA(1,1,1)(1,1,1,7)** vía
`statsmodels`. Estacionalidad de período 7 (semanal). La estacionalidad anual
**no** se modela: el train (~700 días) contiene solo ~1.9 ciclos anuales,
insuficiente. Baseline de comparación: naïve estacional (repetir última
semana).

**Evaluación:** split rolling-origin 700/30, métrica **sMAPE**. SARIMA mejora
al naïve en 3 de 5 categorías y empata en 2 (nunca degrada). sMAPE ≈ 45 % —
alto en absoluto, pero la demanda diaria de e-commerce es intrínsecamente
ruidosa; la métrica relevante es *mejora relativa vs baseline*.

**Sistema de alertas (capa de reglas sobre el pronóstico):**
- STOCKOUT: IC superior 90 % > P90 histórico (90d).
- SOBRE-STOCK: IC inferior 90 % < P10 histórico.
- OK: dentro de banda.
- En horizonte 14d: 51 STOCKOUT, 12 SOBRE-STOCK, 7 OK.

**Limitación:** un modelo SARIMA independiente por categoría; no hay modelo
jerárquico ni *cross-learning* entre series.

**Reentrenamiento:** semanal o mensual, al refrescar la ventana de demanda.

---

## 9. Modelo supervisado v2 — `08_modelo_supervisado_v2.ipynb`

**Propósito:** reentrenar el clasificador de `is_late_delivery` con señales
causales; superar el techo de F1=0.23 del v1.

**Inputs/outputs:**
- Input: `tad_pedidos_enriquecido.csv` (calendario) + `seller_agg_clusters.csv`
  (cluster + historial) + coordenadas geo.
- Output: `rf_v2_pipeline.joblib` (pipeline serializado), `rf_v2_schema.joblib`
  (esquema de columnas de entrada), y 4 CSV de métricas/importancias.

**Tipo de modelo y justificación:** **Random Forest** tuneado por
`GridSearchCV`. Se eligió RF sobre Gradient Boosting por la **restricción
académica** (solo arquitecturas vistas en clase). RF aporta el efecto *ensemble*
(bagging de árboles) reduciendo la varianza del árbol único del v1.

**Bloques de features nuevas vs v1:**
- 7 banderas exógenas del calendario BR.
- Cluster del seller + `seller_tasa_retraso_hist` + `seller_review_promedio`.
- `distancia_km` — distancia geodésica **haversine** seller↔cliente.
- *Seller dominante*: cuando un pedido tiene ítems de varios sellers, se toma el
  de mayor `price`.

**Diseño:** grano = pedido (comparable con v1), split estratificado 70/30
`random_state=42`, `ColumnTransformer` (mediana + most-frequent + OneHot),
mismas exclusiones de fuga que v1. GridSearch: 24 combinaciones × 3 folds,
`scoring="f1"`. Mejor config: `n_estimators=400, max_depth=20,
max_features="sqrt", min_samples_leaf=5`.

**Features más importantes (RF tuneado):** `seller_tasa_retraso_hist` (0.19,
top-1), `delivery_days_estimated` (0.09), `mes` (0.09, cae desde 0.33),
`distancia_km` (0.08), `seller_review_promedio` (0.07).

**Métricas y su significado:**
- **F1₁ = 0.39** (vs 0.23 en v1, +70 %). PR-AUC 0.17→0.32 (+90 %). ROC-AUC
  0.72→0.84.
- Recall baja (0.60→0.49): el modelo es más selectivo. Precision sube
  (0.15→0.32): la tasa de falsos positivos por alerta cae de ~85 % a ~68 %.
- En contexto de negocio: cada alerta del v2 es ~2× más confiable que la del v1.

**Reentrenamiento:** trimestral, o tras un refresh del clustering de sellers
(del que depende su feature top-1).

---

## 10. Capa de aplicación — `App/`

**Propósito:** servir todos los artefactos en una UI interactiva. No hay
cómputo de modelado en runtime salvo `pipeline.predict` del RF v2.

**Estructura de módulos:**

| Módulo | Responsabilidad |
|---|---|
| `app.py` | Entry point: page config, inyección de CSS, hero, router de 6 tabs. |
| `lib/theme.py` | Paleta, CSS global, helpers visuales (`hero`, `kpi_card`, `chip`). |
| `lib/data.py` | Carga de CSV y del `.joblib`, **cacheada** (`@st.cache_data` para DataFrames, `@st.cache_resource` para el modelo). |
| `lib/charts.py` | Plantillas Plotly (template oscuro propio): `bar_estado`, `forecast_chart`, `gauge_prob`, etc. |
| `lib/views/*.py` | Una vista por archivo: `overview`, `prediccion`, `pronostico`, `sellers`, `calidad`, `agente`. |
| `lib/agent.py` | Motor conversacional rule-based. |
| `lib/llm.py` | Integración con LLM (Gemini). |

**Decisión de diseño:** cache agresivo en `data.py` → primer arranque ≈ 5 s,
reruns instantáneos. La vista `prediccion` reconstruye el vector de entrada
según `rf_v2_schema.joblib` y llama a `pipeline.predict_proba`.

**Dependencias:** `streamlit` 1.57, `plotly` 6.7, `joblib`, `pandas`.

---

## 11. Agente conversacional — `lib/agent.py` + `lib/llm.py`

Arquitectura **híbrida de dos vías** con degradación elegante.

### 11.1 Motor rule-based — `lib/agent.py`

**Propósito:** responder de forma determinista, sin costo ni latencia de red.

**Pipeline (minería de texto clásica, dentro del temario):**
1. `normalize()` — lowercase + strip de acentos (`unicodedata`) + colapso de
   espacios.
2. Extracción de entidades por diccionario (estados UF de Brasil, categorías,
   clusters).
3. *Intent matching* por puntaje de keywords contra un set finito de intents.
4. Cada intent tiene un *handler* que consulta los `DataFrame` cacheados de
   `lib.data` y devuelve un `AgentResponse`.

**Tipo de salida:** `AgentResponse` (dataclass) — `text`, `intent`, `chips`,
`table`, `table_config`, `chart` (figura Plotly), `followups`. Cubre **19
intents/visualizaciones**.

### 11.2 Capa LLM — `lib/llm.py`

**Propósito:** dar lenguaje natural fluido a las preguntas escritas libremente.

**Flujo:** ante input escrito, se construye un *system prompt* con un snapshot
textual (~4 KB) del estado del negocio (KPIs, retraso por estado, top
categorías, clusters, alertas, métricas del modelo, errores SARIMA) + el
historial de conversación. El LLM (Gemini, default `gemini-3-flash-lite`)
responde en JSON estructurado `{text, viz, viz_hint}`. Si pide una `viz`, se
reutiliza el `chart`/`table`/`chips` del handler rule-based correspondiente; el
texto lo redacta el LLM.

**Configuración:** clave en `st.secrets["gemini"]["api_key"]` o env
`GEMINI_API_KEY`; modelo sobreescribible vía secrets/env.

**Degradación:** sin clave o ante fallo de la llamada → **fallback automático**
al motor rule-based. Los botones de sugerencia/follow-up van **siempre** directo
al rule-based (determinista, gratis, instantáneo).

**Decisión de diseño:** el rule-based se conserva como núcleo por la restricción
académica (debe poder funcionar solo con técnicas vistas en clase); el LLM es
una mejora de UX *por encima* y desactivable quitando la clave de secrets.

**Limitación:** el LLM solo "ve" el snapshot de ~4 KB — no consulta los
DataFrame completos, así que su precisión numérica está acotada a lo
pre-resumido.

---

## 12. Stack y reproducibilidad

- **Lenguaje:** Python 3 (notebooks en Colab y `venv` local con Python 3.14).
- **Datos/ML:** `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `holidays`.
- **Almacenamiento analítico:** Google BigQuery (`mineria-datos-493000.smart_supply_chain`).
- **BI:** Looker Studio (sobre BigQuery) + dashboard Streamlit/Plotly local.
- **Serving:** Streamlit 1.57, Plotly 6.7, modelo serializado con `joblib`.
- **Ejecución de la app:** `.venv/bin/python -m streamlit run App/app.py`.

**Supuestos clave del proyecto:**
- Restricción académica: solo arquitecturas vistas en clase (de ahí Árbol/RF en
  lugar de Gradient Boosting).
- La capa batch y la capa serving están desacopladas vía artefactos en disco; un
  cambio de modelo exige re-ejecutar el notebook 08 y regenerar los `.joblib`.
- No hay carga incremental: el ETL reemplaza tablas completas (`WRITE_TRUNCATE`).
