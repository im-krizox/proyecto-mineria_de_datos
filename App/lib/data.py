"""Carga cacheada de los datasets producidos por los notebooks."""
from __future__ import annotations

import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CSV_DIR = Path(os.environ.get("CSV_DIR", PROJECT_ROOT / "CSV")).resolve()
MODEL_DIR = PROJECT_ROOT / "Modelado" / "_modelo"


@st.cache_data(show_spinner=False)
def load_pedidos() -> pd.DataFrame:
    """`04_tad_pedidos_enriquecido.csv` (a nivel pedido con banderas exógenas)."""
    df = pd.read_csv(CSV_DIR / "04_tad_pedidos_enriquecido.csv",
                     parse_dates=["order_purchase_timestamp",
                                  "order_approved_at",
                                  "order_estimated_delivery_date"])
    return df


@st.cache_data(show_spinner=False)
def load_ventas_min() -> pd.DataFrame:
    """`02_tad_ventas.csv` con un subconjunto de columnas para tarjetas y joins."""
    cols = ["order_id", "order_item_id", "seller_id", "product_id",
            "product_category_name_english",
            "price", "freight_value", "total_item_value",
            "seller_state", "seller_city",
            "seller_geo_lat", "seller_geo_lng",
            "is_late_delivery", "is_delivered",
            "anio", "mes"]
    return pd.read_csv(CSV_DIR / "02_tad_ventas.csv", usecols=cols)


@st.cache_data(show_spinner=False)
def load_clusters() -> pd.DataFrame:
    return pd.read_csv(CSV_DIR / "06_seller_agg_clusters.csv")


@st.cache_data(show_spinner=False)
def load_perfil_clusters() -> pd.DataFrame:
    return pd.read_csv(CSV_DIR / "06_perfil_clusters.csv")


@st.cache_data(show_spinner=False)
def load_series_diaria() -> pd.DataFrame:
    df = pd.read_csv(CSV_DIR / "07_series_demanda_diaria.csv",
                     parse_dates=["fecha"])
    return df


@st.cache_data(show_spinner=False)
def load_alertas() -> pd.DataFrame:
    df = pd.read_csv(CSV_DIR / "07_alertas_inventario.csv",
                     parse_dates=["fecha"])
    return df


@st.cache_data(show_spinner=False)
def load_metricas_series() -> pd.DataFrame:
    return pd.read_csv(CSV_DIR / "07_metricas_series_tiempo.csv")


@st.cache_data(show_spinner=False)
def load_calendario() -> pd.DataFrame:
    df = pd.read_csv(CSV_DIR / "04_dim_calendario.csv", parse_dates=["fecha"])
    return df


@st.cache_data(show_spinner=False)
def load_comparacion_v1v2() -> pd.DataFrame:
    return pd.read_csv(CSV_DIR / "08_comparacion_v1_v2.csv")


@st.cache_data(show_spinner=False)
def load_importancias() -> pd.DataFrame:
    return pd.read_csv(CSV_DIR / "08_importancias_rf_tuneado.csv")


@st.cache_resource(show_spinner=False)
def load_model():
    """Pipeline serializado del modelo v2 (Random Forest tuneado)."""
    pipeline = joblib.load(MODEL_DIR / "rf_v2_pipeline.joblib")
    schema = joblib.load(MODEL_DIR / "rf_v2_schema.joblib")
    return pipeline, schema


# --- Combinaciones derivadas (cacheadas) ------------------------------------

@st.cache_data(show_spinner=False)
def kpi_globales() -> dict:
    """Métricas agregadas globales para el hero/header."""
    ped = load_pedidos()
    ven = load_ventas_min()
    return {
        "n_pedidos":   int(len(ped)),
        "n_items":     int(len(ven)),
        "n_sellers":   int(ven["seller_id"].nunique()),
        "n_productos": int(ven["product_id"].nunique()),
        "gmv":         float(ven["price"].sum() + ven["freight_value"].sum()),
        "gmv_price":   float(ven["price"].sum()),
        "tasa_retraso":float(ped["is_late_delivery"].mean()),
        "tasa_retraso_items": float(ven["is_late_delivery"].mean()),
        "n_alertas":   int(len(load_alertas())),
        "rango_fechas": (ped["order_purchase_timestamp"].min(),
                         ped["order_purchase_timestamp"].max()),
    }


@st.cache_data(show_spinner=False)
def retraso_por_estado() -> pd.DataFrame:
    ped = load_pedidos()
    out = (ped.groupby("customer_state", as_index=False)
              .agg(pedidos=("order_id", "count"),
                   tasa_retraso=("is_late_delivery", "mean")))
    return out.sort_values("tasa_retraso", ascending=False)


@st.cache_data(show_spinner=False)
def retraso_por_mes() -> pd.DataFrame:
    ped = load_pedidos()
    ped = ped.dropna(subset=["order_purchase_timestamp"]).copy()
    ped["aniomes"] = ped["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
    out = (ped.groupby("aniomes", as_index=False)
              .agg(pedidos=("order_id", "count"),
                   tasa_retraso=("is_late_delivery", "mean")))
    return out.sort_values("aniomes")


@st.cache_data(show_spinner=False)
def top_categorias(n: int = 12) -> pd.DataFrame:
    ven = load_ventas_min()
    out = (ven.groupby("product_category_name_english", as_index=False)
              .agg(items=("order_item_id", "count"),
                   ingresos=("price", "sum"),
                   tasa_retraso=("is_late_delivery", "mean"))
              .sort_values("ingresos", ascending=False)
              .head(n))
    return out


@st.cache_data(show_spinner=False)
def haversine_km(lat1, lon1, lat2, lon2):
    """Distancia entre dos puntos (vectorizable). Pública para la calculadora."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1; dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return float(2 * R * np.arcsin(np.sqrt(a)))


@st.cache_data(show_spinner=False)
def coords_por_estado() -> pd.DataFrame:
    """Centroide aproximado por estado (cliente)."""
    ped = load_pedidos()
    return (ped.dropna(subset=["geo_lat", "geo_lng"])
              .groupby("customer_state", as_index=False)
              .agg(geo_lat=("geo_lat", "mean"),
                   geo_lng=("geo_lng", "mean")))


@st.cache_data(show_spinner=False)
def coords_seller_por_estado() -> pd.DataFrame:
    ven = load_ventas_min()
    return (ven.dropna(subset=["seller_geo_lat", "seller_geo_lng"])
              .groupby("seller_state", as_index=False)
              .agg(seller_geo_lat=("seller_geo_lat", "mean"),
                   seller_geo_lng=("seller_geo_lng", "mean")))
