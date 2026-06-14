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