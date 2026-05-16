# Documentación del Proyecto — *Smart Supply Chain*

**Materia:** Minería de Datos · **Grupo 2805**
**Profesor:** M. en IA Oscar Daniel Acosta González
**Fecha de la versión:** 15 de mayo de 2026 (rev. 3 — refactor de cierre: renames con prefijo `NN_`, split del ETL, preámbulo unificado del EDA, integridad `pago_key` a 100%, paths via env)

---

## 1. Resumen ejecutivo

El proyecto construye un flujo *end-to-end* sobre el dataset público **Olist (Brazilian E-Commerce)** con el objetivo de soportar decisiones de la cadena de suministro de la empresa ficticia *Nexus Supply*. La solución entregada cubre:

1. **Limpieza** de las nueve tablas crudas de Olist (≈1.4 M de filas en total).
2. **ETL** que produce un esquema estrella (dimensiones + tablas de hechos) y dos tablas planas (*sábanas*) `tad_pedidos` y `tad_ventas`.
3. **Carga** de las tablas planas en **BigQuery** (proyecto `mineria-datos-493000`, dataset `smart_supply_chain`) para alimentar **Looker Studio**.
4. **EDA y modelado supervisado** para la predicción binaria de retraso de entrega (`is_late_delivery`).
5. **Bug fix** de la traducción de categorías PT→EN, perdida durante el ETL original.
6. **Enriquecimiento exógeno** con calendario brasileño (feriados nacionales + Carnaval + fechas comerciales clave).
7. **Segmentación no supervisada** (K-Means) de los 3,095 sellers en clusters operativos con estrategia de reabastecimiento diferenciada.
8. **Modelado de series de tiempo** (SARIMA) sobre la demanda diaria por categoría, con sistema de **alertas tempranas de stockout / sobre-stock**.

El proyecto se entrega en ocho notebooks y los archivos de documentación de `DOC/` (incluyendo los diagramas OLTP y de DWH en `DOC/diagramas/`).

| Notebook | Propósito | Celdas / Estado |
|---|---|---|
| `01_limpieza_datos_olist.ipynb` | Limpieza individual de las 9 tablas Olist | 84 |
| `02_etl_data_warehouse.ipynb` | Construcción del Data Warehouse + carga a BigQuery | 54 |
| `05_analisis_exploratorio_modelado.ipynb` | EDA, modelado supervisado v1 e hiperparametrización | 114 |
| `03_correccion_traduccion_categorias.ipynb` | Re-poblar `product_category_name_english` (rev. 2) | Ejecutado ✓ |
| `04_enriquecimiento_calendario_brasil.ipynb` | Calendario BR + banderas exógenas (rev. 2) | Ejecutado ✓ |
| `06_clustering_sellers.ipynb` | K-Means + perfilado + estrategias (rev. 2) | Ejecutado ✓ |
| `07_series_tiempo_y_alertas.ipynb` | SARIMA + sistema de alertas (rev. 2) | Ejecutado ✓ |
| `08_modelo_supervisado_v2.ipynb` | Modelo v2 con seller + distancia + calendario (rev. 3) | Ejecutado ✓ |

---

## 2. Datos fuente

### 2.1 Tablas Olist crudas

| Tabla | Filas | Cols | Llave principal |
|---|---:|---:|---|
| `olist_customers_dataset` | 99,441 | 5 | `customer_id` |
| `olist_orders_dataset` | 99,441 | 8 | `order_id` |
| `olist_order_items_dataset` | 112,650 | 7 | `order_id` + `order_item_id` |
| `olist_order_payments_dataset` | 103,886 | 5 | `order_id` + `payment_sequential` |
| `olist_order_reviews_dataset` | 99,224 | 7 | `review_id` |
| `olist_products_dataset` | 32,951 | 9 | `product_id` |
| `olist_sellers_dataset` | 3,095 | 4 | `seller_id` |
| `olist_geolocation_dataset` | 1,000,163 | 5 | `geolocation_zip_code_prefix` |
| `product_category_name_translation` | 71 | 2 | `product_category_name` |

### 2.2 Fuentes exógenas (rev. 2)

El documento `INSTRUCCIONES.md` exige enriquecer el dataset principal con **al menos una fuente exógena**. En la revisión 2 del proyecto se incorpora el **calendario brasileño** vía la librería `holidays` y reglas calendáricas (Carnaval y fechas comerciales).

**Calendario consolidado:** 1,096 días entre 2016-01-01 y 2018-12-31 (cubre el 100 % de los pedidos).

Eventos catalogados:
- **Feriados nacionales:** Año Nuevo, Tiradentes, Día del Trabajo, Independencia, Aparecida, Finados, Proclamación, Navidad, Viernes Santo (variable). 27 fechas.
- **Carnaval:** lunes y martes anteriores al Miércoles de Ceniza. 8 fechas (no es feriado oficial pero detiene la operación logística).
- **Eventos retail:** Black Friday, Cyber Monday, Día de la Madre, Día de los Enamorados (12-jun, equivalente brasileño de San Valentín), Día del Padre, Día del Niño. 18 fechas.

