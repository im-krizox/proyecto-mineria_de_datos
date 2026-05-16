# Diagramas del Proyecto — *Smart Supply Chain*

**Materia:** Minería de Datos · Grupo 2805
**Fecha:** 15 de mayo de 2026

Este documento agrupa los dos diagramas exigidos por el enunciado:

1. **OLTP** — Modelo transaccional original (las 9 tablas crudas de Olist).
2. **DWH (esquema estrella)** — Modelo analítico construido por el ETL.

Ambos están en formato Mermaid (texto plano, versionable). Para exportarlos a PNG/SVG se puede usar [mermaid.live](https://mermaid.live), la extensión *Markdown Preview Mermaid Support* de VSCode, o el plugin de GitHub (los renderiza automáticamente en este archivo).

---

## 1. Diagrama OLTP — Modelo transaccional Olist

Representa la **fuente de datos cruda**, antes de cualquier transformación. Cada tabla está normalizada (3FN). Las claves primarias se marcan con `PK` y las foráneas con `FK`.

```mermaid
erDiagram
    olist_customers_dataset {
        string customer_id PK
        string customer_unique_id
        string customer_zip_code_prefix FK
        string customer_city
        string customer_state
    }

    olist_orders_dataset {
        string order_id PK
        string customer_id FK
        string order_status
        datetime order_purchase_timestamp
        datetime order_approved_at
        datetime order_delivered_carrier_date
        datetime order_delivered_customer_date
        datetime order_estimated_delivery_date
    }

    olist_order_items_dataset {
        string order_id PK_FK
        int order_item_id PK
        string product_id FK
        string seller_id FK
        datetime shipping_limit_date
        float price
        float freight_value
    }

    olist_order_payments_dataset {
        string order_id PK_FK
        int payment_sequential PK
        string payment_type
        int payment_installments
        float payment_value
    }

    olist_order_reviews_dataset {
        string review_id PK
        string order_id FK
        int review_score
        string review_comment_title
        string review_comment_message
        datetime review_creation_date
        datetime review_answer_timestamp
    }

    olist_products_dataset {
        string product_id PK
        string product_category_name FK
        int product_name_lenght
        int product_description_lenght
        int product_photos_qty
        float product_weight_g
        float product_length_cm
        float product_height_cm
        float product_width_cm
    }

    olist_sellers_dataset {
        string seller_id PK
        string seller_zip_code_prefix FK
        string seller_city
        string seller_state
    }

    olist_geolocation_dataset {
        string geolocation_zip_code_prefix PK
        float geolocation_lat
        float geolocation_lng
        string geolocation_city
        string geolocation_state
    }

    product_category_name_translation {
        string product_category_name PK
        string product_category_name_english
    }

    olist_customers_dataset ||--o{ olist_orders_dataset : "realiza"
    olist_orders_dataset ||--|{ olist_order_items_dataset : "contiene"
    olist_orders_dataset ||--o{ olist_order_payments_dataset : "se_paga_con"
    olist_orders_dataset ||--o{ olist_order_reviews_dataset : "recibe"
    olist_products_dataset ||--o{ olist_order_items_dataset : "es_vendido_en"
    olist_sellers_dataset ||--o{ olist_order_items_dataset : "vende"
    product_category_name_translation ||--o{ olist_products_dataset : "traduce"
    olist_geolocation_dataset ||--o{ olist_customers_dataset : "ubica_cliente"
    olist_geolocation_dataset ||--o{ olist_sellers_dataset : "ubica_seller"
```

**Lectura del diagrama:**

| Relación | Cardinalidad | Significado |
|---|---|---|
| `customers ↔ orders` | 1 : N | Un cliente puede tener varios pedidos. |
| `orders ↔ order_items` | 1 : N (al menos 1) | Un pedido tiene uno o más ítems. |
| `orders ↔ payments` | 1 : N | Un pedido se paga en una o varias secuencias (ej. tarjeta + voucher). |
| `orders ↔ reviews` | 1 : 0..N | Un pedido puede recibir 0 o varias reseñas. |
| `products ↔ items` | 1 : N | Un producto se vende en muchos ítems. |
| `sellers ↔ items` | 1 : N | Un seller vende muchos ítems. |
| `category_translation ↔ products` | 1 : N | Cada categoría PT mapea a una EN. |
| `geolocation ↔ customers/sellers` | 1 : N | Un prefijo postal localiza a múltiples clientes y sellers. |

**Volúmenes en producción:**

| Tabla | Filas | Granularidad |
|---|---:|---|
| `olist_customers_dataset` | 99,441 | 1 fila / cliente |
| `olist_orders_dataset` | 99,441 | 1 fila / pedido |
| `olist_order_items_dataset` | 112,650 | 1 fila / ítem del pedido |
| `olist_order_payments_dataset` | 103,886 | 1 fila / secuencia de pago |
| `olist_order_reviews_dataset` | 99,224 | 1 fila / reseña |
| `olist_products_dataset` | 32,951 | 1 fila / SKU |
| `olist_sellers_dataset` | 3,095 | 1 fila / seller |
| `olist_geolocation_dataset` | 1,000,163 | 1 fila / coord. (≈19,010 prefijos únicos tras dedupe) |
| `product_category_name_translation` | 71 | 1 fila / categoría |

---

## 2. Diagrama del Data Warehouse — Esquema estrella

Construido por `02_etl_data_warehouse.ipynb`. Modelo dimensional con **6 dimensiones** y **2 tablas de hechos** (a nivel pedido y a nivel ítem). Diseñado para BigQuery + Looker Studio.

```mermaid
erDiagram
    dim_tiempo {
        int fecha_key PK "YYYYMMDD"
        date fecha
        int anio
        int mes
        int dia
        int trimestre
        int dia_semana_num
        string dia_semana_nombre
        bool es_fin_semana
    }

    dim_cliente {
        string customer_id PK
        string customer_unique_id
        string customer_zip_code_prefix FK
        string customer_city
        string customer_state
    }

    dim_geografia_cliente {
        string zip_code_prefix PK
        float geo_lat
        float geo_lng
        string geo_city
        string geo_state
    }

    dim_producto {
        string product_id PK
        string product_category_name
        string product_category_name_english
        int product_name_lenght
        int product_description_lenght
        int product_photos_qty
        float product_weight_g
        float product_length_cm
        float product_height_cm
        float product_width_cm
        float product_volume_cm3
    }

    dim_vendedor {
        string seller_id PK
        string seller_zip_code_prefix FK
        string seller_city
        string seller_state
        float seller_geo_lat
        float seller_geo_lng
    }

    dim_pago {
        int pago_key PK "0 = SIN_PAGO"
        string payment_type
        int payment_installments
    }

    fact_ventas {
        string order_id PK_FK
        int order_item_id PK
        string customer_id FK
        string product_id FK
        string seller_id FK
        int fecha_key FK
        int pago_key FK
        float price
        float freight_value
        float total_item_value
        float payment_value_item
        string order_status
        int delivery_days_real
        int delivery_days_estimated
        int delivery_delay_days
        bool is_late_delivery
        bool is_delivered
        int review_score
        bool is_bad_review
        bool is_good_review
    }

    fact_pedidos {
        string order_id PK
        string customer_id FK
        int fecha_key FK
        int pago_key FK
        string order_status
        int num_items
        bool tiene_items
        float payment_value
        int payment_installments
        int delivery_days_real
        int delivery_days_estimated
        int delivery_delay_days
        bool is_late_delivery
        bool is_delivered
        float review_score
    }

    dim_tiempo            ||--o{ fact_ventas    : "fecha_key"
    dim_tiempo            ||--o{ fact_pedidos   : "fecha_key"
    dim_cliente           ||--o{ fact_ventas    : "customer_id"
    dim_cliente           ||--o{ fact_pedidos   : "customer_id"
    dim_geografia_cliente ||--o{ dim_cliente    : "zip_code_prefix"
    dim_producto          ||--o{ fact_ventas    : "product_id"
    dim_vendedor          ||--o{ fact_ventas    : "seller_id"
    dim_pago              ||--o{ fact_ventas    : "pago_key"
    dim_pago              ||--o{ fact_pedidos   : "pago_key"
```

**Granularidad y volúmenes:**

| Tabla | Tipo | Filas | Granularidad |
|---|---|---:|---|
| `dim_tiempo` | Dimensión | 634 | 1 fila / día |
| `dim_cliente` | Dimensión | 99,441 | 1 fila / cliente |
| `dim_geografia_cliente` | Dimensión | 14,994 | 1 fila / prefijo postal |
| `dim_producto` | Dimensión | 32,951 | 1 fila / SKU |
| `dim_vendedor` | Dimensión | 3,095 | 1 fila / seller |
| `dim_pago` | Dimensión | 28 | 1 fila / (tipo × cuotas) + sentinela |
| **`fact_ventas`** | Hechos | **112,650** | 1 fila / ítem |
| **`fact_pedidos`** | Hechos | **99,441** | 1 fila / pedido |

**Decisiones de diseño:**

- **Dos tablas de hechos** (no una única) porque el negocio analiza dos granularidades distintas:
  - `fact_pedidos` para KPIs operativos (tasa de retraso, tiempo de entrega, ingreso por pedido).
  - `fact_ventas` para análisis por SKU, categoría y seller.
- **Snowflake parcial** en `dim_cliente → dim_geografia_cliente`: el prefijo postal vive en su propia dimensión porque se reutiliza para sellers y porque las coordenadas (`lat/lng`) tendrían cardinalidad innecesaria si se replicaran por cliente.
- **`dim_pago` sintética** con `pago_key=0 → SIN_PAGO` como fila sentinela para mantener integridad referencial al 100 % (existen pedidos sin registro de pago en Olist).
- **`fecha_key` entero `YYYYMMDD`** para joins rápidos en BigQuery y compatibilidad con Looker Studio.
- **Dos tablas planas (`tad_pedidos`, `tad_ventas`)** se materializan adicionalmente con todos los joins ya hechos, para alimentar dashboards sin necesidad de re-join en cada query.

---

## 3. Cómo exportar los diagramas a imagen

**Opción 1 — Web (sin instalación):**
1. Abrir https://mermaid.live
2. Pegar el contenido de `01_diagrama_oltp.mmd` o `02_diagrama_dwh_estrella.mmd`.
3. *Actions → PNG / SVG*.

**Opción 2 — Línea de comandos:**
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i 01_diagrama_oltp.mmd -o 01_diagrama_oltp.png -w 2000
mmdc -i 02_diagrama_dwh_estrella.mmd -o 02_diagrama_dwh_estrella.png -w 2000
```

**Opción 3 — VSCode:**
1. Instalar la extensión *Markdown Preview Mermaid Support*.
2. Abrir este `DIAGRAMAS.md` y `Cmd+Shift+V` para preview.

---

## 4. Archivos relacionados

| Archivo | Contenido |
|---|---|
| `DOC/diagramas/01_diagrama_oltp.mmd` | Fuente Mermaid del OLTP. |
| `DOC/diagramas/02_diagrama_dwh_estrella.mmd` | Fuente Mermaid del DWH. |
| `DOC/diagramas/DIAGRAMAS.md` | Este documento (versión publicable). |
| `Modelado/02_etl_data_warehouse.ipynb` | Implementación del ETL que materializa el modelo. |
