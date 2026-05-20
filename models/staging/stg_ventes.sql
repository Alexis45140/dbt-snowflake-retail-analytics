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