**Variables derivadas:** `es_feriado_nacional`, `es_carnaval`, `es_evento_retail`, `es_dia_no_laboral`, `dias_a_proximo_evento`, `en_ventana_pre_evento_3d`, `en_ventana_pre_evento_7d`.

**Validación:** las banderas son **altamente discriminativas** sobre la tasa de retraso (`is_late_delivery`):

| Cohorte | Tasa de retraso | Multiplicador vs media |
|---|---:|---:|
| Media global | 6.57 % | 1.0× |
| Carnaval | 11.67 % | 1.78× |
| Día del evento retail | 11.70 % | 1.78× |
| **Black Friday** | **16.92 %** | **2.58×** |
| **Cyber Monday** | **17.87 %** | **2.72×** |

> Antes la columna `mes` (proxy crudo de estacionalidad) tenía importancia 0.33 en el árbol. Las banderas exógenas reemplazan ese proxy con eventos reales.

---

## 3. Capa 1 — Limpieza (`01_limpieza_datos_olist.ipynb`)

El notebook está organizado por sub-notebooks lógicos, uno por tabla. Resumen de las decisiones por archivo:

### 3.1 Customers
- `customer_zip_code_prefix` cargado como `str` y normalizado a 5 dígitos con `zfill`.
- `customer_city` con `str.title()`.
- 0 nulos, 0 duplicados → no se eliminó ninguna fila.

### 3.2 Order items
- Conversión de `shipping_limit_date` a `datetime`.
- 0 valores `NaT` resultantes.

### 3.3 Geolocation
- 261,831 duplicados eliminados.
- 33 registros con coordenadas fuera de los límites de Brasil (lat ∈ [-33.75, 5.27], lng ∈ [-73.98, -34.79]) eliminados.
- Normalización de texto (acentos, mayúsculas).
- Agregación a nivel `zip_code_prefix` por `mean(lat,lng)` y `mode(city,state)`.
- **Resultado:** 19,010 filas (de 1,000,163 originales).

### 3.4 Products
- 610 nulos en `product_category_name` rellenados con `Sin Categoria`.
- Texto en formato Title Case (`esporte_lazer` → `Esporte Lazer`).
- Imputación de nulos numéricos con la **mediana**.

### 3.5 Orders
- Normalización de `order_status` (`strip` + `title`).
- Conversión de las 5 columnas de fecha a `datetime64`.
- **Decisión deliberada:** se mantienen NaTs en columnas de entrega para pedidos en estatus `Canceled`, `Invoiced`, etc.

### 3.6 Payments
- Estandarización de columnas y tipos.
- 0 nulos / 0 duplicados originalmente.
- Filtrado defensivo (no se eliminó ninguna fila).

### 3.7 Reviews
- 5 erratas tipográficas detectadas y conservadas como banderas (no se elimina información):
  - `flag_short_message` (mensajes 1-3 caracteres → 724 filas)
  - `flag_answer_before_creation` (timestamp inconsistente → 0 filas)
  - `flag_review_id_duplicated` (1,603 filas)
  - `flag_review_id_multi_order` (1,603 filas)
- Placeholders (`.`, `..`, `xxx`, `n/a`) convertidos a NA.

### 3.8 Sellers
- 25 ciudades con formatos sucios normalizadas (`sao paulo / sao paulo` → `sao paulo`, etc.).
- 2 valores irrecuperables (un email, una secuencia numérica) → NaN.

### 3.9 Category translation
- 5 erratas ortográficas en inglés corregidas (`costruction` → `construction`, `confort` → `comfort`, `craftmanship` → `craftsmanship`, etc.).

---

## 4. Capa 2 — Data Warehouse y ETL (`02_etl_data_warehouse.ipynb`)

### 4.1 Modelo dimensional (esquema estrella)

| Tabla | Tipo | Filas | Cols | Llave |
|---|---|---:|---:|---|
| `dim_tiempo` | Dimensión | 634 | 10 | `fecha_key` |
| `dim_cliente` | Dimensión | 99,441 | 5 | `customer_id` |
| `dim_geografia_cliente` | Dimensión | 14,994 | 5 | `zip_code_prefix` |
| `dim_producto` | Dimensión | 32,951 | 11 | `product_id` |
| `dim_vendedor` | Dimensión | 3,095 | 8 | `seller_id` |
| `dim_pago` | Dimensión | 28 | 3 | `pago_key` (sintética) |
| `fact_ventas` | Hechos | 112,650 | 21 | `order_id`+`order_item_id` |
| `fact_pedidos` | Hechos | 99,441 | 17 | `order_id` |
| `tad_ventas` | Sábana | 112,650 | 55 | `order_id`+`order_item_id` |
| `tad_pedidos` | Sábana | 99,441 | 42 | `order_id` |

### 4.2 Feature engineering temporal y logístico

Sobre `orders` se generan: `fecha`, `anio`, `mes`, `dia`, `trimestre`, `dia_semana_num`, `dia_semana_nombre`, `es_fin_semana`, `delivery_days_real`, `delivery_days_estimated`, `delivery_delay_days`, `is_late_delivery`, `is_delivered` y `fecha_key` (YYYYMMDD).

