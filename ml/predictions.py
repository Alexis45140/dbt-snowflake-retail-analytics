"""
Prédiction du montant d'achat — Random Forest
==============================================
Ce script entraîne un modèle Random Forest pour prédire
le montant d'achat d'un client à partir de son profil
(âge, catégorie produit, quantité, genre, prix unitaire).

Input  : seeds/retail_sales_dataset.csv
Output : console (MAE + feature importance)

Usage  : python ml/predictions.py
"""

import os
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error


# ─────────────────────────────────────────
# 1. Chargement des données
# ─────────────────────────────────────────

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, "seeds", "retail_sales_dataset.csv")

df = pd.read_csv(INPUT_PATH)

# Normalisation des noms de colonnes
df.columns = df.columns.str.lower()
df = df.rename(columns={
    "total_amount"    : "montant_total",
    "product_category": "categorie_produit",
    "gender"          : "genre",
    "quantity"        : "quantite",
    "price_per_unit"  : "prix_unitaire",
})


# ─────────────────────────────────────────
# 2. Préparation des features
# ─────────────────────────────────────────

FEATURES_NUM = ["age"]
FEATURES_CAT = ["categorie_produit", "genre"]
TARGET       = "montant_total"

df_model = df[FEATURES_NUM + FEATURES_CAT + [TARGET]].copy()

# Encodage one-hot des variables catégorielles
df_encoded = pd.get_dummies(df_model, columns=FEATURES_CAT)

X = df_encoded.drop(TARGET, axis=1)
y = df_encoded[TARGET]


# ─────────────────────────────────────────
# 3. Split train / test (80 % / 20 %)
# ─────────────────────────────────────────

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)


# ─────────────────────────────────────────
# 4. Entraînement du modèle Random Forest
# ─────────────────────────────────────────

model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)


# ─────────────────────────────────────────
# 5. Évaluation
# ─────────────────────────────────────────

y_pred = model.predict(X_test)
mae    = mean_absolute_error(y_test, y_pred)


# ─────────────────────────────────────────
# 6. Résultats
# ─────────────────────────────────────────

print("✅ Modèle Random Forest entraîné")
print(f"   Observations : {len(df)} | Train : {len(X_train)} | Test : {len(X_test)}")
print(f"\n📊 MAE (erreur moyenne absolue) : {mae:.2f} €")

feature_importance = (
    pd.DataFrame({
        "feature"   : X.columns,
        "importance": model.feature_importances_,
    })
    .sort_values("importance", ascending=False)
    .reset_index(drop=True)
)

print("\n🎯 Top 5 facteurs prédictifs :")
print(feature_importance.head(5).to_string(index=False))