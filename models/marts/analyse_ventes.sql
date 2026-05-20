-- models/marts/analyse_ventes.sql
SELECT 
    categorie_produit,
    date_trunc('month', date_transaction) as mois,
    sum(montant_total) as chiffre_affaires,
    count(distinct transaction_id) as nombre_transactions
FROM {{ ref('stg_ventes') }}
GROUP BY 1, 2