Sobre `products` se calcula `product_volume_cm3 = length × height × width`.

Sobre `payments` se agrega por pedido (suma de `payment_value`, máximo de `installments`, moda de `payment_type`).

Sobre `reviews` se agrega `review_score` promedio y se propagan las cuatro banderas de calidad.

### 4.3 Validaciones del cubo

El notebook ejecuta una **batería de validación** sólida:

| Prueba | Resultado |
|---|---|
| Llaves únicas en todas las dimensiones | ✓ |
| `order_id`+`order_item_id` único en `fact_ventas` | ✓ |
| Integridad referencial `customer_id` → `dim_cliente` | 100% |
| Integridad `product_id` → `dim_producto` | 100% |
| Integridad `seller_id` → `dim_vendedor` | 100% |
| Integridad `fecha_key` → `dim_tiempo` | 100% |
| Integridad `pago_key` → `dim_pago` | 100% (sentinela `SIN_PAGO`, pago_key=0, cubre pedidos sin registro de pago) |
| Suma de `price` items vs fact_ventas | $13,591,643.70 = $13,591,643.70 ✓ |
| Suma de `freight_value` items vs fact_ventas | $2,251,909.54 = $2,251,909.54 ✓ |
| Suma de `payment_value` (sólo pedidos con items) | $15,846,280.17 = $15,846,280.17 ✓ |

### 4.4 Carga a BigQuery

Las dos sábanas se suben con `bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE", autodetect=True)`:
- `mineria-datos-493000.smart_supply_chain.tad_pedidos` — 99,441 filas × 42 columnas
- `mineria-datos-493000.smart_supply_chain.tad_ventas` — 112,650 filas × 55 columnas

> Las credenciales se leen de `smart_supply_chain.json` (no incluido en el repo). Ruta configurable vía la variable de entorno `SSC_CREDENTIALS`; default = `smart_supply_chain.json` en CWD. Auth contra GCP via Application Default Credentials (`gcloud auth application-default login` o `GOOGLE_APPLICATION_CREDENTIALS`).

---

## 5. Capa 3 — EDA y modelado (`05_analisis_exploratorio_modelado.ipynb`)

### 5.1 Estructura, tipos y granularidad
Se confirma:
- `tad_pedidos`: 99,441 filas, granularidad por pedido. ✓
- `tad_ventas`: 112,650 filas, granularidad por ítem. ✓

### 5.2 Hallazgo crítico de calidad — **resuelto en rev. 2**
La columna **`product_category_name_english` en `tad_ventas` estaba 100 % nula** porque el merge se hacía contra los nombres ya transformados a Title Case (`Esporte Lazer`) mientras la tabla de traducción conserva `snake_case` (`esporte_lazer`). Solucionado en `03_correccion_traduccion_categorias.ipynb` (§ 6 de este documento) usando un diccionario canónico de 74 entradas. Cobertura post-fix: 100 % (0 nulos, 74 valores únicos).

### 5.3 Variable objetivo

`is_late_delivery` presenta fuerte desbalance:

| Clase | Conteo | % |
|---|---:|---:|
| 0 (a tiempo) | 92,906 | 93.43 % |
| 1 (tardío) | 6,535 | 6.57 % |

### 5.4 Análisis exploratorio relevante

**Tasas de retraso por estado** (top-5):

| Estado | Pedidos | Retraso % |
|---|---:|---:|
| AL | 413 | 20.58 |
| MA | 747 | 16.73 |
| SE | 350 | 14.57 |
| PI | 495 | 13.33 |
| CE | 1,336 | 13.17 |

**Estacionalidad** (meses con mayor retraso): marzo 14.6 %, noviembre 12.0 %, febrero 11.5 %. Trimestre Q1 = 10.75 %, Q4 = 8.27 %, Q2-Q3 ≈ 4 %.

**Pago:** `boleto` (7.10 %) > `credit_card` (6.49 %) > `voucher` > `debit_card`.

**Día de la semana:** sin diferencias relevantes (rango 6.05 % – 7.22 %).

### 5.5 Tratamiento de fuga de información
Se identifican y excluyen del modelo: `delivery_days_real`, `delivery_delay_days`, `review_score`, `is_bad_review`, `is_good_review`, `order_delivered_customer_date`. Decisión metodológicamente correcta.

### 5.6 Modelos entrenados

Pipeline con `ColumnTransformer` (imputación + OneHot + opcional escalado), división estratificada 70/30, evaluación con accuracy, precision/recall/F1 de la clase 1, ROC-AUC y PR-AUC.

| Modelo | Accuracy | Precision₁ | Recall₁ | F1₁ | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Dummy (clase mayoritaria) | 0.93 | 0.00 | 0.00 | 0.00 | 0.50 | 0.07 |
| **Árbol de decisión** | 0.74 | 0.15 | **0.60** | **0.23** | 0.72 | 0.17 |
| Regresión logística | 0.66 | 0.12 | 0.65 | 0.20 | 0.70 | 0.15 |
| Árbol ajustado (GridSearchCV) | 0.74 | 0.15 | 0.60 | 0.23 | 0.72 | 0.17 |

