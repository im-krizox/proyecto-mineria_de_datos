# Retroalimentación — *Smart Supply Chain*

**Materia:** Minería de Datos · **Grupo 2805**
**Profesor:** M. en IA Oscar Daniel Acosta González
**Fecha:** 15 de mayo de 2026 (rev. 3 — incluye refactor de cierre)
**Auditoría sobre:** `INSTRUCCIONES.md`, los tres notebooks originales más los cuatro notebooks de mejora (`03_correccion_traduccion_categorias`, `04_enriquecimiento_calendario_brasil`, `06_clustering_sellers`, `07_series_tiempo_y_alertas`).

---

## Veredicto general

**Cumplimiento global estimado: ~75-80 %.** (rev. 1: ~50 %)

La capa de datos sigue siendo **sólida** (limpieza + ETL + DWH validado + BigQuery). En esta revisión se cierran cuatro de las brechas más graves identificadas en la auditoría inicial:

| Brecha original | Estado en rev. 1 | Estado en rev. 2 |
|---|:---:|:---:|
| Fuente exógena (requisito *indispensable*) | ❌ | ✅ Calendario BR (feriados + Carnaval + retail) |
| Modelado de series de tiempo | ❌ | ✅ SARIMA por categoría (5 series) |
| Clustering ejecutado | ⚠️ EDA preliminar | ✅ K-Means k=3 + estrategias |
| Sistema de alertas tempranas | ❌ | ✅ STOCKOUT / SOBRE-STOCK con bandas P10/P90 |
| Bug de `product_category_name_english` | ❌ 100 % nula | ✅ 100 % cobertura |

**Lo que sigue pendiente:** agente conversacional, interfaz web (Streamlit), simulación de carga incremental, diagramas visuales OLTP / estrella.

A continuación se documenta cada brecha en orden de criticidad, indicando si fue resuelta y, si no, cómo cerrarla.

---

## 1. Brechas frente al enunciado

### 1.1 ✅ Fuente exógena — **RESUELTO** en `04_enriquecimiento_calendario_brasil.ipynb`

> *“Como requisito **indispensable** para robustecer el análisis, el conjunto de datos principal deberá ser enriquecido con **al menos una fuente de información exógena**.”* — INSTRUCCIONES.md

**Implementación:** calendario brasileño 2016-2018 (1,096 días) construido con la librería `holidays` (9 feriados nacionales) + reglas para Carnaval (móvil) + 6 fechas comerciales clave (Black Friday, Cyber Monday, Día de la Madre, Día de los Enamorados BR, Día del Padre, Día del Niño).

**Variables generadas:** `es_feriado_nacional`, `es_carnaval`, `es_evento_retail`, `es_dia_no_laboral`, `dias_a_proximo_evento`, `en_ventana_pre_evento_3d`, `en_ventana_pre_evento_7d`.

**Validación cuantitativa — son altamente discriminativas:**

| Cohorte | Tasa de retraso | × media |
|---|---:|---:|
| Media global | 6.57 % | 1.0 |
| Día de la Madre | 4.70 % | 0.7 |
| Día de los Enamorados | 4.57 % | 0.7 |
| Carnaval | 11.67 % | 1.78 |
| Día evento retail | 11.70 % | 1.78 |
| **Black Friday** | **16.92 %** | **2.58** |
| **Cyber Monday** | **17.87 %** | **2.72** |

**Outputs:** `04_dim_calendario.csv` (1,096 × 15) y `04_tad_pedidos_enriquecido.csv` (99,441 × 51).

> Sustituir el proxy crudo `mes` (importancia 0.33 en el árbol original) por estas banderas reales es lo que va a permitir que el modelo supervisado v2 supere a la versión 1.

### 1.2 ✅ Modelado de series de tiempo — **RESUELTO** en `07_series_tiempo_y_alertas.ipynb`

> *“Modelado de Series de Tiempo: pronosticar la demanda futura a nivel de SKU y por sucursal.”* — INSTRUCCIONES.md

**Implementación honesta:** Olist no tiene tiendas físicas ni inventario real, por lo que la unidad muestral viable es **demanda diaria por categoría** (no SKU-store-day). Se modelan las 5 categorías top por volumen.

**Modelo:** SARIMA(1,1,1)(1,1,1,7) — captura tendencia y estacionalidad semanal de período 7. La estacionalidad anual no se modela porque sólo hay ~1.9 ciclos anuales en el train.

**Validación contra baseline (sMAPE sobre últimos 30 días):**

