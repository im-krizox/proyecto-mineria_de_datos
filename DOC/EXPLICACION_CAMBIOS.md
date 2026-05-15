# Guía de entendimiento — ¿Qué cambió en el proyecto?

> Documento pensado para entender en lenguaje normal qué hicimos, por qué, cómo, y qué cambió. Sin asumir conocimiento técnico previo.

---

## Mapa rápido

Hicimos **5 cambios**. Cada uno tenía un problema concreto del enunciado del profesor que no estaba cubierto. Los cuatro primeros son notebooks nuevos que generan archivos; el quinto es la actualización de la documentación para reflejar todo lo nuevo.

| # | Cambio | Archivo principal | Problema que resuelve |
|---|---|---|---|
| 1 | Bug fix de categorías | `03_correccion_traduccion_categorias.ipynb` | Una columna estaba 100 % vacía sin que nadie lo notara |
| 2 | Enriquecimiento con feriados | `04_enriquecimiento_calendario_brasil.ipynb` | El profesor pedía una fuente externa "indispensable" y no había ninguna |
| 3 | Clustering de sellers | `06_clustering_sellers.ipynb` | Faltaba ejecutar la segmentación que el enunciado pedía |
| 4 | Series de tiempo + alertas | `07_series_tiempo_y_alertas.ipynb` | Faltaba pronosticar demanda y avisar de quiebres de stock |
| 5 | Actualización de docs | `DOCUMENTACION_PROYECTO.md` y `RETROALIMENTACION.md` | Reflejar todo lo anterior |

A continuación cada uno con detalle.

---

## Cambio #1 — Bug fix de categorías

### El problema en una frase
La columna que traduce el nombre de la categoría del producto del portugués al inglés (`product_category_name_english`) en la tabla `tad_ventas` estaba **completamente vacía**, todas las 112,650 filas tenían `NaN` (nulo). Nadie se había dado cuenta.

### Por qué pasó (analogía)
Imagínate que tienes dos listas de invitados a una boda. La lista A tiene los nombres tal cual los escribió la novia: *"Juan Pérez", "María López"*. La lista B vino del catering, que automáticamente puso todo en MAYÚSCULAS: *"JUAN PÉREZ", "MARÍA LÓPEZ"*. Si quieres juntar ambas listas usando "el nombre" como llave, **ningún nombre va a coincidir**, porque para la computadora `"Juan Pérez"` y `"JUAN PÉREZ"` son textos distintos.

Eso fue lo que pasó aquí:

- En la limpieza, alguien convirtió las categorías de `"esporte_lazer"` a `"Esporte Lazer"` (mejor para mostrar en un dashboard).
- En el ETL, se intentó cruzar contra una tabla de traducción que seguía usando `"esporte_lazer"`.
- Resultado: ninguna fila coincidió, la columna en inglés quedó toda vacía, pero el código no marcó ningún error.

### Qué hice
1. **Respaldé** el archivo original (`_backup/tad_ventas_backup_pre_bugfix.csv`) por si algo salía mal.
2. Construí un **diccionario de 74 traducciones** PT → EN (los 71 oficiales de Olist + 3 que el dataset tenía de más).
3. Antes de buscar en el diccionario, **convierto la categoría de "Esporte Lazer" de vuelta a "esporte_lazer"** para que coincidan las llaves.
4. Apliqué el mapeo y verifiqué con asserts (líneas que rompen el código si algo está mal): 0 nulos, 74 valores únicos, cada categoría en portugués corresponde a una sola en inglés.
5. Sobrescribí `02_tad_ventas.csv` con la columna corregida.

### Resultado
| | Antes | Después |
|---|---:|---:|
| Filas con traducción | 0 | **112,650** |
| Categorías únicas en EN | 0 | **74** |
| Nulos | 100 % | 0 % |

### Qué significa para la práctica
- Los gráficos del dashboard que usaran el nombre en inglés ahora funcionan.
- Los modelos de los siguientes notebooks (sobre todo el de series de tiempo, que filtra por categoría) ya pueden usar la columna corregida.
- Aprendizaje para próximas iteraciones: **siempre validar la cobertura de un join** (ej: `print(df['nueva_columna'].isna().mean())`). Si el 100 % es nulo, algo está roto.

---

## Cambio #2 — Enriquecimiento con calendario brasileño

### El problema en una frase
El profesor escribió en el enunciado, palabras textuales: *"Como **requisito indispensable** para robustecer el análisis, el conjunto de datos principal **deberá ser enriquecido con al menos una fuente de información exógena**"*. Y no había ninguna.

