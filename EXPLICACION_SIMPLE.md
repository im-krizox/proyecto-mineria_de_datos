# Explicación Simple — Proyecto *Smart Supply Chain*

> Este documento está escrito para alguien que **no sabe programar ni de ciencia de datos**.
> No vas a encontrar código. Vas a encontrar, en español llano y con analogías,
> qué hace cada pieza del proyecto y por qué existe.

---

## 0. La idea general en una frase

Tomamos los registros de ventas reales de una tienda en línea brasileña, los
**limpiamos**, los **ordenamos como en un almacén bien organizado**, y luego
construimos **cuatro "asesores automáticos"**: uno que avisa qué pedidos van a
llegar tarde, uno que predice cuánto se va a vender, uno que clasifica a los
vendedores por tipo, y un asistente con el que puedes conversar para preguntar
todo lo anterior. Todo se ve en una **página web** tipo tablero de control.

**Analogía del mundo real:** es como contratar a un equipo de consultores para
una tienda, pero en lugar de personas son programas. Uno revisa la bodega, otro
adivina las ventas del próximo mes, otro te dice qué proveedores son confiables
y cuáles no, y hay una recepcionista que responde tus preguntas sobre todo eso.

*Si alguien te pregunta por esto en una presentación, di:* "Construimos un
sistema completo que convierte los datos de ventas de una tienda en línea en
decisiones concretas sobre entregas, inventario y proveedores."

---

## 1. Los datos de origen — el dataset Olist

### ¿Qué problema resuelve?
Todo proyecto de datos necesita datos. Usamos un conjunto público y real
llamado **Olist**: el historial de una empresa brasileña de comercio
electrónico, con unos **100,000 pedidos** hechos entre 2016 y 2018.

### ¿Qué recibe y qué produce?
- **Entrada:** nueve archivos separados (clientes, pedidos, productos,
  vendedores, pagos, reseñas, ubicaciones, etc.). Son alrededor de 1.4 millones
  de filas en total.
- **Salida:** los mismos datos, pero ya entendidos y listos para trabajar.

### ¿Cómo encaja con el resto?
Es el punto de partida. Todo lo demás —limpieza, modelos, tablero— se construye
encima de estos archivos.

### Analogía
Es como recibir nueve cajas de recibos, facturas y notas sueltas de una tienda
que cerró. Antes de poder analizar nada, tienes que abrir las cajas y ver qué
hay dentro.

*Si alguien te pregunta por esto en una presentación, di:* "Partimos de un
dataset público real de e-commerce con 100,000 pedidos, lo que le da realismo
y credibilidad al proyecto."

---

## 2. Limpieza de datos (`01_limpieza_datos_olist.ipynb`)

### ¿Qué problema resuelve?
Los datos reales vienen sucios: nombres de ciudades mal escritos, fechas en
formato de texto, filas repetidas, casillas vacías, coordenadas imposibles
(ubicaciones que caen en el océano). Si trabajas con datos sucios, todas las
conclusiones salen mal.

### ¿Qué recibe y qué produce?
- **Entrada:** las nueve tablas crudas de Olist.
- **Salida:** las mismas nueve tablas, pero corregidas: sin duplicados, con
  fechas reales, textos normalizados y huecos rellenados de forma razonable.

### ¿Cómo encaja con el resto?
Es el cimiento. Ningún modelo posterior funcionaría bien sin este paso.

### Detalles que vale la pena conocer
- De **un millón de filas de ubicaciones** quedaron solo 19,010, porque la
  mayoría eran repeticiones del mismo código postal.
- Cuando faltaba un dato numérico, se rellenó con el **valor mediano** (el del
  medio), para no inventar números extremos.
- Los errores que *no* se podían arreglar no se borraron: se les puso una
  **"bandera"** (una marca) para recordar que ese dato es sospechoso.

### Analogía
Es como cuando heredas la contabilidad de un negocio en hojas sueltas: pasas
todo en limpio a un cuaderno, juntas las hojas repetidas, corriges los nombres
mal escritos y, donde falta un número, pones el más típico en lugar de dejar el
hueco.

