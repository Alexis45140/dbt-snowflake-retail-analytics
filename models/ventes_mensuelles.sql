-- models/ventes_mensuelles.sql
SELECT 
    date,
    product_category,
    sum(total_amount) as total_ventes
FROM {{ ref('retail_sales_dataset') }}
GROUP BY 1, 2