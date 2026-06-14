# 🛍️ Pipeline Data ELT — Retail Analytics (dbt Core × Snowflake × Tableau)

Ce dépôt héberge un projet complet de **Modern Data Stack** simulant un environnement de production pour un **Analytics Engineer**. L'objectif est d'ingérer des données brutes de ventes au détail, de les transformer avec **dbt Core** dans **Snowflake**, de valider la qualité des données via des tests automatisés, et de restituer des KPIs dans un **dashboard Tableau interactif**.

---

## 🏗️ Architecture Globale du Pipeline (ELT)

```
CSV (1 000 transactions)
        ↓
   Snowflake (ANALYTICS.ANALYTICS)
        ↓
   dbt Core — Staging (stg_retail)
        ↓
   dbt Core — Marts (mart_kpis / mart_ca_mensuel / mart_performance_categorie)
        ↓
   Tableau Public (Dashboard interactif)
```

Le pipeline suit une approche **ELT** moderne :

1. **Extract & Load** — Chargement du fichier CSV brut dans Snowflake via `dbt seed`
2. **Staging** — Nettoyage, typage et normalisation des colonnes (snake_case, casting Snowflake)
3. **Marts** — Modélisation orientée métier : KPIs globaux, évolution mensuelle, performance par catégorie
4. **Data Quality** — Tests automatisés (unicité, nullité, plages de valeurs) via dbt native + `dbt_expectations`
5. **BI** — Restitution visuelle sur Tableau Public

---

## 🛠️ Stack Technique

| Outil | Rôle |
|---|---|
| **Snowflake** | Cloud Data Warehouse — stockage et calcul |
| **dbt Core v1.11** | Transformation SQL modulaire — staging et marts |
| **dbt_expectations** | Tests avancés de qualité des données |
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
│   └── retail_sales_dataset.csv
└── models/
    ├── staging/
    │   ├── sources.yml
    │   └── stg_retail.sql
    ├── marts/
    │   ├── mart_kpis.sql
    │   ├── mart_ca_mensuel.sql
    │   └── mart_performance_categorie.sql
    └── schema.yml
```

---

## 🧬 Détail des Modèles dbt

### 1. Couche Staging — `stg_retail.sql` (Vue)

Isole la donnée brute. Normalise les colonnes Snowflake (majuscules → snake_case), applique le typage précis et enrichit avec des colonnes calculées (mois, année, tranche d'âge).

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

### 2. Couche Marts — 3 tables orientées métier

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
    mois_debut,
    annee,
    mois,
    COUNT(transaction_id)        AS nb_commandes,
    SUM(montant_total)           AS ca_mensuel,
    ROUND(AVG(montant_total), 2) AS panier_moyen,
    COUNT(DISTINCT customer_id)  AS nb_clients
FROM {{ ref('stg_retail') }}
GROUP BY mois_debut, annee, mois
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
    ROUND(
        SUM(montant_total) * 100.0 /
        SUM(SUM(montant_total)) OVER (), 1
    )                            AS part_ca_pct
FROM {{ ref('stg_retail') }}
GROUP BY categorie_produit
ORDER BY ca_total DESC
```

---

## 🧪 Qualité des Données & Tests Automatisés

Tests déclarés dans `models/schema.yml` pour garantir le principe de **Single Source of Truth** :

```yaml
version: 2

models:
  - name: stg_retail
    description: "Staging retail — données nettoyées et typées"
    columns:
      - name: transaction_id
        tests:
          - unique
          - not_null
      - name: montant_total
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              arguments:
                min_value: 0
                max_value: 10000
      - name: categorie_produit
        tests:
          - not_null
          - accepted_values:
              values: ['Beauty', 'Clothing', 'Electronics']
```

---

## 📊 Dashboard Tableau Public

Les marts dbt alimentent un dashboard interactif comprenant :

- **KPIs globaux** — CA total, nombre de commandes, panier moyen
- **Évolution mensuelle** — Courbe de tendance des ventes sur l'année
- **Performance par catégorie** — Comparaison Beauty / Clothing / Electronics

👉 **[Consulter le dashboard interactif](https://public.tableau.com/views/ExecutiveSalesDashboard-RetailAnalytics/Feuille2?:language=fr-FR&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)**

> *Note : Pour Tableau Public (version gratuite), les données sont exportées en CSV depuis Snowflake. En environnement d'entreprise, Tableau Desktop maintient une connexion live avec Snowflake pour un rafraîchissement automatisé.*

---

## 🚀 Guide d'Exécution Local

### Prérequis

- Python 3.9+
- Compte Snowflake actif

### Installation

```powershell
# Cloner le repo
git clone https://github.com/Alexis45140/dbt-snowflake-retail-analytics.git
cd dbt-snowflake-retail-analytics

# Créer et activer le venv
python -m venv .venv
.venv\Scripts\activate

# Installer dbt
pip install dbt-snowflake
```

### Configuration

Configurer `~/.dbt/profiles.yml` avec vos identifiants Snowflake :

```yaml
mon_projet:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: QYWJEWA-FZ21738
      user: dbt_user
      password: PASSWORD
      database: ANALYTICS
      schema: ANALYTICS
      warehouse: TRANSFORMING_WH
```

### Déploiement

```powershell
# 1. Installer les packages dbt
dbt deps

# 2. Charger le CSV dans Snowflake
dbt seed

# 3. Exécuter les modèles
dbt run

# 4. Lancer les tests qualité
dbt test

# 5. Générer la documentation
dbt docs generate
dbt docs serve
```

---

## 👤 Auteur

**Alexis Claudeon** — Data Analyst | Analytics Engineer Junior

- 🐙 [GitHub](https://github.com/Alexis45140)
- 💼 [LinkedIn](https://www.linkedin.com/in/alexis-claudeon)
