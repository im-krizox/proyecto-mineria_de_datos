# Minería de datos
## Proyecto final
### — *Smart Supply Chain* —

**Grupo 2805**  
**Profesor:** M. en IA Oscar Daniel Acosta González (MAC)  
**Marzo 2026**

---

## Introducción

La gestión moderna de la cadena de suministro en el sector retail exige una transición hacia modelos analíticos de alta precisión, eliminando las conjeturas que tradicionalmente provocan mermas o quiebres de inventario (*stockouts*). En un entorno logístico dinámico, resulta imperativo contar con herramientas predictivas que procesen grandes volúmenes de datos transaccionales e integren variables exógenas como temporalidades climáticas o calendarios festivos. Al aplicar modelos de aprendizaje automático a estos conjuntos de datos, las organizaciones pueden transformar el registro histórico de ventas en pronósticos robustos de demanda a nivel tienda y SKU.

El verdadero salto cualitativo se da al integrar esta capacidad predictiva con una interfaz basada en agentes conversacionales. Este enfoque democratiza el acceso a la inteligencia de negocios, permitiendo que los gerentes de almacén y planeadores de inventario interactúen en lenguaje natural con sus datos. De esta manera, el sistema no solo predice cuándo se agotará un producto, sino que el agente actúa como un orquestador que facilita la toma de decisiones logísticas inmediatas, reduciendo la fricción entre la matemática predictiva y la operación diaria en piso.

El objetivo principal de este proyecto es construir un ecosistema analítico *end-to-end* que anticipe el comportamiento de la demanda y optimice el almacenamiento, permitiendo a los usuarios interactuar con estos pronósticos mediante una interfaz conversacional para generar estrategias de reabastecimiento informadas.

---

## Adquisición del Conjunto de Datos

Para el desarrollo de este proyecto, se deberá identificar, extraer y consolidar un conjunto de datos transaccionales representativo del sector retail o logístico. Es posible utilizar repositorios de datos públicos y robustos (por ejemplo, los conjuntos de datos de *Olist*, *Instacart* o equivalentes) que contengan registros históricos de ventas, movimientos de almacén e información a nivel de Unidad de Mantenimiento de Existencias (SKU).

Como requisito indispensable para robustecer el análisis, el conjunto de datos principal deberá ser enriquecido con al menos una fuente de información exógena. La adquisición de estos datos adicionales (tales como variables climatológicas, calendarios de días festivos locales o indicadores macroeconómicos) es crucial para justificar e interpretar correctamente las estacionalidades, picos de demanda y fluctuaciones atípicas en la cadena de suministro.

---

## Estrategia Analítica

La empresa *Nexus Supply* requiere el diseño, entrenamiento y validación de modelos de aprendizaje automático capaces de capturar la dinámica del inventario. La estrategia metodológica debe contemplar, de manera enunciativa mas no limitativa, los siguientes enfoques:

- **Modelado de Series de Tiempo:** Construcción de modelos predictivos orientados a pronosticar la demanda futura a nivel de SKU y por sucursal. El objetivo primordial es establecer un sistema de alertas tempranas que anticipe posibles quiebres de inventario (*stockouts*) o excesos de almacenamiento.

- **Segmentación (Clustering):** Aplicación de algoritmos de aprendizaje no supervisado para identificar y agrupar tiendas, centros de distribución o categorías de productos que exhiban comportamientos de rotación similares. Esto permitirá generar estrategias de reabastecimiento parametrizadas por clúster.

- **Ingeniería de Características y Limpieza:** Tratamiento exhaustivo de las bases de datos transaccionales, poniendo especial énfasis en la imputación de valores ausentes (comunes en historiales de retail), el manejo de valores atípicos generados por compras de pánico o errores de captura, y la evaluación de la multicolinealidad al integrar las variables exógenas.

- Estructuración de datos en OLTP.

- Construcción de un Data Warehouse.

- Construcción de una interfaz web amigable y flexible que permita interactuar durante todo el proceso.

Adicionalmente, quieren disponibilizar su solución mediante un agente que les permita explorar la información y poder tomar decisiones en tiempo cercano al real. Es por ello que han destinado un equipo de expertos en datos para realizar las siguientes tareas:

- Entablar conversaciones con sus datos
- Recibir recomendaciones basadas en datos
- Consumir la información más reciente. Para este punto, en caso de que el dataset no lo permita, se debe de simular la carga de datos cada cierto tiempo.
- Identificar la precisión de la solución.

El objetivo principal de este proyecto es poder aprovechar al máximo la información disponible, así como poder conocer de forma anticipada los comportamientos de ciertos indicadores para tomar decisiones informadas.

---

## Entregables

### Gerenciales

- Presentación de aproximadamente 5-10 minutos sobre las soluciones a los requerimientos previamente planteados. La presentación debe considerar:
  - Explicación de como su solución responde a sus problemáticas.
  - Accionables
  - Siguientes pasos

### Técnicos

- Diagrama OLTP.
- Diagrama de Data Warehouse.
- Dashboard de BI.
- Procesos ETL.
- Arquitecturas de modelos utilizados y métricas de ajuste, donde aplique.
- Agente conversacional.
- Interfaz de consumo.

---

## Consideraciones

- Es altamente importante que se defina correctamente la/las unidades muestrales a modelar en todas las soluciones.
- **INTERPRETACIÓN** y no solo lectura de estadígrafos.
- Las únicas arquitecturas válidas a utilizar son aquellas vistas en clase.
- La parte técnica del proyecto debe resolverse en Python y/o las tecnologías revisadas en clase.
- Examine el uso (o no) de todas las fuentes de datos.
- Tome en cuenta el tratamiento y limpieza de las variables unarias, multicolineales, poco pobladas, con valores atípicos o ausentes.
- La entrega debe encontrarse en perfecto orden y de forma entendible.