| Categoría | Naïve estacional | **SARIMA** | Mejora |
|---|---:|---:|:---:|
| bed_bath_table | 50.24 % | **45.38 %** | ✓ |
| health_beauty | 50.96 % | **44.89 %** | ✓ |
| furniture_decor | 59.41 % | **55.42 %** | ✓ |
| sports_leisure | 42.48 % | 42.34 % | empate |
| computers_accessories | 50.22 % | 50.62 % | empate |

SARIMA gana 3 de 5 y empata en 2 (no degrada al baseline).

### 1.3 ✅ Sistema de alertas tempranas — **RESUELTO**

> *“Sistema de alertas tempranas que anticipe posibles quiebres de inventario (stockouts) o excesos de almacenamiento.”* — INSTRUCCIONES.md

**Implementación:** sobre el pronóstico SARIMA a 14 días, se compara el IC al 90 % contra los percentiles P10/P90 de la demanda histórica de los últimos 90 días.

| Color | Regla | Acción operativa |
|:---:|---|---|
| 🔴 STOCKOUT | IC sup > P90 hist | Reabastecer +X % sobre el pedido base |
| 🟡 SOBRE-STOCK | IC inf < P10 hist | Promoción / reducir reabasto |
| 🟢 OK | dentro de banda | Operación normal |

**Resultado en horizonte 14d × 5 categorías = 70 puntos:**

| Tipo | Cantidad |
|---|---:|
| STOCKOUT | 51 |
| SOBRE-STOCK | 12 |
| OK | 7 |

Cada alerta incluye **mensaje accionable** con la magnitud sugerida del ajuste. Ejemplo: *“`computers_accessories` 2018-08-13 STOCKOUT — demanda esperada hasta 36 items vs P90 hist 24, reabastecer +159 % sobre el pedido base”*.

### 1.4 ✅ Clustering de sellers — **RESUELTO** en `06_clustering_sellers.ipynb`

> *“Aplicación de algoritmos de aprendizaje no supervisado para identificar y agrupar… que exhiban comportamientos de rotación similares. Esto permitirá generar **estrategias de reabastecimiento parametrizadas por clúster**.”*

**Implementación:** K-Means sobre los 3,095 sellers con 13 variables agrupadas en 5 dimensiones (volumen, ticket, servicio, satisfacción, alcance). `log1p` sobre monetarias y `StandardScaler` para evitar dominio de variables de mayor magnitud.

**Selección de k:** método del codo + silhouette + Davies-Bouldin, restringida al rango operativo 3-6 (más segmentos serían inmanejables para reabastecimiento). **k seleccionado: 3.**

**Segmentos resultantes:**

| Cluster | Etiqueta | n sellers | Estrategia operativa |
|:---:|---|---:|---|
| 1 | **Power-seller confiable** | 1,058 | Buffer +30 %, reabasto semanal automático, prioridad pre-Black-Friday. |
| 0 | **Mediano regional** | 1,541 | Stock conservador, cubrir footprint regional, reabasto mensual. |
| 2 | **Cola larga inestable** | 496 | Cero buffer, producción bajo pedido. Plan de mejora o salida si retraso/mala-review no mejora en 60 días. |

### 1.5 ❌ Interfaz web — **PENDIENTE**

> *“Construcción de una interfaz web amigable y flexible…”*

**Sugerencia:** Streamlit (1 archivo `app.py`) con 3 pestañas:

1. **KPIs** — métricas globales sobre la sábana (pedidos, ingresos, tasa retraso por estado/mes).
2. **Predicción** — calculadora de retraso por pedido (input: estado, mes, payment_type, fecha; output: probabilidad y top variables).
3. **Pronóstico de demanda** — selector de categoría + gráfica del SARIMA + alertas activas.

Esfuerzo estimado: 2-4 horas. Lo puedo hacer en una iteración posterior si lo apruebas.

### 1.6 ❌ Agente conversacional — **PENDIENTE**

> *“Agente que les permita explorar la información y poder tomar decisiones en tiempo cercano al real.”*

**Sugerencia (sin LLM externo, costo cero):** intents por keywords en Python que mapean preguntas a queries pandas sobre las sábanas.

```python
# Ejemplos
"¿Cuál es la tasa de retraso en SP?"   → pandas filter + mean
"Sellers en cluster cola larga inestable" → filter
"¿Qué alertas hay para furniture decor?"  → lectura de alertas_inventario.csv
```

Versión avanzada: text-to-SQL contra BigQuery con LangChain `SQLDatabaseToolkit` o un LLM. Esfuerzo estimado: 2-3 horas sin LLM, 4-6 con LLM.

### 1.7 ❌ Simulación de carga incremental — **PENDIENTE**

> *“Consumir la información más reciente. Para este punto, en caso de que el dataset no lo permita, se debe de simular la carga de datos cada cierto tiempo.”*