*Si alguien te pregunta por esto en una presentación, di:* "Dedicamos un módulo
entero solo a limpiar los datos, porque un análisis sobre datos sucios produce
conclusiones equivocadas."

---

## 3. El almacén de datos — ETL y Data Warehouse (`02_etl_data_warehouse.ipynb`)

### ¿Qué problema resuelve?
Tener nueve tablas separadas es incómodo: para responder "¿cuánto vendió tal
producto en tal ciudad?" tendrías que cruzar varias a mano. Este paso
**reorganiza todo** en una estructura pensada para hacer preguntas rápido.

### ¿Qué recibe y qué produce?
- **Entrada:** las nueve tablas ya limpias.
- **Salida:**
  - Un **"esquema estrella"**: una tabla central de hechos (cada venta) rodeada
    de tablas satélite que describen el cliente, el producto, el vendedor, la
    fecha, el pago y la ubicación.
  - Dos **tablas planas grandes** ("sábanas"): `tad_pedidos` (una fila por
    pedido) y `tad_ventas` (una fila por producto vendido). Todo junto, listo
    para analizar.
  - La carga de esas tablas en **Google BigQuery**, una base de datos en la
    nube.

### ¿Cómo encaja con el resto?
Es la "fuente única de verdad". Todos los modelos y el tablero leen de aquí.

### Una garantía importante
El proyecto **verifica que las cuentas cuadren**: la suma de todas las ventas
da exactamente $13.5 millones tanto en la tabla original como en la
reorganizada. Eso prueba que no se perdió ni se inventó dinero al reordenar.

### Analogía
Imagina pasar de tener recibos amontonados en cajas a montar un **archivero
ordenado**: una gaveta para clientes, otra para productos, otra para fechas. Y
antes de cerrar el archivero, cuentas el dinero dos veces para asegurarte de
que cuadra.

*Si alguien te pregunta por esto en una presentación, di:* "Organizamos los
datos en un almacén con forma de estrella y validamos que las sumas de dinero
cuadran al centavo, garantizando que la reorganización fue fiel."

---

## 4. Arreglo de un error de traducción (`03_correccion_traduccion_categorias.ipynb`)

### ¿Qué problema resuelve?
Las categorías de producto venían en portugués. Al traducirlas al inglés, un
detalle técnico hizo que la columna traducida quedara **completamente vacía**:
112,650 filas sin categoría en inglés. Era un error silencioso, nadie había
saltado una alarma.

### ¿Qué recibe y qué produce?
- **Entrada:** la tabla de ventas con la columna de categoría en inglés vacía.
- **Salida:** la misma tabla con las 74 categorías correctamente traducidas y
  cero huecos.

### ¿Cómo encaja con el resto?
Sin esta corrección, el pronóstico de demanda (que trabaja por categoría) no
tendría sobre qué agrupar.

### Analogía
Es como descubrir que la columna "categoría" de tu inventario quedó en blanco
porque la plantilla de traducción usaba mayúsculas y la tuya minúsculas. Aquí
se hizo un diccionario manual y se rellenó correctamente.

*Si alguien te pregunta por esto en una presentación, di:* "Detectamos y
corregimos un error de calidad de datos que dejaba sin categoría a todas las
ventas; mostrarlo demuestra rigor."

---

## 5. Enriquecimiento con el calendario brasileño (`04_enriquecimiento_calendario_brasil.ipynb`)

### ¿Qué problema resuelve?
Los datos de Olist no dicen nada sobre el contexto del país. Pero las entregas
se retrasan más en feriados, en Carnaval y en fechas de mucha compra como Black
Friday. Este módulo **añade información externa**: un calendario de Brasil con
todos esos eventos.

### ¿Qué recibe y qué produce?
- **Entrada:** la tabla de pedidos y un calendario de feriados de Brasil.
- **Salida:** la tabla de pedidos con marcas nuevas: "este pedido cayó en
  feriado", "cayó en Carnaval", "faltaban X días para un evento grande", etc.

