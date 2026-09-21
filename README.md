# 🛍️ Pipeline Data ELT + ML — Retail Analytics (dbt Core × Snowflake × BigQuery × Tableau)

Ce dépôt héberge un projet complet de **Modern Data Stack enrichi d'une couche Machine Learning**, simulant un environnement de production pour un **Analytics Engineer**. L'objectif est d'ingérer des données brutes de ventes au détail, de les transformer avec **dbt Core**, de valider la qualité des données, d'enrichir le pipeline avec des modèles ML (clustering K-means sur les montants d'achat et prédiction Random Forest), et de restituer des KPIs dans un **dashboard Tableau interactif**.

---

## 🏗️ Architecture Globale du Pipeline (ELT + ML)

```
CSV (1 000 transactions)
        ↓
   Snowflake / BigQuery
        ↓
   dbt Core — Staging (stg_retail)
        ↓
   dbt Core — Marts (mart_kpis / mart_ca_mensuel / mart_performance_categorie)
        ↓
   ML — Clustering K-means (montants d'achat)
   ML — Random Forest (prédiction montant d'achat)
        ↓
   dbt Core — mart_predictions (clusters intégrés au pipeline)
        ↓
   Tableau Public (Dashboard interactif)
```

Le pipeline suit une approche **ELT** moderne enrichie d'une couche analytique IA :

1. **Extract & Load** — Chargement du CSV brut via `dbt seed`
2. **Staging** — Nettoyage, typage et normalisation des colonnes
3. **Marts** — Modélisation orientée métier : KPIs globaux, évolution mensuelle, performance par catégorie
4. **Machine Learning** — Clustering K-means sur les montants d'achat (3 groupes) + prédiction Random Forest (MAE 483.72€ contre 448.01€ pour la baseline : le modèle ne la bat pas ; fuite de données détectée et corrigée)
5. **Mart Prédictions** — Intégration des clusters ML dans le pipeline dbt
6. **Data Quality** — 6 tests déclarés via dbt natif + `dbt_expectations`
7. **BI** — Restitution visuelle sur Tableau Public

---

## 🛠️ Stack Technique

| Outil | Rôle |
|---|---|
| **Snowflake** | Cloud Data Warehouse (version originale) |
| **Google BigQuery** | Cloud Data Warehouse (version ML) |
| **dbt Core v1.12** | Transformation SQL modulaire — staging et marts |
| **dbt_expectations** | Tests de qualité au-delà des tests natifs dbt |
| **scikit-learn** | Clustering K-means + Random Forest |
| **pandas** | Manipulation et préparation des données ML |
| **Tableau Public** | Visualisation et dashboard interactif |
| **Git & GitHub** | Versioning et collaboration |

---

## 📂 Structure du Projet

```
dbt-snowflake-retail-analytics/
├── README.md
├── dbt_project.yml
├── packages.yml
├── seeds/
│   ├── retail_sales_dataset.csv       ← données brutes (1 000 transactions)
│   └── retail_predictions.csv         ← clusters ML (généré par clustering.py)
├── ml/
│   ├── clustering.py                  ← clustering K-means (montants d'achat)
│   ├── predictions.py                 ← prédiction Random Forest vs baseline (MAE ~484€ / ~448€)
│   └── requirements_ml.txt            ← dépendances ML
└── models/
    ├── staging/
    │   ├── sources.yml
    │   ├── schema.yml
    │   └── stg_retail.sql
    └── marts/
        ├── mart_kpis.sql
        ├── mart_ca_mensuel.sql
        ├── mart_performance_categorie.sql
        └── mart_predictions.sql       ← clusters ML intégrés au pipeline dbt
```

---

## 🧬 Détail des Modèles dbt

### 1. Couche Staging — `stg_retail.sql` (Vue)

Isole la donnée brute. Normalise les colonnes, applique le typage précis et enrichit avec des colonnes calculées (mois, année, tranche d'âge).

```sql
{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('retail', 'retail_sales_dataset') }}
),

renamed AS (
    SELECT
        "TRANSACTION_ID"::int           AS transaction_id,
        "DATE"::date                    AS date_transaction,
        "CUSTOMER_ID"::text             AS customer_id,
        "GENDER"::text                  AS genre,
        "AGE"::int                      AS age,
        "PRODUCT_CATEGORY"::text        AS categorie_produit,
        "QUANTITY"::int                 AS quantite,
        "PRICE_PER_UNIT"::float         AS prix_unitaire,
        "TOTAL_AMOUNT"::float           AS montant_total,
        EXTRACT(MONTH FROM "DATE"::date)    AS mois,
        EXTRACT(YEAR FROM "DATE"::date)     AS annee,
        DATE_TRUNC('month', "DATE"::date)   AS mois_debut,
        CASE
            WHEN "AGE"::int < 25 THEN '18-24'
            WHEN "AGE"::int < 35 THEN '25-34'
            WHEN "AGE"::int < 45 THEN '35-44'
            WHEN "AGE"::int < 55 THEN '45-54'
            ELSE '55+'
        END AS tranche_age,
        CURRENT_TIMESTAMP AS loaded_at
    FROM source
    WHERE "TOTAL_AMOUNT"::float > 0
      AND "TRANSACTION_ID" IS NOT NULL
)

SELECT * FROM renamed
```

---

### 2. Couche Marts — 4 tables orientées métier

#### `mart_kpis.sql` — KPIs Globaux (Table)

```sql
{{ config(materialized='table') }}

SELECT
    SUM(montant_total)                AS ca_total,
    COUNT(transaction_id)             AS nb_commandes,
    ROUND(AVG(montant_total), 2)      AS panier_moyen,
    COUNT(DISTINCT categorie_produit) AS nb_categories,
    COUNT(DISTINCT customer_id)       AS nb_clients,
    MIN(date_transaction)             AS premiere_vente,
    MAX(date_transaction)             AS derniere_vente
FROM {{ ref('stg_retail') }}
```

#### `mart_ca_mensuel.sql` — Évolution Mensuelle (Table)

```sql
{{ config(materialized='table') }}

SELECT
    mois_debut, annee, mois, categorie_produit,
    COUNT(transaction_id)        AS nb_commandes,
    SUM(montant_total)           AS ca_mensuel,
    ROUND(AVG(montant_total), 2) AS panier_moyen,
    COUNT(DISTINCT customer_id)  AS nb_clients
FROM {{ ref('stg_retail') }}
WHERE categorie_produit IS NOT NULL
GROUP BY mois_debut, annee, mois, categorie_produit
ORDER BY mois_debut
```

#### `mart_performance_categorie.sql` — Performance par Catégorie (Table)

```sql
{{ config(materialized='table') }}

SELECT
    categorie_produit,
    COUNT(transaction_id)        AS nb_commandes,
    SUM(montant_total)           AS ca_total,
    ROUND(AVG(montant_total), 2) AS panier_moyen,
    COUNT(DISTINCT customer_id)  AS nb_clients,
    ROUND(SUM(montant_total) * 100.0 / SUM(SUM(montant_total)) OVER (), 1) AS part_ca_pct
FROM {{ ref('stg_retail') }}
GROUP BY categorie_produit
ORDER BY ca_total DESC
```

#### `mart_predictions.sql` — Clusters ML intégrés (Table)

```sql
{{ config(materialized='table') }}

SELECT
    s.customer_id, s.genre, s.age, s.tranche_age,
    SUM(s.montant_total)           AS ca_total,
    COUNT(s.transaction_id)        AS nb_achats,
    ROUND(AVG(s.montant_total), 2) AS panier_moyen,
    p.segment, p.segment_label
FROM {{ ref('stg_retail') }} s
LEFT JOIN {{ ref('retail_predictions') }} p ON s.customer_id = p.customer_id
GROUP BY s.customer_id, s.genre, s.age, s.tranche_age, p.segment, p.segment_label
ORDER BY ca_total DESC
```

---

## 🤖 Couche Machine Learning

### Clustering K-means — `ml/clustering.py`

Regroupe les 1 000 clients en **3 groupes selon leur montant d'achat**. Le jeu de données compte ~1 achat par client : nombre d'achats et diversité catégorielle sont constants, le clustering porte donc en pratique sur le montant (CA total = panier moyen) — ce n'est pas une segmentation comportementale.

| Groupe (libellé du code) | Nb clients | CA moyen | Part |
|---|---|---|---|
| **Petit acheteur** | 701 | 131€ | 70% |
| **Acheteur régulier** | 200 | 953€ | 20% |
| **Gros acheteur** | 99 | 1 747€ | 10% |

> 10% des clients génèrent en moyenne 1 747€ de CA chacun — soit 13x plus que les petits acheteurs.

### Random Forest — `ml/predictions.py`

Prédit le montant d'achat à partir du profil client (âge, catégorie, genre), puis compare le résultat à une baseline naïve qui prédit toujours le montant moyen.

| Métrique | Valeur |
|---|---|
| **MAE** | 483.72€ |
| **MAE baseline (moyenne)** | 448.01€ |
| **Split train/test** | 800 / 200 |
| **Arbres** | 100 |
| **Variable la plus utilisée par les splits** | Age (60.6%) — sans portée prédictive, voir la baseline |

> **Note** : Une première version incluait `prix_unitaire` et `quantite` (MAE = 0€, data leakage détecté et corrigé — `montant_total = prix_unitaire × quantite`).

> **Baseline** : sans les variables à l'origine de la fuite, le Random Forest (MAE 483.72€) ne fait pas mieux qu'une prédiction constante égale à la moyenne (MAE 448.01€). Âge, genre et catégorie ne permettent donc pas de prédire le montant d'achat sur ce jeu de données : la comparaison à la baseline évite de présenter comme utile un modèle qui ne l'est pas.

---

## 🧪 Qualité des Données & Tests dbt

6 tests déclarés dans `models/staging/schema.yml` :

| Test | Type | Colonne |
|---|---|---|
| `unique` | Natif dbt | transaction_id |
| `not_null` | Natif dbt | transaction_id, montant_total, categorie_produit |
| `expect_column_values_to_be_between` | dbt_expectations | montant_total (0 → 10 000€) |
| `accepted_values` | Natif dbt | categorie_produit (Beauty, Clothing, Electronics) |

---

## 📊 Dashboard Tableau Public

- **KPIs globaux** — CA total, nombre de commandes, panier moyen
- **Évolution mensuelle** — Courbe de tendance des ventes
- **Performance par catégorie** — Comparaison Beauty / Clothing / Electronics
- **Filtres dynamiques** — Par mois et par catégorie produit

👉 **[Consulter le dashboard interactif](https://public.tableau.com/views/RetailAnalyticsSalesDashboard_17815243980290/Tableaudebord1?:language=fr-FR&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)**

---

## 🚀 Guide d'Exécution Local

### Prérequis

- Python 3.9+
- Compte Snowflake ou projet Google BigQuery

### Installation

```powershell
git clone https://github.com/Alexis45140/dbt-snowflake-retail-analytics.git
cd dbt-snowflake-retail-analytics

# Venv dbt
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install dbt-snowflake        # ou dbt-bigquery

# Venv ML (séparé)
python -m venv .venv_ml
.venv_ml\Scripts\Activate.ps1
pip install -r ml/requirements_ml.txt
```

### Déploiement

```powershell
dbt deps                         # 1. Packages dbt
dbt seed                         # 2. Chargement données brutes
dbt run                          # 3. Transformations
dbt test                         # 4. Tests qualité
python ml/clustering.py          # 5. Génération des clusters ML
python ml/predictions.py         # 6. Prédiction Random Forest
dbt seed && dbt run --select mart_predictions  # 7. Intégration ML → dbt
```

---

## 👤 Auteur

**Alexis Claudeon** — Data Analyst | Analytics Engineer Junior

- 🐙 [GitHub](https://github.com/Alexis45140)
- 💼 [LinkedIn](https://www.linkedin.com/in/alexis-claudeon)