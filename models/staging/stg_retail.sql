{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('retail', 'retail_sales_dataset') }}
),

renamed AS (
    SELECT
        "TRANSACTION_ID"::int          AS transaction_id,
        "DATE"::date                   AS date_transaction,
        "CUSTOMER_ID"::text            AS customer_id,
        "GENDER"::text                 AS genre,
        "AGE"::int                     AS age,
        "PRODUCT_CATEGORY"::text       AS categorie_produit,
        "QUANTITY"::int                AS quantite,
        "PRICE_PER_UNIT"::float        AS prix_unitaire,
        "TOTAL_AMOUNT"::float          AS montant_total,

        -- Colonnes calculées utiles
        EXTRACT(MONTH FROM "DATE"::date)  AS mois,
        EXTRACT(YEAR FROM "DATE"::date)   AS annee,
        DATE_TRUNC('month', "DATE"::date) AS mois_debut,

        -- Segmentation âge
        CASE
            WHEN "AGE"::int < 25 THEN '18-24'
            WHEN "AGE"::int < 35 THEN '25-34'
            WHEN "AGE"::int < 45 THEN '35-44'
            WHEN "AGE"::int < 55 THEN '45-54'
            ELSE '55+'
        END AS tranche_age,

        -- Chargement
        CURRENT_TIMESTAMP AS loaded_at

    FROM source
    WHERE "TOTAL_AMOUNT"::float > 0
      AND "TRANSACTION_ID" IS NOT NULL
)

SELECT * FROM renamed