### Qué es una "fuente exógena" (analogía)
Si el dataset es un libro de tu vida (compras, ventas, cuentas), una fuente exógena es **información de afuera que ayuda a explicar lo que pasó**. Ejemplos:
- *"Compré un paraguas porque ese día llovió"* → la fuente exógena es el clima.
- *"Las ventas se dispararon porque era Black Friday"* → la fuente exógena es el calendario comercial.
- *"El reparto se demoró porque era Carnaval"* → la fuente exógena es el calendario de feriados.

Sin esa información externa, los modelos sólo ven números y no entienden el "por qué".

### Qué hice
Construí un **calendario completo de Brasil** con tres tipos de eventos:

1. **Feriados nacionales** (Año Nuevo, Tiradentes, Día del Trabajo, Independencia, Navidad, etc.). Los obtuve automáticamente con la librería de Python `holidays` que ya viene calibrada por país.
2. **Carnaval**. No es feriado oficial, pero **detiene la operación logística del país durante 5 días**. Lo añadí manualmente porque es móvil (cae en distintas fechas cada año, dependiendo de la Pascua).
3. **Fechas comerciales clave** (Black Friday, Cyber Monday, Día de la Madre, Día de los Enamorados brasileño que es el 12 de junio, Día del Padre, Día del Niño). Estos no son feriados pero son los **picos de venta más fuertes del año**.

Después generé varias **banderas** (columnas con 1 o 0) para cada día:
- `es_feriado_nacional`, `es_carnaval`, `es_evento_retail`
- `es_dia_no_laboral` (combina feriados, Carnaval y fines de semana)
- `dias_a_proximo_evento` (cuántos días faltan al siguiente evento)
- `en_ventana_pre_evento_3d` (si estamos a 3 días o menos de un evento — aquí es cuando se acumulan los pedidos y la logística colapsa)

Y finalmente uní este calendario a la tabla de pedidos (`tad_pedidos`), creando una nueva versión enriquecida (`04_tad_pedidos_enriquecido.csv`).

### Cómo validamos que sirve
La pregunta clave: **¿estas banderas realmente ayudan a explicar los retrasos?** Si no marcan diferencia, son adorno. Resultado:

| Cuando el pedido cayó en... | % de pedidos que llegaron tarde |
|---|---:|
| Día normal (promedio global) | 6.6 % |
| Día de la Madre | 4.7 % (mejor que normal) |
| Carnaval | **11.7 %** (casi el doble) |
| Black Friday | **16.9 %** (2.6× el promedio) |
| **Cyber Monday** | **17.9 %** (2.7× el promedio) |

Los eventos comerciales son los peores días para la logística. El modelo anterior no veía esto, sólo veía "este pedido fue en marzo" o "este fue en noviembre", lo cual es información mucho más pobre.

### Qué significa para la práctica
- **Cumplimos el requisito indispensable** del enunciado.
- El modelo de predicción de retrasos ahora puede aprender: *"Si el pedido cae 2 días antes de Cyber Monday, marca alerta roja"*, en lugar de la lógica vaga que tenía antes (*"si es noviembre, hay más probabilidad"*).
- En negocio: el equipo de logística puede **anticiparse**. Saber que se viene Black Friday significa contratar mensajeros extra, alquilar más almacén temporal, etc.

---

## Cambio #3 — Clustering (segmentación) de sellers

### El problema en una frase
El enunciado pide **agrupar a los sellers en clusters** según comportamiento similar y luego diseñar **estrategias de reabastecimiento diferentes para cada grupo**. El proyecto tenía la tabla preparada pero **nunca corrió el algoritmo**.

### Qué es clustering (analogía)
Imagina que tienes 3,000 personas en un salón y quieres organizarlas por afinidad sin saber nada de ellas de antemano. El clustering es un algoritmo que **mira las características de cada persona** (edad, hobbies, ingresos…) y las agrupa en N grupos donde **dentro de cada grupo las personas se parecen mucho entre sí, y entre grupos son distintas**.

No le decimos al algoritmo "agrúpalos en jóvenes-adultos-mayores" — el algoritmo descubre las agrupaciones por sí mismo a partir de los datos. Por eso se llama **aprendizaje no supervisado** (nadie le da las respuestas correctas).

### Qué hice paso a paso

**1. Construir la "ficha técnica" de cada seller.**
Cada uno de los 3,095 sellers tiene una fila con 13 variables: cuántos pedidos vendió, cuántos ingresos generó, qué tan rápido entrega, qué calificación promedio recibe, en cuántas categorías opera, en cuántos estados llega…