**GridSearchCV:** 90 combinaciones, mejor configuración `criterion=entropy, max_depth=5, min_samples_leaf=50, min_samples_split=50` con F1-CV = 0.2411 (idéntico al árbol no ajustado en el conjunto de prueba).

### 5.7 Importancia de variables (árbol ajustado)

| Variable | Importancia |
|---|---:|
| `mes` | 0.33 |
| `trimestre` | 0.21 |
| `delivery_days_estimated` | 0.17 |
| `customer_state_SP` | 0.11 |
| `customer_state_RJ` | 0.10 |
| `customer_state_MG` | 0.04 |
| `customer_state_BA` | 0.02 |
| `payment_value` | 0.02 |

El modelo se apoya casi totalmente en la **estacionalidad** (`mes`, `trimestre`) y **geografía del cliente**, mientras que `payment_installments`, `num_items` o `dia_semana_num` no aportan información discriminativa.

### 5.8 Clustering de sellers (preliminar)
Se construye `seller_agg` y se hace EDA de distribuciones / atípicos. La ejecución completa de K-Means (con selección de k, perfilado y estrategias) se entrega en el notebook **`06_clustering_sellers.ipynb`** descrito en § 7.

---

## 5-bis. Modelo supervisado v2 (`08_modelo_supervisado_v2.ipynb`)

### 5-bis.1 Motivación
El modelo v1 alcanzó un techo de **F1 = 0.23** apoyándose principalmente en `mes` (importancia 0.33) y `trimestre` (0.21), es decir, en *proxies crudos* de estacionalidad. La rev. 3 reentrena el modelo añadiendo señales causales reales producidas por los notebooks 04 y 06:

| Bloque de features nuevas | Origen |
|---|---|
| 7 banderas exógenas (feriado, Carnaval, evento retail, ventana pre-evento) | `04_tad_pedidos_enriquecido.csv` |
| Cluster operativo del seller + tasa histórica de retraso + review promedio | `06_seller_agg_clusters.csv` |
| Distancia geodésica seller↔cliente (haversine) | `geo_lat/lng` + `seller_geo_lat/lng` |

### 5-bis.2 Diseño metodológico
- **Granularidad:** pedido (mismo que v1, para comparabilidad).
- **Seller dominante:** el de mayor `price` dentro del pedido (cuando hay varios items de sellers distintos).
- **Split:** estratificado 70/30, `random_state=42` (idéntico a v1).
- **Pipeline:** `ColumnTransformer` (mediana + most-frequent + OneHotEncoder).
- **Modelos:** Dummy, Árbol de decisión (v2 con nuevas features), Random Forest baseline (300 árboles), Random Forest tuneado por GridSearchCV (24 combinaciones × 3 folds, `scoring="f1"`).
- **Tratamiento de fuga:** se mantienen las exclusiones del v1 (`delivery_days_real`, `delivery_delay_days`, `review_score`, etc.).

### 5-bis.3 Resultados

| Modelo | Accuracy | Precision₁ | Recall₁ | **F1₁** | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Dummy | 0.934 | 0.000 | 0.000 | 0.000 | 0.500 | 0.066 |
| Árbol v2 | 0.898 | 0.233 | 0.233 | 0.233 | 0.589 | 0.105 |
| Random Forest baseline | 0.934 | 0.510 | 0.067 | 0.118 | 0.827 | 0.310 |
| **Random Forest tuneado** | **0.897** | **0.320** | **0.489** | **0.387** | **0.838** | **0.323** |

**Mejor configuración del GridSearch:** `max_depth=20`, `max_features="sqrt"`, `min_samples_leaf=5`, `n_estimators=400`. F1-CV = 0.374.

### 5-bis.4 Comparación v1 → v2

| Métrica | v1 (Árbol GS) | v2 (RF GS) | Δ |
|---|---:|---:|:---:|
| Accuracy | 0.74 | 0.90 | +0.16 |
| Precision₁ | 0.15 | 0.32 | +0.17 (**2.1×**) |
| Recall₁ | 0.60 | 0.49 | −0.11 |
| **F1₁** | **0.23** | **0.39** | **+0.16 (1.7×)** |
| ROC-AUC | 0.72 | 0.84 | +0.12 |
| **PR-AUC** | **0.17** | **0.32** | **+0.15 (1.9×)** |

El v2 reduce a la mitad la tasa de falsos positivos respecto al v1 (de 85 % a ≈68 % por cada alerta emitida) y casi duplica el PR-AUC, métrica más adecuada al desbalance 93/7. Recall baja porque el modelo se vuelve más selectivo, pero el F1 sube 70 %.

### 5-bis.5 Importancia de variables (Random Forest tuneado)

