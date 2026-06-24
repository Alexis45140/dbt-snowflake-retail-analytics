{{ config(materialized='table') }}
SELECT
    mois_debut,
    annee,
    mois,
    categorie_produit,
    COUNT(transaction_id)        AS nb_commandes,
    SUM(montant_total)           AS ca_mensuel,
    ROUND(AVG(montant_total), 2) AS panier_moyen,
    COUNT(DISTINCT customer_id)  AS nb_clients
FROM {{ ref('stg_retail') }}
WHERE categorie_produit IS NOT NULL  -- ← ligne ajoutée
GROUP BY mois_debut, annee, mois, categorie_produit
ORDER BY mois_debut