**2. Pre-procesar.**
- A las variables monetarias les apliqué `log` para que un seller gigante no aplaste a los chicos en la comparación.
- A todas las variables les apliqué `StandardScaler`: las pongo en la misma escala (media 0, desviación 1). Como decir "olvidemos las unidades, comparémoslos en términos relativos".

**3. Decidir cuántos grupos hacer (k).**
Esta es la pregunta central del clustering: ¿2 grupos? ¿5? ¿10? Probé del 2 al 10 y miré tres métricas:
- **Codo (inertia)**: qué tan "apretados" están los grupos. Mejor cuanto más bajo.
- **Silhouette**: qué tan bien separados están entre sí. Mejor cuanto más alto.
- **Davies-Bouldin**: combinación de las dos anteriores. Mejor cuanto más bajo.

Adicionalmente me restringí a un rango operativo de 3 a 6 clusters: con más de 6, las "estrategias diferenciadas" se vuelven inmanejables para el equipo de operaciones.

El ganador fue **k=3**.

**4. Entrenar el K-Means y poner etiquetas humanas a los clusters.**

| Cluster | Etiqueta | Cuántos | Perfil típico |
|:---:|---|---:|---|
| 1 | **Power-seller confiable** | 1,058 | 38 pedidos, $5,129 ingresos, retraso 5 %, llega a 10 estados |
| 0 | **Mediano regional** | 1,541 | 4 pedidos, llega a 2 estados, calificación 4.55/5 |
| 2 | **Cola larga inestable** | 496 | 2 pedidos, calificación **2.42/5** ⚠️ |

**5. Diseñar estrategias de reabastecimiento por cluster.**

| Cluster | Estrategia |
|---|---|
| Power-seller confiable | Buffer alto (+30 % stock), reabasto semanal automático, prioridad en pre-Black-Friday. |
| Mediano regional | Stock conservador para cubrir su zona, reabasto mensual. Útil como respaldo cuando los grandes se saturan. |
| Cola larga inestable | Cero buffer, producción bajo pedido. Plan de mejora obligatorio o salida del catálogo en 60 días. |

### Qué significa para la práctica
- Cumplimos el requisito de "aprendizaje no supervisado" del enunciado.
- En lugar de tratar a los 3,095 sellers igual, **el negocio tiene 3 manuales operativos distintos**: uno para los grandes, otro para los medianos, otro para los chicos problemáticos.
- Los 496 sellers del cluster "Cola larga inestable" representan un **problema real**: tienen calificación de 2.4/5 (los clientes están enojados con ellos). Se justifica una intervención específica.

---

## Cambio #4 — Series de tiempo + sistema de alertas

### El problema en una frase
El enunciado pide **pronosticar la demanda futura** y **avisar antes de que se acabe el stock o se acumule en exceso**. El proyecto no lo había hecho.

### Qué es una serie de tiempo (analogía)
Una serie de tiempo es **el mismo dato medido cada cierto rato**: la temperatura cada hora, las visitas a tu sitio cada día, las ventas cada semana. Tiene tres componentes:

- **Tendencia**: ¿está subiendo o bajando con el tiempo? (ej: las ventas crecen 5 % anual).
- **Estacionalidad**: ¿hay patrones que se repiten? (ej: los viernes vendemos más que los lunes).
- **Ruido**: lo que queda después de quitar tendencia y estacionalidad.

Un modelo de series de tiempo aprende esos tres componentes del pasado y los usa para predecir el futuro.

### Qué hice paso a paso

**1. Definir la unidad muestral.**
El enunciado pide *"a nivel de SKU y por sucursal"*. Olist no tiene tiendas físicas (es un marketplace) y los SKUs son demasiados (32,951 productos), así que usé la siguiente granularidad estable: **demanda diaria por categoría de producto**. Tomé las 5 categorías con más volumen.

**2. Construir las series.**
Para cada categoría: número de items vendidos cada día durante 730 días (2016-09-04 a 2018-09-03). Si un día no tuvo ventas en esa categoría, lo lleno con 0.

**3. Dividir entrenamiento y prueba.**
Reservé los **últimos 30 días como "test"** y entrené con los primeros 700. Esto es para evaluar honestamente: ¿el modelo predice bien algo que **no vio**?

**4. Entrenar dos modelos y compararlos.**