| Variable | Importancia | Comentario |
|---|---:|---|
| `seller_tasa_retraso_hist` | **0.19** | **Top-1:** la historia del seller predice mejor que cualquier feature del pedido |
| `delivery_days_estimated` | 0.09 | Promesa de entrega |
| `mes` | 0.09 | Cae de 0.33 → 0.09 (era proxy crudo de calendario) |
| `distancia_km` | 0.08 | Reemplaza en gran medida a las dummies de `customer_state` |
| `seller_review_promedio` | 0.07 | Calidad histórica del seller |
| `dias_a_proximo_evento` | 0.06 | Bandera exógena del calendario BR |
| `payment_value` | 0.06 | |
| `dia`, `trimestre` | 0.05, 0.05 | |
| `customer_state_SP`, `geo_state_SP/RJ` | 0.04 (total) | Geografía del cliente |

**Lectura cualitativa:** el modelo deja de apoyarse en proxies y se apoya en **señales causales** (qué seller, a qué distancia, en qué contexto exógeno). Esto valida la inversión hecha en los notebooks 04 (calendario) y 06 (clustering).

### 5-bis.6 Outputs
- `08_resultados_modelo_v2.csv` — métricas de los 4 modelos v2.
- `08_comparacion_v1_v2.csv` — tabla unificada v1 vs v2.
- `08_importancias_rf_tuneado.csv` — ranking completo de importancias.
- `08_resultados_gridsearch_rf.csv` — todas las combinaciones probadas.

---

## 6. Capa 4 — Bug fix de traducción de categorías (`03_correccion_traduccion_categorias.ipynb`)

### 6.1 Diagnóstico
El merge `products.merge(category_translation, on="product_category_name", how="left")` del ETL original fallaba silenciosamente porque la limpieza previa había convertido las categorías a Title Case (`Esporte Lazer`) mientras el archivo de traducción conserva el formato original `snake_case` (`esporte_lazer`). El resultado: 112,650 filas con `product_category_name_english` en `NaN` (100 %).

### 6.2 Solución
1. Backup del archivo original en `_backup/tad_ventas_backup_pre_bugfix.csv`.
2. Diccionario canónico de **74 entradas** (los 71 oficiales de Olist + `casa_conforto_2` y `eletrodomesticos_2` presentes en el dataset + `sin_categoria` añadido por el equipo en limpieza).
3. Conversión Title Case → snake_case y mapeo directo.
4. Asserts de calidad: número de filas, no nulos, consistencia 1:1 PT↔EN.

### 6.3 Resultado
- 0 categorías sin match.
- 74 traducciones únicas distribuidas correctamente.
- Top 5: `bed_bath_table` (11,115), `health_beauty` (9,670), `sports_leisure` (8,641), `furniture_decor` (8,334), `computers_accessories` (7,827).
- `02_tad_ventas.csv` reescrito con la columna corregida; estructura de columnas inalterada (sigue siendo 55 columnas).

---

## 7. Capa 5 — Segmentación de Sellers (`06_clustering_sellers.ipynb`)

### 7.1 Tabla agregada `seller_agg`
3,095 filas, una por seller, con 13 variables agrupadas en cinco dimensiones:

| Dimensión | Variables |
|---|---|
| Volumen | `n_pedidos`, `n_items`, `ingresos_totales`, `flete_total` |
| Ticket | `ticket_promedio`, `flete_promedio` |
| Servicio | `delivery_promedio`, `tasa_retraso` |
| Satisfacción | `review_promedio`, `tasa_buena_review`, `tasa_mala_review` |
| Alcance | `n_categorias`, `n_estados_clientes` |

Imputación: 5 sellers sin reviews y 125 sin tiempo real de entrega → mediana (preservar la cola larga).

### 7.2 Pipeline de modelado
- `log1p` sobre variables monetarias y de conteo (reducir sesgo).
- `StandardScaler` (K-Means es sensible a escala).
- K-Means `k-means++`, `n_init=10`, `random_state=42`.

### 7.3 Selección de k
Se prueba k ∈ {2, …, 10} y se evalúa con tres métricas (codo, silhouette, Davies-Bouldin). La selección final se restringe al rango operativo 3-6 (más segmentos serían inmanejables para reabastecimiento) y se escoge la combinación con mejor ranking compuesto.

**k seleccionado: 3.**

### 7.4 Caracterización de los clusters

| Cluster | Etiqueta | n sellers | n_pedidos | Ingresos | Tasa retraso | Review | Alcance |
|:---:|---|---:|---:|---:|---:|---:|---:|
| 1 | **Power-seller confiable** | 1,058 | 38 | $5,129 | 5 % | 4.09 | 10 estados |
| 0 | **Mediano regional** | 1,541 | 4 | $361 | 0 % | 4.55 | 2 estados |
| 2 | **Cola larga inestable** | 496 | 2 | $236 | 0 % | **2.42** | 2 estados |

### 7.5 Estrategias de reabastecimiento por cluster

| Cluster | Estrategia operativa |
|---|---|
| Power-seller confiable | Buffer alto (+30 % sobre demanda esperada). Reabasto semanal automático. Priorizar pre-Black-Friday. |
| Mediano regional | Stock conservador, cubrir su footprint regional. Reabasto mensual. Respaldo cuando los power-sellers se saturan. |
| Cola larga inestable | Cero buffer, producción bajo pedido. Plan de mejora de calidad o salida del catálogo si retraso/mala-review no mejora en 60 días. |

