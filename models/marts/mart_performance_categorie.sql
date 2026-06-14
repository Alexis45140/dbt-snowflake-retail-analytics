{{ config(materialized='table') }}
SELECT
    categorie_produit,
    COUNT(transaction_id)                   AS nb_commandes,
    SUM(montant_total)                      AS ca_total,
    ROUND(AVG(montant_total), 2)            AS panier_moyen,
    COUNT(DISTINCT customer_id)             AS nb_clients,
    ROUND(
        SUM(montant_total) * 100.0 /
        SUM(SUM(montant_total)) OVER (), 1
    )                                       AS part_ca_pct

FROM {{ ref('stg_retail') }}
GROUP BY categorie_produit
ORDER BY ca_total DESC