### ¿Cómo encaja con el resto?
Estas marcas alimentan el modelo de predicción de retrasos (sección 7) y lo
hacen mucho más certero.

### El dato que más impresiona
Se comprobó que los pedidos de **Black Friday se retrasan 2.6 veces más** que
un día normal, y los de **Cyber Monday 2.7 veces más**. O sea: el calendario sí
explica retrasos.

### Analogía
Es como un repartidor que no solo mira la dirección, sino también el calendario:
sabe que entregar el día del Grito de Independencia o en plena Navidad es más
difícil. Le dimos al sistema esa misma "conciencia de las fechas".

*Si alguien te pregunta por esto en una presentación, di:* "Enriquecimos los
datos con el calendario de Brasil y comprobamos que en Black Friday los
retrasos se multiplican por 2.6 — un factor que el sistema ahora sí considera."

---

## 6. Predicción de retrasos en la entrega — modelo v1 (`05_analisis_exploratorio_modelado.ipynb`)

### ¿Qué problema resuelve?
La pregunta de negocio es: **¿este pedido va a llegar tarde?** Si pudiéramos
saberlo de antemano, la empresa podría adelantarse: avisar al cliente, usar otro
transportista, etc.

### ¿Qué recibe y qué produce?
- **Entrada:** las características de cada pedido (estado del cliente, fecha,
  forma de pago, etc.).
- **Salida:** una predicción "sí va tarde" / "no va tarde".

### ¿Cómo encaja con el resto?
Es la **primera versión** del modelo de retrasos. Funcionó regular y por eso se
construyó después una versión mejorada (sección 9).

### Las métricas, en términos de negocio
Solo el **6.6 % de los pedidos llegan tarde**. Eso hace el problema difícil:
buscar lo raro es como buscar una aguja en un pajar.

- Este primer modelo logró un **F1 de 0.23**. El F1 es una nota de 0 a 1 que
  mezcla dos cosas: cuántas alarmas son correctas y cuántos retrasos reales
  detecta. Un 0.23 es bajo: el modelo "huele" el problema pero falla mucho.
- En concreto: detectaba **6 de cada 10 retrasos reales** (bien), pero de cada
  100 alarmas que daba, **85 eran falsas** (mal). Demasiado ruido.

### Analogía
Es como un detector de humo demasiado nervioso: suena cuando hay fuego, pero
también cuando tuestas pan. Sirve, pero molesta tanto que la gente lo ignora.

*Si alguien te pregunta por esto en una presentación, di:* "La primera versión
del modelo detectaba retrasos pero daba demasiadas falsas alarmas, así que la
usamos como punto de partida para mejorarla."

---

## 7. Segmentación de vendedores (`06_clustering_sellers.ipynb`)

### ¿Qué problema resuelve?
Hay **3,095 vendedores** distintos. Tratarlos a todos igual sería un error: un
vendedor enorme y confiable no necesita la misma estrategia que uno pequeño y
problemático. Este módulo los **agrupa por parecido** automáticamente.

### ¿Qué recibe y qué produce?
- **Entrada:** un resumen de cada vendedor (cuánto vende, qué tan rápido
  entrega, qué calificación recibe, en cuántos estados opera, etc.).
- **Salida:** cada vendedor queda asignado a uno de **3 grupos**, con una
  estrategia de inventario recomendada para cada grupo.

### Los tres grupos encontrados
1. **Power-seller confiable** (1,058 vendedores): venden mucho, entregan bien,
   buena calificación. Estrategia: tener inventario de sobra para ellos.
2. **Mediano regional** (1,541): venden poco pero estables y bien calificados.
   Estrategia: inventario conservador.
3. **Cola larga inestable** (496): venden muy poco y con mala calificación
   (2.4 de 5). Estrategia: cero inventario adelantado; mejorar o sacar del
   catálogo.

### ¿Cómo encaja con el resto?
El grupo de cada vendedor se usa después como pista para el modelo mejorado de
retrasos (sección 9).

