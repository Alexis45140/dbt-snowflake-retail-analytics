# 🛍️ Pipeline Data ELT & Analyse des Ventes Retail (dbt Core × Snowflake × Tableau)

Ce dépôt héberge un projet complet de **Modern Data Stack** simulant un environnement de production pour un **Analytics Engineer**. L'objectif est d'ingérer des données brutes de ventes au détail (Retail), de les stocker dans un entrepôt de données **Snowflake**, d'appliquer des transformations modulaires avec **dbt Core**, de valider la qualité des données via des tests automatisés, et de restituer des indicateurs clés (KPIs) sous forme de tableau de bord interactif dans **Tableau**.

---

## 🏗️ Architecture Globale du Pipeline (ELT)

Le pipeline suit une approche moderne de type **ELT** (Extract, Load, Transform) où les transformations s'exécutent directement au sein de la puissance de calcul du cloud data warehouse.

1. **Ingestion (Load)** : Chargement du fichier brut `retail_sales_dataset.csv` (1 000 transactions) dans la base de données Snowflake via la fonctionnalité `dbt seed`.
2. **Transformation - Couche Staging** : Nettoyage, normalisation de la casse Snowflake (conversion des majuscules contraignantes en minuscules), typage précis (*casting*) et renommage des colonnes.
3. **Transformation - Couche Marts** : Modélisation dimensionnelle orientée métier. Agrégation mensuelle et par catégorie de produits pour calculer les indicateurs financiers indispensables au pilotage.
4. **Qualité des Données (Data Quality)** : Exécution de tests automatisés (contraintes d'intégrité et règles métiers) pour valider la fiabilité du modèle final.
5. **Restitution (BI)** : Modélisation visuelle et analytique des données transformées sur Tableau.

---

## 🛠️ Stack Technique

* **Entrepôt de Données** : Snowflake Cloud Data Warehouse (Virtual Warehouse dédié : `TRANSFORMING_WH`)
* **Transformation & Modélisation** : dbt Core v1.11 (SQL modularisé par références)
* **Qualité des Données** : dbt Native Tests & Framework `dbt_expectations`
* **Visualisation BI** : Tableau Public
* **Gestion de Version** : Git & GitHub

---

## 📂 Structure du Projet dbt

```text
mon_projet/
├── .gitignore               # Fichiers et dossiers exclus du versioning (ex: .venv, target)
├── README.md                # Documentation principale du projet
├── dbt_project.yml          # Fichier de configuration global du projet dbt
├── packages.yml             # Gestion des dépendances dbt (dbt_expectations)
├── seeds/
│   └── retail_sales_dataset.csv  # Données sources brutes de ventes
└── models/
    ├── staging/
    │   └── stg_ventes.sql   # Vue de nettoyage et normalisation des colonnes
    ├── marts/
    │   └── analyse_ventes.sql # Table d'agrégation décisionnelle pour la BI
    └── schema.yml           # Déclaration des modèles et tests de qualité des données

```

---

## 🧬 Détail des Couches de Transformation

### 1. Couche Staging (`models/staging/stg_ventes.sql`)

Cette couche isole les données brutes. Snowflake indexant par défaut en lettres majuscules avec une sensibilité à la casse lors de l'ingestion, ce modèle normalise la structure en *snake_case* propre et applique le bon typage de données.

```sql
{{ config(materialized='view') }}

SELECT
    "TRANSACTION_ID"::int as transaction_id,
    "DATE"::date as date_transaction,
    "CUSTOMER_ID"::int as customer_id,
    "GENDER"::text as genre,
    "AGE"::int as age,
    "PRODUCT_CATEGORY"::text as categorie_produit,
    "QUANTITY"::int as quantite,
    "PRICE_PER_UNIT"::float as prix_unitaire,
    "TOTAL_AMOUNT"::float as montant_total
FROM {{ ref('retail_sales_dataset') }}

```

### 2. Couche Marts (`models/marts/analyse_ventes.sql`)

Cette couche combine les données pour créer une table agrégée, optimisée pour les outils de Business Intelligence et les analyses métiers complexes.

```sql
SELECT 
    categorie_produit,
    date_trunc('month', date_transaction) as mois,
    sum(montant_total) as chiffre_affaires,
    sum(quantite) as volume_vendu,
    avg(montant_total) as panier_moyen,
    count(distinct transaction_id) as nombre_transactions
FROM {{ ref('stg_ventes') }}
GROUP BY 1, 2
ORDER BY 2 DESC, 3 DESC

```

---

## 🧪 Qualité des Données & Tests Automatisés

Pour garantir le principe de "Single Source of Truth" (Source unique de vérité), des tests d'intégrité stricts sont déclarés dans le fichier `models/schema.yml`.

* **Tests Natifs** :
* `unique` sur `transaction_id` : Garantit l'absence totale de doublons dans les transactions.
* `not_null` sur `transaction_id` : S'assure qu'aucune vente n'est orpheline d'identifiant.


* **Tests Avancés (`dbt_expectations`)** :
* Validation métier sur la colonne `montant_total` : Interdiction de valeurs de vente négatives ou égales à zéro via le test `expect_column_values_to_be_between`.



```yaml
version: 2

models:
  - name: stg_ventes
    columns:
      - name: transaction_id
        tests:
          - unique
          - not_null
      - name: montant_total
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              arguments:
                min_value: 0

```

---

## 📊 Restitution & Tableau de Bord Interactif (Tableau)

Les données agrégées issues de la table de Marts `ANALYSE_VENTES` ont été exploitées graphiquement afin de fournir un outil d'aide à la décision pour les équipes dirigeantes (*Executive Sales Dashboard*).

### Éléments clés du Dashboard :

* **Section KPI (Haut)** : Chiffre d'Affaires Global (somme), Volumes de pièces vendues et Panier Moyen par transaction.
* **Analyse Temporelle (Centre)** : Graphique linéaire affichant la tendance historique des ventes mois par mois pour identifier la saisonnalité.
* **Analyse Segmentée (Bas gauche)** : Graphique en barres horizontales classant la performance financière des différentes catégories de produits (Électronique, Vêtements, Beauté, etc.).
* **Filtres Dynamiques** : Possibilité de filtrer l'intégralité du tableau de bord au clic sur une catégorie ou un mois spécifique pour une exploration granulaire.

👉 **[Consulter le Tableau de bord interactif en ligne](https://public.tableau.com/app/profile/alexis.claudeon/viz/ExecutiveSalesDashboard-RetailAnalytics/Tableaudebord1)**

> *Note d'architecture : Pour les besoins de la publication sur la version gratuite de Tableau Public, les données nettoyées ont été extraites sous forme de Snapshot CSV sécurisé. En environnement d'entreprise réel, Tableau Desktop maintient une connexion en direct (Live/Extract planifié) avec le warehouse Snowflake (`TRANSFORMING_WH`) pour un rafraîchissement 100% automatisé.*

---

## 🚀 Guide d'Exécution Local

Pour reproduire ou tester ce pipeline de données sur votre machine :

### 1. Prérequis

* Python 3.9+ installé
* Un compte Snowflake actif configuré avec les accès appropriés

### 2. Installation de l'environnement

Cloner le dépôt et configurer l'environnement virtuel Python :

```powershell
python -m venv .venv
.\\.venv\\Scripts\\activate
pip install dbt-snowflake

```

### 3. Configuration de la connexion dbt (`profiles.yml`)

Assurez-vous d'avoir configuré votre fichier `profiles.yml` (généralement situé dans `~/.dbt/`) avec vos identifiants Snowflake, votre rôle de sécurité, ainsi que le chemin d'accès vers votre clé privée (`rsa_key.p8`) si applicable.

### 4. Déploiement du Pipeline

Exécuter la séquence de commandes dbt suivantes dans votre terminal :

```powershell
# 1. Télécharger les dépendances et packages d'extension (dbt_expectations)
dbt deps

# 2. Charger le jeu de données CSV brut dans Snowflake
dbt seed

# 3. Compiler et exécuter les modèles de transformation SQL (Staging & Marts)
dbt run

# 4. Lancer la suite de tests automatisés pour valider la qualité des données
dbt test
```

## 👤 CONTACT
**Alexis Claudeon**
* [Mon Profil LinkedIn](https://www.linkedin.com/in/alexis-claudeon/)
* [Mon Portfolio](https://github.com/alexis45140)