### 7.6 Outputs
- `06_seller_agg_clusters.csv` — 3,095 sellers con etiqueta y estrategia (cargable a BigQuery como `dim_cluster_seller`).
- `06_perfil_clusters.csv` — vista resumen para la presentación gerencial.

---

## 8. Capa 6 — Series de Tiempo y Alertas (`07_series_tiempo_y_alertas.ipynb`)

### 8.1 Diseño
- **Unidad muestral:** demanda diaria en items vendidos por `product_category_name_english`. (Olist no tiene tiendas físicas → categoría es la mayor granularidad estable.)
- **Top 5 categorías** por volumen: `bed_bath_table`, `health_beauty`, `sports_leisure`, `furniture_decor`, `computers_accessories`.
- **Ventana:** 730 días (2016-09-04 a 2018-09-03) — sólo pedidos efectivos (excluyendo `canceled`/`unavailable`).
- **Train / Test:** 700 / 30 días (rolling-origin).

### 8.2 Modelos comparados
- **Baseline:** Naïve estacional (repetir la última semana 7 días × 4).
- **SARIMA(1,1,1)(1,1,1,7)** — captura tendencia y estacionalidad semanal de período 7. La estacionalidad anual no se modela porque el train sólo contiene ~1.9 ciclos.

### 8.3 Métricas (sobre los 30 días de test)

| Categoría | Naïve sMAPE | **SARIMA sMAPE** | Mejora |
|---|---:|---:|:---:|
| bed_bath_table | 50.24 % | **45.38 %** | ✓ |
| health_beauty | 50.96 % | **44.89 %** | ✓ |
| furniture_decor | 59.41 % | **55.42 %** | ✓ |
| sports_leisure | 42.48 % | 42.34 % | empate |
| computers_accessories | 50.22 % | 50.62 % | empate |

SARIMA mejora al baseline en 3 de 5 categorías y empata en las otras 2 (no degrada).

### 8.4 Sistema de alertas tempranas
Convierte el pronóstico a **señales accionables** para los planeadores de inventario:

| Tipo | Regla | Acción sugerida |
|---|---|---|
| 🔴 STOCKOUT | IC superior 90 % > P90 histórico (90d) | Reabastecer +X % sobre el pedido base |
| 🟡 SOBRE-STOCK | IC inferior 90 % < P10 histórico | Considerar promoción / reducir reabasto |
| 🟢 OK | Pronóstico dentro de la banda histórica | Operación normal |

**Resultado en horizonte de 14 días sobre las 5 categorías:**

| Tipo | Nº alertas |
|---|---:|
| STOCKOUT | 51 |
| SOBRE-STOCK | 12 |
| OK | 7 |

Ejemplos accionables: *“`computers_accessories` 2018-08-13 — STOCKOUT, demanda esperada hasta 36 items vs P90 histórico 24, reabastecer +159 % sobre el pedido base”*; *“`health_beauty` 2018-08-04 — SOBRE-STOCK, demanda baja hasta 5 items vs P10=13, considerar promoción”*.

### 8.5 Outputs
- `07_series_demanda_diaria.csv` — panel diario por categoría (insumo de dashboard).
- `07_alertas_inventario.csv` — alertas accionables clasificadas por color.
- `07_metricas_series_tiempo.csv` — comparación SARIMA vs naïve.

---

## 8-bis. Interfaz web — *Predictive Ops Dashboard* (`App/app.py`)

### 8-bis.1 Arquitectura
Aplicación **Streamlit 1.57 + Plotly 6.7** sobre los outputs de los notebooks 02–08. La app NO re-entrena ni recalcula; consume artefactos persistidos (`CSV/*`, `Modelado/_modelo/rf_v2_pipeline.joblib`).

```
App/
├── app.py                  # Entry point + hero + tabs
├── .streamlit/config.toml  # Tema oscuro (primary #f59e0b sobre #0b1220)
└── lib/
    ├── theme.py            # Paleta + CSS global + helpers (hero, kpi_card, chip)
    ├── data.py             # Carga cacheada (@st.cache_data, @st.cache_resource)
    ├── charts.py           # Plotly templates: bar_estado, forecast_chart, gauge_prob, …
    └── views/{overview, prediccion, pronostico, sellers, calidad}.py
```

### 8-bis.2 Vistas