### Analogía
Es exactamente como **cuando Spotify arma playlists automáticamente**: nadie le
dijo cuáles eran los géneros; el programa notó que ciertas canciones se parecen
entre sí y las juntó. Aquí el programa notó que ciertos vendedores se parecen y
los juntó en 3 perfiles, sin que nadie le diera las etiquetas de antemano.

*Si alguien te pregunta por esto en una presentación, di:* "Agrupamos
automáticamente a los 3,095 vendedores en 3 perfiles y le dimos a cada perfil su
propia estrategia de inventario, en lugar de tratarlos a todos igual."

---

## 8. Pronóstico de demanda y alertas de inventario (`07_series_tiempo_y_alertas.ipynb`)

### ¿Qué problema resuelve?
Dos preguntas: **¿cuánto se va a vender de cada categoría las próximas
semanas?** y, sobre todo, **¿de qué me voy a quedar sin stock y de qué me va a
sobrar?**

### ¿Qué recibe y qué produce?
- **Entrada:** el historial diario de cuántos artículos se vendieron en cada una
  de las 5 categorías más vendidas.
- **Salida:**
  - Un pronóstico de los próximos días.
  - Una lista de **alertas con semáforo**: rojo = riesgo de quedarte sin stock,
    amarillo = te va a sobrar, verde = todo normal.

### Las métricas, en términos de negocio
- El modelo usado se llama **SARIMA**. Aprende dos cosas: la tendencia general y
  el ritmo semanal (se vende distinto en lunes que en sábado).
- Su error ronda el **45 %**. Suena alto, pero la demanda diaria de e-commerce
  es muy errática; lo importante es que **le gana al método ingenuo** de "la
  próxima semana será igual a la anterior" en la mayoría de las categorías.
- En un horizonte de 14 días, el sistema levantó **51 alertas de posible falta
  de stock**. Ejemplo real: "el 13 de agosto, accesorios de computadora — pedir
  159 % más de lo habitual".

### ¿Cómo encaja con el resto?
Es uno de los cuatro asesores. Sus alertas se ven en el tablero y el asistente
las puede consultar.

### Analogía
Es como el **pronóstico del clima, pero para tu bodega**. No te dice el número
exacto de ventas (igual que el clima no acierta los grados exactos), pero sí te
avisa "lleva paraguas" — es decir, "reabastece esta categoría, te vas a quedar
corto".

*Si alguien te pregunta por esto en una presentación, di:* "Hicimos un
pronóstico de demanda que se traduce en alertas de semáforo: rojo si te vas a
quedar sin stock, amarillo si te va a sobrar."

---

## 9. Modelo de retrasos mejorado — versión 2 (`08_modelo_supervisado_v2.ipynb`)

### ¿Qué problema resuelve?
El modelo v1 (sección 6) daba demasiadas falsas alarmas. Esta versión lo
**reconstruye** usando información mejor.

### ¿Qué cambió?
La clave fue **darle mejores pistas**:
- El **perfil del vendedor** y su historial de retrasos (de la sección 7).
- La **distancia** real entre el vendedor y el cliente.
- Las **marcas del calendario** (de la sección 5).

Y se cambió el tipo de modelo: de un solo "árbol de decisión" a un **Bosque
Aleatorio** (Random Forest), que es básicamente **cientos de árboles votando**.

### Las métricas, en términos de negocio
- El **F1 subió de 0.23 a 0.39**: una mejora del **70 %**.
- Las falsas alarmas bajaron: de 85 falsas por cada 100 alertas, a unas 68.
- El descubrimiento más interesante: lo que **mejor predice si un pedido llega
  tarde es el historial del propio vendedor**. Si un vendedor ha llegado tarde
  antes, probablemente lo vuelva a hacer.

### Analogía
El modelo v1 era un detector de humo nervioso. El v2 es como pasar de **un solo
médico dando un diagnóstico a una junta de cientos de médicos que votan**: el
consenso se equivoca menos. Y además le dimos al modelo el "expediente" de cada
vendedor, no solo los datos del pedido suelto.

*Si alguien te pregunta por esto en una presentación, di:* "Mejoramos el modelo
de retrasos un 70 % al darle el historial de cada vendedor y usar un Bosque
Aleatorio, que es como cientos de modelos votando en vez de uno solo."

