-- 1. Produtos que venderam acima da media geral de quantidade.
SELECT
    p.nome_produto,
    SUM(i.quantidade) AS quantidade_vendida
FROM comercial.dim_produto p
JOIN comercial.fato_itens_venda i ON i.id_produto = p.id_produto
GROUP BY p.nome_produto
HAVING SUM(i.quantidade) > (
    SELECT AVG(total_produto)
    FROM (
        SELECT SUM(i2.quantidade) AS total_produto
        FROM comercial.fato_itens_venda i2
        GROUP BY i2.id_produto
    ) media_produtos
)
ORDER BY quantidade_vendida DESC;

-- 2. Filiais com receita maior que a media geral das filiais.
SELECT
    filial.nome_filial,
    filial.receita_liquida
FROM (
    SELECT
        f.nome_filial,
        SUM(v.valor_liquido) AS receita_liquida
    FROM comercial.fato_vendas v
    JOIN comercial.dim_filial f ON f.id_filial = v.id_filial
    GROUP BY f.nome_filial
) filial
WHERE filial.receita_liquida > (
    SELECT AVG(receita_filial)
    FROM (
        SELECT SUM(v2.valor_liquido) AS receita_filial
        FROM comercial.fato_vendas v2
        GROUP BY v2.id_filial
    ) medias
)
ORDER BY filial.receita_liquida DESC;

-- 3. Clientes que possuem compras, usando EXISTS.
SELECT
    c.nome_cliente,
    c.tipo_cliente
FROM comercial.dim_cliente c
WHERE EXISTS (
    SELECT 1
    FROM comercial.fato_vendas v
    WHERE v.id_cliente = c.id_cliente
)
ORDER BY c.nome_cliente
LIMIT 100;

-- 4. Categorias com faturamento superior a media das categorias, usando IN.
SELECT
    c.nome_categoria
FROM comercial.dim_categoria c
WHERE c.id_categoria IN (
    SELECT p.id_categoria
    FROM comercial.dim_produto p
    JOIN comercial.fato_itens_venda i ON i.id_produto = p.id_produto
    GROUP BY p.id_categoria
    HAVING SUM(i.valor_total) > (
        SELECT AVG(faturamento_categoria)
        FROM (
            SELECT SUM(i2.valor_total) AS faturamento_categoria
            FROM comercial.dim_produto p2
            JOIN comercial.fato_itens_venda i2 ON i2.id_produto = p2.id_produto
            GROUP BY p2.id_categoria
        ) medias
    )
);

-- 5. Produtos nunca vendidos.
SELECT
    p.nome_produto
FROM comercial.dim_produto p
WHERE p.id_produto NOT IN (
    SELECT DISTINCT id_produto
    FROM comercial.fato_itens_venda
)
ORDER BY p.nome_produto;

-- 6. Vendas acima do ticket medio.
SELECT
    v.numero_pedido,
    v.valor_liquido,
    (SELECT AVG(valor_liquido) FROM comercial.fato_vendas WHERE status_venda = 'CONCLUIDA') AS ticket_medio
FROM comercial.fato_vendas v
WHERE v.valor_liquido > (
    SELECT AVG(valor_liquido)
    FROM comercial.fato_vendas
    WHERE status_venda = 'CONCLUIDA'
)
ORDER BY v.valor_liquido DESC;

