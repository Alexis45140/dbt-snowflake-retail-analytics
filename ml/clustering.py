"""
Segmentation clients — Clustering K-means
==========================================
Ce script segmente les clients du dataset Retail Analytics
en 3 profils comportementaux via un algorithme K-means.

Input  : seeds/retail_sales_dataset.csv
Output : seeds/retail_predictions.csv (customer_id, segment, segment_label)

Usage  : python ml/clustering.py
"""

import os
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


# ─────────────────────────────────────────
# 1. Chargement des données
# ─────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH  = os.path.join(BASE_DIR, "seeds", "retail_sales_dataset.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "seeds", "retail_predictions.csv")

df_raw = pd.read_csv(INPUT_PATH)

# Normalisation des noms de colonnes
df_raw.columns = df_raw.columns.str.lower()
df_raw = df_raw.rename(columns={
    "total_amount"    : "montant_total",
    "product_category": "categorie_produit",
    "gender"          : "genre",
    "quantity"        : "quantite",
    "price_per_unit"  : "prix_unitaire",
})


# ─────────────────────────────────────────
# 2. Agrégation par client
# ─────────────────────────────────────────

df_clients = (
    df_raw
    .groupby("customer_id")
    .agg(
        ca_total      = ("montant_total",    "sum"),
        nb_achats     = ("transaction_id",   "count"),
        panier_moyen  = ("montant_total",    "mean"),
        nb_categories = ("categorie_produit","nunique"),
    )
    .reset_index()
)


# ─────────────────────────────────────────
# 3. Normalisation des features
# ─────────────────────────────────────────

FEATURES = ["ca_total", "nb_achats", "panier_moyen", "nb_categories"]

scaler = StandardScaler()
X = scaler.fit_transform(df_clients[FEATURES])


# ─────────────────────────────────────────
# 4. Clustering K-means (3 segments)
# ─────────────────────────────────────────

N_CLUSTERS = 3

kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
df_clients["segment"] = kmeans.fit_predict(X)

# Nommage des segments selon le CA moyen (du plus faible au plus élevé)
segment_ca = df_clients.groupby("segment")["ca_total"].mean().sort_values()
SEGMENT_LABELS = {
    segment_ca.index[0]: "Petit acheteur",
    segment_ca.index[1]: "Acheteur régulier",
    segment_ca.index[2]: "Gros acheteur",
}
df_clients["segment_label"] = df_clients["segment"].map(SEGMENT_LABELS)


# ─────────────────────────────────────────
# 5. Export CSV pour dbt seed
# ─────────────────────────────────────────

df_clients[["customer_id", "segment", "segment_label"]].to_csv(
    OUTPUT_PATH, index=False, encoding="utf-8-sig"
)


# ─────────────────────────────────────────
# 6. Résultats
# ─────────────────────────────────────────

print("✅ Clustering K-means terminé")
print(f"   Fichier exporté → {OUTPUT_PATH}\n")

print("📊 Répartition des segments :")
print(df_clients["segment_label"].value_counts().to_string())

print("\n💰 CA moyen par segment :")
print(
    df_clients
    .groupby("segment_label")["ca_total"]
    .mean()
    .round(2)
    .to_string()
)