{{ config(materialized='table') }}

SELECT
    s.customer_id,
    s.genre,
    s.age,
    s.tranche_age,
    SUM(s.montant_total)           AS ca_total,
    COUNT(s.transaction_id)        AS nb_achats,
    ROUND(AVG(s.montant_total), 2) AS panier_moyen,
    p.segment,
    p.segment_label
FROM {{ ref('stg_retail') }} s
LEFT JOIN {{ ref('retail_predictions') }} p
    ON s.customer_id = p.customer_id
GROUP BY
    s.customer_id, s.genre, s.age,
    s.tranche_age, p.segment, p.segment_label
ORDER BY ca_total DESC