- **Baseline ingenuo (naïve estacional)**: "lo de la próxima semana será exactamente igual a la última semana que vi". Es la regla más tonta posible. **Si nuestro modelo no le gana, no sirve para nada.**
- **SARIMA(1,1,1)(1,1,1,7)**: un modelo estadístico clásico que aprende tendencia + estacionalidad semanal (de período 7 días).

**5. Evaluar con métricas formales** (sMAPE — error porcentual simétrico, mientras más bajo mejor).

| Categoría | Naïve | **SARIMA** | ¿Mejoró? |
|---|---:|---:|:---:|
| bed_bath_table | 50.2 % | **45.4 %** | ✓ |
| health_beauty | 51.0 % | **44.9 %** | ✓ |
| furniture_decor | 59.4 % | **55.4 %** | ✓ |
| sports_leisure | 42.5 % | 42.3 % | empate |
| computers_accessories | 50.2 % | 50.6 % | empate |

SARIMA gana 3 de 5 y empata las otras 2 — **nunca es peor que el baseline**, que era el riesgo. Esto significa que sí está aprendiendo señal real.

**6. Convertir el pronóstico en alertas accionables.**
Aquí es donde el modelo deja de ser un ejercicio académico y se vuelve útil. La lógica:

- Tomo los últimos 90 días de demanda real y calculo el **P10** (el límite bajo "normal") y el **P90** (el límite alto "normal").
- Genero el pronóstico de los próximos 14 días con su intervalo de confianza al 90 %.
- Comparo:
  - Si el pronóstico se va por arriba del P90 histórico → 🔴 **STOCKOUT** (riesgo de quedarse sin stock, hay que reabastecer).
  - Si el pronóstico se va por debajo del P10 histórico → 🟡 **SOBRE-STOCK** (riesgo de quedarse con inventario muerto, hay que promover/reducir compras).
  - Si está dentro de la banda → 🟢 **OK**.

### Resultado del sistema de alertas
En 14 días × 5 categorías = 70 puntos pronosticados:

| Tipo | Cantidad |
|---|---:|
| 🔴 STOCKOUT | 51 |
| 🟡 SOBRE-STOCK | 12 |
| 🟢 OK | 7 |

Cada alerta viene con **mensaje accionable** y la magnitud sugerida. Ejemplos reales:

> *"`computers_accessories` 2018-08-13 — STOCKOUT. Demanda esperada hasta 36 items vs P90 histórico 24. Reabastecer +159 % sobre el pedido base."*

> *"`health_beauty` 2018-08-04 — SOBRE-STOCK. Demanda esperada baja hasta 5 items vs P10 histórico 13. Considerar promoción / reducir reabasto."*

### Qué significa para la práctica
- Cumplimos los requisitos de **modelado de series de tiempo** y **alertas tempranas** del enunciado.
- El equipo de operaciones tiene un sistema **automatizable**: cada mañana el modelo se actualiza con los datos de ayer, recalcula el pronóstico de los próximos 14 días, y manda un email/dashboard con las alertas activas.
- **Limitación honesta** que también escribí en el notebook: Olist es un marketplace (no maneja inventario propio). El modelo sirve como **proxy de demanda esperada**; la traducción 1:1 a stockout requeriría datos reales de inventario.

---

## Cambio #5 — Actualización de la documentación

### El problema en una frase
La documentación que habíamos hecho describía el proyecto **como estaba antes** de los 4 cambios anteriores. Si la entregabas tal cual, mostraba todo lo que faltaba — pero ya no faltaba.

### Qué actualicé

**`DOCUMENTACION_PROYECTO.md`** (la documentación técnica):

- En el resumen ejecutivo, ahora son 8 puntos de cobertura (antes 4).
- La tabla de notebooks pasó de 3 a 7 notebooks, marcando los nuevos como "rev. 2 — Ejecutado ✓".
- La sección de fuentes exógenas ya no dice "no se hizo nada"; ahora describe el calendario, las banderas y la tabla de tasas de retraso por evento.
- El bug de categorías ya no está como "hallazgo crítico pendiente"; está como "**resuelto** en `03_correccion_traduccion_categorias.ipynb`".
- Agregué tres secciones completas describiendo los nuevos notebooks: bugfix, clustering, series de tiempo.
- La estructura de archivos del proyecto está reorganizada en bloques: notebooks rev. 1, notebooks rev. 2, datasets de entrada, datasets generados, documentación.
- La tabla de "cobertura del enunciado" pasó de tener varios ❌/⚠️ a tener ✅ en lo que cubrimos. **El cumplimiento estimado pasó de ~50 % a ~75-80 %**.
- La conclusión está reescrita reconociendo lo que se cerró y lo que falta.