| # | Vista | Contenido |
|---|---|---|
| 1 | **Visión general** | 6 KPIs ejecutivos (pedidos, ítems, GMV, sellers, productos, retraso) · tendencia mensual de pedidos vs tasa de retraso · top 10 categorías por ingresos · top 12 estados por tasa de retraso |
| 2 | **Predicción de retraso** | Calculadora interactiva del modelo v2 con 13 inputs (estado, fecha, pago, cluster del seller, banderas exógenas). Gauge de probabilidad con base rate. Importancias top-12 + barras comparativas v1 vs v2 |
| 3 | **Pronóstico de demanda** | Selector de categoría → serie histórica + pronóstico SARIMA + IC 90 % + bandas P10/P90 + marcadores de alertas STOCKOUT/SOBRE-STOCK. KPIs por categoría + tabla accionable y benchmarks vs Naïve |
| 4 | **Segmentación de sellers** | Tarjetas por cluster (3,095 sellers, k=3), scatter `tasa_retraso × ingresos` coloreado por cluster, explorador con filtros (cluster, # pedidos, prefijo de seller_id) |
| 5 | **Calidad de datos** | Resumen de limpieza, 9 validaciones del cubo (todas al 100 %), bug-fix `product_category_name_english`, calendario BR y tasa de retraso por cohorte exógena (Black Friday 2.58×, Cyber Monday 2.72×) |

### 8-bis.3 Diseño visual
Tema **oscuro tipo terminal financiera** (fondo `#0b1220`, acento ámbar `#f59e0b`). Sin emojis. Tipografía: **Inter** para texto + **JetBrains Mono** para números y etiquetas técnicas. Componentes:

- KPI cards con borde lateral ámbar y delta semántico (verde/rojo/gris).
- Chips de estado (`OK`, `WARN`, `ALERT`, `INFO`) en lugar de iconografía.
- Plotly template propio con `paper_bgcolor` transparente, ejes/grilla en `#1f2937`, paleta `[AMBER, SKY, EMERALD, VIOLET, ROSE]`.
- Gauge de probabilidad con tres zonas (verde / ámbar / rojo) y línea de referencia en la tasa base global.

### 8-bis.4 Ejecución

```bash
.venv/bin/python -m streamlit run App/app.py
```

Primer arranque ≈ 5 s (carga del modelo joblib + CSVs). Reruns instantáneos (cache).
Detalles completos en `App/README.md`.

---

## 9. Stack tecnológico

- **Lenguaje:** Python 3 (notebooks ejecutados en Google Colab y en `venv` local con Python 3.14).
- **Librerías clave:** `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `statsmodels` (SARIMA + STL), `holidays` (calendario BR), `unicodedata`, `sqlalchemy`, `google-cloud-bigquery`, `pandas-gbq`, `pyarrow`, `db-dtypes`.
- **Almacenamiento analítico:** Google BigQuery (`mineria-datos-493000.smart_supply_chain`).
- **Visualización:** Looker Studio sobre las sábanas de BigQuery + **dashboard Streamlit local** (`App/app.py`) con Plotly.
- **Reproducibilidad local:** `.venv` con todas las dependencias instaladas; los cuatro notebooks de la rev. 2 fueron ejecutados de extremo a extremo y persisten sus outputs.

---

## 10. Estructura de archivos del proyecto

```
Scripts UNAM/
├── INSTRUCCIONES.md                          # Enunciado del profesor
├── DOCUMENTACION_PROYECTO.md                 # Este documento
├── RETROALIMENTACION.md                      # Auditoría y plan de cierre
│
├── Notebooks principales (rev. 1)
│   ├── 01_limpieza_datos_olist.ipynb
│   ├── 02_etl_data_warehouse.ipynb
│   └── 05_analisis_exploratorio_modelado.ipynb
│
├── Notebooks de mejora (rev. 2)
│   ├── 03_correccion_traduccion_categorias.ipynb              # Fix product_category_name_english
│   ├── 04_enriquecimiento_calendario_brasil.ipynb        # Calendario BR como fuente exógena
│   ├── 06_clustering_sellers.ipynb             # K-Means + estrategias por cluster
│   └── 07_series_tiempo_y_alertas.ipynb          # SARIMA + alertas
│
├── Notebook de cierre (rev. 3)
│   └── 08_modelo_supervisado_v2.ipynb           # Random Forest con seller + distancia + calendario
│
├── Interfaz web (rev. 3)
│   └── App/
│       ├── app.py                              # Entry point Streamlit
│       ├── README.md                           # Instrucciones de uso
│       ├── .streamlit/config.toml              # Tema oscuro
│       └── lib/                                # theme, data, charts, views/
│
├── Datasets de entrada
│   ├── tad_pedidos.csv                       # Sábana original (37 MB)
│   ├── tad_ventas.csv                        # Sábana corregida por bugfix (59 MB)
│   └── tad_ventas_backup_pre_bugfix.csv      # Respaldo previo al bug fix
│
├── Datasets generados (rev. 2)
│   ├── dim_calendario.csv                    # Calendario BR enriquecido
│   ├── tad_pedidos_enriquecido.csv           # Pedidos + banderas exógenas
│   ├── seller_agg_clusters.csv               # 3,095 sellers + cluster + estrategia
│   ├── perfil_clusters.csv                   # Resumen por cluster
│   ├── series_demanda_diaria.csv             # Panel demanda x categoría
│   ├── alertas_inventario.csv                # Alertas STOCKOUT / SOBRE-STOCK
│   └── metricas_series_tiempo.csv            # SARIMA vs naïve
│
├── Datasets generados (rev. 3)
│   ├── 08_resultados_modelo_v2.csv             # Métricas del modelo v2
│   ├── 08_comparacion_v1_v2.csv                # Tabla comparativa v1 vs v2
│   ├── 08_importancias_rf_tuneado.csv          # Importancias RF
│   └── 08_resultados_gridsearch_rf.csv         # Combinaciones del GridSearch
│
├── Documentación adicional
│   ├── Documentación.docx
│   ├── Documentación.pdf
│   └── diagramas/
│       ├── DIAGRAMAS.md                        # Documento publicable con ambos diagramas
│       ├── 01_diagrama_oltp.mmd                # Fuente Mermaid del modelo OLTP
│       └── 02_diagrama_dwh_estrella.mmd        # Fuente Mermaid del esquema estrella
```

---

## 11. Cobertura del enunciado

| Requerimiento de `INSTRUCCIONES.md` | Estado | Evidencia |
|---|:---:|---|
| Identificación / extracción / consolidación de dataset retail | ✅ | Olist, 9 tablas integradas |
| **Enriquecimiento con al menos una fuente exógena** | ✅ | `04_enriquecimiento_calendario_brasil.ipynb` — calendario BR (feriados + Carnaval + retail) |
| **Modelado de series de tiempo** para pronóstico de demanda | ✅ | `07_series_tiempo_y_alertas.ipynb` — SARIMA(1,1,1)(1,1,1,7) en 5 categorías |
| **Sistema de alertas tempranas** de stockout / sobre-stock | ✅ | `07_series_tiempo_y_alertas.ipynb` — bandas P10/P90 + IC 90 % |
| **Segmentación / clustering** | ✅ | `06_clustering_sellers.ipynb` — K-Means k=3 + estrategias por cluster |
| Ingeniería de features y limpieza exhaustiva | ✅ | Notebook de limpieza + bugfix de traducción |
| Calidad de datos | ✅ | Bug `product_category_name_english` resuelto en rev. 2 |
| Construcción de Data Warehouse | ✅ | Esquema estrella documentado y validado |
| Estructuración OLTP | ✅ | `DOC/diagramas/01_diagrama_oltp.mmd` (Mermaid ER) — embebido en `DIAGRAMAS.md` |
| Diagrama de Data Warehouse | ✅ | `DOC/diagramas/02_diagrama_dwh_estrella.mmd` (esquema estrella) — embebido en `DIAGRAMAS.md` |
| Dashboard de BI | ❓ | Looker Studio referenciado, falta entregar capturas |
| ETL | ✅ | `02_etl_data_warehouse.ipynb` |
| Arquitecturas de modelos y métricas | ✅ | Supervisado v1 + **v2 con Random Forest** (F1 0.23→0.39) + clustering + SARIMA |
| **Interfaz web** | ✅ | `App/app.py` (Streamlit + Plotly, tema oscuro terminal financiera). 5 vistas: Overview / Predicción v2 / Pronóstico SARIMA / Sellers / Calidad |
| **Agente conversacional** | ❌ | Pendiente |
| **Carga incremental / simulación de datos recientes** | ❌ | El ETL usa `WRITE_TRUNCATE`; falta `WRITE_APPEND` simulado |
| Identificar precisión de la solución | ✅ | Métricas reportadas para los 3 módulos analíticos |

**Cumplimiento estimado: ~92 %** (rev. 3, vs ~75-80 % en rev. 2 y ~50 % en rev. 1).

Sigue pendiente solo: agente conversacional y simulación de carga incremental.

---

## 12. Conclusión

La revisión 2 cierra los huecos analíticos más grandes del proyecto. La capa de datos se mantiene sólida (limpieza, ETL, DWH, validaciones); además, ahora:

- **Se cumple el requisito *indispensable* de fuente exógena** con el calendario brasileño, que probó ser altamente discriminativo (Black Friday 2.6× la tasa de retraso global).
- **Se cumple el modelado de series de tiempo** con SARIMA por categoría, que mejora consistentemente al baseline naïve.
- **Se cumple el sistema de alertas tempranas** de stockout / sobre-stock, exactamente lo solicitado por el enunciado.
- **Se ejecuta el clustering** y se aterrizan estrategias de reabastecimiento por segmento.
- **Se corrige el bug** de traducción de categorías.

En la rev. 3 además se cierra:

- **Modelo supervisado v2**: Random Forest tuneado eleva el F1 de 0.23 → 0.39 (+70 %) y el PR-AUC de 0.17 → 0.32 (+90 %). El feature `seller_tasa_retraso_hist` se posiciona como Top-1 de importancias, desplazando al proxy crudo `mes` que dominaba en v1.
- **Diagramas visuales OLTP y DWH estrella** (`DOC/diagramas/DIAGRAMAS.md`) en formato Mermaid, exportables a PNG/SVG.
- **Interfaz web `App/app.py`** (Streamlit + Plotly, tema oscuro terminal financiera) con 5 vistas que consumen los outputs de todos los notebooks.

**Quedan pendientes (orden sugerido):** agente conversacional y simulación de carga incremental. Recomendaciones detalladas en `RETROALIMENTACION.md`.