El cargador a BigQuery actual usa `WRITE_TRUNCATE` (reescritura total). Para cumplir el requisito:

1. Agregar columna `etl_loaded_at = pd.Timestamp.now()` a la sábana.
2. Cambiar a `WRITE_APPEND` y ejecutar el ETL sólo sobre filas con `order_purchase_timestamp >= ultima_carga`.
3. Programación con cron / Cloud Scheduler / Airflow (en local: `crontab -e` con un script Python).

Esfuerzo estimado: 1-2 horas.

---

## 2. Calidad metodológica del modelado supervisado

### 2.1 Resultados crudos de la rev. 1

| Modelo | Recall₁ | Precision₁ | F1₁ |
|---|---:|---:|---:|
| Árbol | 0.60 | 0.15 | 0.23 |
| Reg. logística | 0.65 | 0.12 | 0.20 |
| Árbol ajustado | 0.60 | 0.15 | 0.23 |

**Lectura honesta:** el árbol detecta 60 % de los pedidos que sí van a llegar tarde, pero por cada 100 alertas que emite **sólo 15 son correctas**. Para un sistema operacional, esto generaría 85 % de falsos positivos, lo cual es operativamente costoso.

### 2.2 La hiperparametrización **no mejoró nada** (rev. 1)
El árbol ajustado por `GridSearchCV` (90 combinaciones) entrega **exactamente las mismas métricas** que el árbol inicial: F1 = 0.2411 vs 0.2411 (CV), 0.23 vs 0.23 (test). Esto sugiere que el espacio de búsqueda y/o el set de variables limita el techo del modelo.

### 2.3 Plan para un modelo supervisado v2 (recomendado para rev. 3)

Ya hay todo lo necesario para entrenar un modelo nuevo con **chance real de mejorar el F1**:

1. **Dataset de entrenamiento ya enriquecido:** `04_tad_pedidos_enriquecido.csv` con las 7 banderas exógenas.
2. **Variables del seller que no se usaron** (calculables ahora con los outputs de la rev. 2):
   - Tasa histórica de retraso del seller (`06_seller_agg_clusters.csv` → `tasa_retraso`).
   - Etiqueta de cluster del seller (categórica de 3 valores).
   - Distancia geodésica seller↔cliente (con `geo_lat/geo_lng` ya disponibles en ambas tablas).
3. **Probar Random Forest y/o Gradient Boosting** si están vistos en clase. Random Forest es interpretable vía importancias.

Esfuerzo estimado: 30-60 minutos. **Es el siguiente entregable más rentable** porque está todo listo para correr.

### 2.4 Punto a favor: tratamiento de fuga de información
El equipo identifica explícitamente y excluye variables conocidas post-entrega (`delivery_days_real`, `delivery_delay_days`, `review_score`). Esto está bien hecho y conviene mantenerlo en v2.

---

## 3. Bug de `product_category_name_english` — **RESUELTO** en `03_correccion_traduccion_categorias.ipynb`

**Causa raíz confirmada:** la limpieza convirtió las categorías a Title Case (`Esporte Lazer`) y el ETL hizo merge contra el archivo de traducción que conserva `snake_case` (`esporte_lazer`). Resultado: 0 matches, 100 % de la columna en NaN.

**Fix aplicado:**
- Diccionario canónico de **74 entradas** (los 71 oficiales + `casa_conforto_2`, `eletrodomesticos_2`, `sin_categoria`).
- Conversión Title Case → snake_case en el momento del lookup.
- Asserts de calidad: 0 nulos, 74 valores únicos, consistencia 1:1 PT↔EN.
- `02_tad_ventas.csv` reescrito; backup en `_backup/tad_ventas_backup_pre_bugfix.csv`.

**Recomendación complementaria:** en una versión definitiva del ETL, mover la transformación cosmética del nombre a una columna nueva (`product_category_display`) y conservar el `snake_case` original como llave de join, para evitar que vuelva a ocurrir.

---

## 4. Hallazgos menores

### 4.1 ✅ Integridad referencial `pago_key` — **RESUELTO**
Se añadió una fila sentinela `SIN_PAGO` (`pago_key=0`, `payment_type='sin_pago'`, `payment_installments=0`) a `dim_pago` y un `fillna(0)` post-merge en `base` que mapea los pedidos sin registro de pago a esa sentinela. La integridad referencial pasa de **99.91% → 100%** al re-ejecutar el ETL.