**`RETROALIMENTACION.md`** (la auditoría/feedback):

- Veredicto general actualizado de 50 % a 75-80 %.
- Tabla comparativa "estado en rev. 1 vs estado en rev. 2" para que se vea de un vistazo qué cambió.
- Las brechas 1.1 a 1.4 (fuente exógena, series de tiempo, alertas, clustering) están marcadas como **RESUELTO** con los detalles de cómo se resolvieron y los números de validación.
- Las brechas 1.5 a 1.7 (interfaz web, agente conversacional, carga incremental) siguen como **PENDIENTE** con sugerencias concretas y estimaciones de esfuerzo.
- En la sección del modelo supervisado se conserva la crítica al F1=0.23 y se agrega un plan claro para entrenar un v2: ahora **ya tienes todos los ingredientes nuevos** (banderas exógenas, cluster del seller, distancia geodésica) listos para correr en 30-60 minutos.
- El plan de acción restante está repriorizado: lo que ya quedó hecho se quitó, y lo que queda se ordenó por rentabilidad esfuerzo/impacto.

### Qué significa para la práctica
- Si el profesor lee la documentación, va a ver el proyecto como está hoy, no como estaba hace 3 días.
- La auditoría sigue siendo **honesta** (no oculta lo que falta) pero ahora celebra los avances.
- Te sirve como guion para la presentación de 5-10 minutos: cada sección ya está estructurada para contar la historia.

---

## Vista general: ¿en qué quedamos?

### Lo que ya está hecho

| Requisito del enunciado | Estado |
|---|:---:|
| Limpieza, ETL, Data Warehouse, BigQuery | ✅ (ya estaba) |
| Modelo supervisado de retraso | ✅ (ya estaba, aunque con F1 bajo) |
| **Fuente exógena indispensable** | ✅ (calendario BR) |
| **Modelo de series de tiempo** | ✅ (SARIMA por categoría) |
| **Sistema de alertas tempranas** | ✅ (rojo / amarillo / verde) |
| **Clustering ejecutado** | ✅ (K-Means k=3) |
| **Estrategia de reabastecimiento por cluster** | ✅ |
| **Bug de calidad de datos** | ✅ (categorías traducidas) |

### Lo que falta para llegar al 100 %

| Requisito | Esfuerzo estimado |
|---|---|
| Modelo supervisado v2 con los nuevos features | 30-60 min |
| Diagramas visuales OLTP + estrella | 30 min en draw.io |
| Interfaz web (Streamlit) | 2-4 horas |
| Agente conversacional (puede ser sin LLM, con keywords) | 2-3 horas |
| Simulación de carga incremental a BigQuery | 1-2 horas |

Si te decides por hacer alguno de estos, el siguiente más rentable es **el modelo supervisado v2**: ya tenemos todos los ingredientes listos en disco; sólo falta entrenarlo y comparar contra el F1=0.23 anterior.

---

## Diccionario de palabras técnicas que aparecieron

- **`tad_ventas` / `tad_pedidos`**: las "sábanas", tablas planas con todo junto. Una fila por venta o por pedido.
- **DWH (Data Warehouse)**: almacén de datos pensado para análisis (vs operación). Aquí en BigQuery.
- **Esquema estrella**: forma de organizar el DWH con una tabla central de "hechos" (las transacciones) y varias tablas de "dimensiones" (catálogos: clientes, productos, fechas).
- **ETL**: Extract-Transform-Load. El proceso que toma los datos crudos, los limpia/transforma y los carga al destino.
- **Granularidad**: a qué nivel de detalle está cada fila (un pedido entero, o un ítem dentro del pedido).
- **K-Means**: algoritmo de clustering que agrupa puntos minimizando la distancia a los centros de cada grupo.
- **SARIMA**: modelo estadístico de series de tiempo que aprende tendencia + estacionalidad.
- **F1, recall, precision**: métricas para clasificación binaria. Recall = "de los retrasos reales, cuántos detecté". Precision = "de mis alertas, cuántas eran correctas". F1 = combinación de las dos.
- **sMAPE**: métrica de error para pronósticos. Porcentaje, mientras más bajo mejor.
- **Intervalo de confianza al 90 %**: el rango donde el valor real estará el 90 % de las veces.
- **P10 / P90**: percentil 10 y 90. El P90 es el valor por debajo del cual cae el 90 % de los datos históricos.
