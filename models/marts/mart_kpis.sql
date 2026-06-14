{{ config(materialized='table') }}
SELECT
    SUM(montant_total)                      AS ca_total,
    COUNT(transaction_id)                   AS nb_commandes,
    ROUND(AVG(montant_total), 2)            AS panier_moyen,
    COUNT(DISTINCT categorie_produit)       AS nb_categories,
    COUNT(DISTINCT customer_id)             AS nb_clients,
    MIN(date_transaction)                   AS premiere_vente,
    MAX(date_transaction)                   AS derniere_vente

FROM {{ ref('stg_retail') }}