### 4.2 ✅ Rutas hardcodeadas — **RESUELTO**
Todos los notebooks leen desde rutas relativas configurables vía variables de entorno:
- `DATA_PATH` / `OUTPUT_PATH` en limpieza (default `../CSV/`).
- `CSV_DIR` en el resto (default `../CSV`).
- `SSC_CREDENTIALS` para el JSON de BigQuery (default `smart_supply_chain.json` en CWD).
Auth a GCP via Application Default Credentials.

### 4.3 ⚠️ Mezcla de notebooks en uno solo — **PARCIAL**
`01_limpieza_datos_olist.ipynb` sigue siendo seis sub-notebooks concatenados (84 celdas). No se refactorizó porque no es re-ejecutable en local sin recuperar los CSV crudos de Olist. `02_etl_data_warehouse.ipynb` sí se refactorizó: la antigua celda monolítica de ~566 líneas se partió en 10 sub-celdas con encabezados de sección (`### 1. Imports y carga` … `### 10. Exportación`).

### 4.4 Documentación generada al final del notebook de modelado
Todos los outputs de la etapa 05 ahora se persisten en `CSV/` con el prefijo `05_` (`05_resultados_modelos_final.csv`, `05_importancias_arbol_ajustado.csv`, etc.) para mantener la organización por etapa. Falta consolidarlos en un *artifact* único (PDF, HTML, o Looker Studio) para el entregable gerencial.

---

## 5. Cobertura del checklist de **Entregables Técnicos**

| Entregable | Estado | Comentario |
|---|:---:|---|
| Diagrama OLTP | ⚠️ | Verificar `Documentación.docx`. Si no, hacerlo en draw.io / dbdiagram.io. |
| Diagrama de Data Warehouse | ⚠️ | Implícito en código. Falta diagrama visual (estrella). |
| Dashboard de BI | ❓ | Looker Studio referenciado; falta link público o capturas. |
| Procesos ETL | ✅ | Bien documentados y validados. |
| Arquitecturas de modelos y métricas | ✅ | Supervisado, clustering y SARIMA todos documentados. |
| Agente conversacional | ❌ | Pendiente. |
| Interfaz de consumo | ❌ | Pendiente. |

---

## 6. Plan de acción restante (orden de prioridad)

| Prioridad | Tarea | Esfuerzo | Impacto |
|:---:|---|:---:|:---:|
| **P0** | Modelo supervisado v2 con `tad_pedidos_enriquecido` + cluster del seller + distancia | Bajo (30-60 min) | Alto — sube F1 esperado |
| **P0** | Diagramas OLTP + estrella en draw.io o dbdiagram.io | Bajo | Medio (presentación) |
| **P1** | Streamlit (KPIs / Predicción / Pronóstico) | Medio (2-4 h) | Alto — cumple requisito |
| **P1** | Agente conversacional (intents + pandas o BigQuery) | Medio | Alto — cumple requisito |
| **P1** | Simulación de carga incremental con `WRITE_APPEND` | Bajo | Medio |
| **P2** | Recargar `tad_ventas` y `dim_calendario` a BigQuery | Mínimo | Medio (consistencia) |
| **P2** | Consolidar todos los CSVs de outputs en un PDF de cierre | Bajo | Medio (gerencial) |

---

## 7. Lo bueno (no perder de vista)

- Limpieza por tabla **rigurosa, conservadora y bien justificada**.
- Validación del cubo **ejemplar**: unicidad, integridad referencial y conservación de montos comprobada con sumas exactas.
- Tratamiento explícito de **fuga de información** en el modelado supervisado.
- Evaluación con **métricas adecuadas al desbalance** (no se quedaron en accuracy).
- Estructura del notebook de EDA muy ordenada, con interpretación tras cada sección — exactamente lo que pide la consideración *“INTERPRETACIÓN y no solo lectura de estadígrafos”*.
- Los notebooks de la **rev. 2 mantienen el mismo estilo** (markdown explicativo + código + interpretación), conservando la coherencia narrativa del proyecto.

---

## 8. Riesgos remanentes para la entrega final

1. **El profesor todavía marcará como faltante**: agente conversacional, interfaz, simulación de carga. Son 3 entregables explícitos que conviene cerrar antes de la presentación.
2. **El F1 = 0.23 del modelo supervisado original** seguirá siendo cuestionado si no se entrena el v2 con los nuevos features (cluster de seller, banderas exógenas, distancia geodésica).
3. **Sin diagramas visuales**, la presentación gerencial pierde fuerza. Hacerlos toma 30 minutos en draw.io y suma mucho.
4. **Los outputs de la rev. 2 (`dim_calendario`, `seller_agg_clusters`, `alertas_inventario`) no están subidos a BigQuery**. Si el dashboard de Looker Studio se va a actualizar, hay que cargarlos antes de la presentación.