---

## 10. El asistente conversacional (`App/lib/agent.py` + `App/lib/llm.py`)

### ¿Qué problema resuelve?
Todo lo anterior produce números y gráficas, pero un gerente no quiere bucear
en tablas: quiere **preguntar en español** "¿cuáles son mis peores vendedores?"
y recibir una respuesta clara.

### ¿Qué recibe y qué produce?
- **Entrada:** una pregunta escrita por el usuario.
- **Salida:** una respuesta en lenguaje de negocio, a veces acompañada de una
  tabla o una gráfica.

### Cómo funciona (tiene dos cerebros)
1. **Cerebro inteligente (LLM Gemini):** cuando escribes una pregunta libre, se
   le manda a un modelo de lenguaje de Google junto con un resumen de todos los
   datos del negocio. Él redacta la respuesta.
2. **Cerebro de reglas (de respaldo):** un sistema más simple que reconoce
   palabras clave. Se usa para los botones de sugerencias y, sobre todo, **si el
   cerebro inteligente falla o no está disponible**, para que el asistente nunca
   se quede mudo.

### Analogía
Es como una **recepcionista con un manual al lado**. Normalmente te responde con
naturalidad (el LLM). Pero si se queda sin internet, abre el manual de
preguntas frecuentes (las reglas) y aún así te atiende. Nunca te deja sin
respuesta.

*Si alguien te pregunta por esto en una presentación, di:* "Añadimos un
asistente con el que se conversa en español; usa inteligencia artificial para
responder y tiene un sistema de respaldo para no fallar nunca."

---

## 11. El tablero web (`App/app.py`)

### ¿Qué problema resuelve?
Reúne **todo el proyecto en una sola pantalla** que cualquiera puede usar sin
saber programar.

### ¿Qué recibe y qué produce?
- **Entrada:** los resultados ya calculados por los notebooks (archivos
  guardados; el tablero no recalcula nada, solo los muestra).
- **Salida:** una página web con 6 secciones navegables.

### Las 6 secciones
1. **Visión general:** los números clave del negocio.
2. **Predicción de retraso:** una calculadora donde metes los datos de un
   pedido y te dice la probabilidad de que llegue tarde.
3. **Pronóstico de demanda:** las gráficas de ventas futuras y las alertas.
4. **Segmentación de vendedores:** los 3 grupos y un explorador.
5. **Calidad de datos:** prueba de que la limpieza y las validaciones se
   hicieron bien.
6. **Asistente:** el chat de la sección 10.

### Analogía
Es el **tablero de un coche**: el motor (los modelos) hace el trabajo pesado por
debajo; el tablero solo te muestra de forma clara la velocidad, la gasolina y
las luces de advertencia para que tú decidas.

*Si alguien te pregunta por esto en una presentación, di:* "Empaquetamos todo en
un tablero web con 6 secciones, para que cualquier persona del negocio use el
sistema sin tocar una línea de código."

---

## 12. Resumen para cerrar

| Pieza | En una frase |
|---|---|
| Limpieza | Pasar los datos sucios en limpio. |
| Data Warehouse | Ordenarlos en un archivero y verificar que cuadran. |
| Calendario BR | Darle al sistema "conciencia" de feriados y Black Friday. |
| Modelo de retrasos v2 | Adivinar qué pedidos llegarán tarde (70 % mejor que la v1). |
| Segmentación | Agrupar 3,095 vendedores en 3 perfiles, estilo playlist de Spotify. |
| Pronóstico + alertas | Predecir ventas y avisar de faltantes con semáforo. |
| Asistente | Preguntarle al sistema en español. |
| Tablero web | Verlo todo en una pantalla amigable. |

*Si alguien te pregunta "¿y para qué sirve todo esto?", di:* "Sirve para que
una tienda en línea deje de reaccionar tarde: ahora puede anticipar entregas
con problemas, faltantes de inventario y vendedores poco confiables, antes de
que le cuesten dinero."
