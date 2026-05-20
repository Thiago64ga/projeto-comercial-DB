# Manutenção e Evolução

## Como Adicionar um Novo Dashboard

1. Criar query em `app/services/bi_queries.py`.
2. Criar rota em `app/routes.py`.
3. Adicionar permissão em `roleProfiles`.
4. Adicionar tela em `screens`.
5. Criar função `renderNovoDashboard()` em `script.js`.
6. Registrar no mapa `renderers`.
7. Criar gráficos com `renderCharts()`.
8. Testar endpoint e interface.

Exemplo de service:

```python
def get_receita_por_regiao():
    return text("""
        SELECT regiao, SUM(receita_liquida) AS total
        FROM comercial.vm_kpis_comercial_mensal
        GROUP BY regiao
        ORDER BY total DESC
    """)
```

## Como Adicionar uma Nova Query

Padrão recomendado:

```python
def minha_query(filtro=None):
    sql = "SELECT ... WHERE 1=1"
    params = {}

    if filtro:
        sql += " AND campo = :filtro"
        params["filtro"] = filtro

    return text(sql), params
```

Evite interpolar valores diretamente na string SQL.

## Como Criar Nova Rota

```python
@app.route("/minha_rota")
def minha_rota():
    session = get_session()
    try:
        query, params = bi_queries.minha_query()
        result = session.execute(query, params).fetchall()
        return jsonify([...])
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    finally:
        session.close()
```

## Como Adicionar Permissão

1. Adicione permissão ao perfil:

```javascript
roleProfiles.administrador.permissions.push("nova:tela");
```

2. Adicione tela:

```javascript
{ id: "nova-tela", label: "Nova Tela", icon: "N", permission: "nova:tela" }
```

3. Adicione renderer:

```javascript
const renderers = {
    "nova-tela": renderNovaTela
};
```

## Como Adicionar Usuários

Via interface:

1. Autentique como Administrador ou Gerente.
2. Abra "Gerenciar Usuários".
3. Preencha nome, email, senha, perfil e status.
4. Clique em cadastrar.

Via SQL:

```sql
INSERT INTO comercial.app_usuario (nome, email, senha, perfil, status)
VALUES ('Nome', 'email@dominio.com', 'senha123', 'analista', 'Ativo');
```

## Como Adicionar Gráfico

1. Garanta que os dados estejam em `state.data`.
2. Adicione canvas com `chartCard`.
3. Chame `renderCharts`.

```javascript
${chartCard("Receita por região", "chartRegiao")}

renderCharts([
    {
        id: "chartRegiao",
        type: "bar",
        data: {
            labels: dados.map((item) => item.regiao),
            datasets: [{ label: "Receita", data: dados.map((item) => item.total) }]
        }
    }
]);
```

## Como Criar Nova Tela

1. Defina função `renderMinhaTela()`.
2. Monte HTML usando helpers existentes.
3. Adicione evento se houver formulário.
4. Registre em `renderCurrentScreen()`.
5. Adicione permissão e item no menu.

## Como Integrar APIs Externas

Padrão recomendado:

- criar rota backend que consome API externa;
- tratar credenciais no `.env`;
- nunca expor chaves no frontend;
- normalizar resposta no service;
- adicionar fallback e tratamento de erro.

## Como Expandir o Banco

1. Alterar `db/init/cria_banco.sql`.
2. Atualizar `docs/database.md`.
3. Criar ou ajustar query em `bi_queries.py`.
4. Atualizar endpoints e frontend.
5. Recriar banco em ambiente de desenvolvimento.

Melhoria recomendada: usar Alembic para migrations incrementais.

## Boas Práticas de Manutenção

- Manter SQL parametrizado.
- Fechar sessões no `finally`.
- Usar `rollback` em exceções de escrita.
- Atualizar documentação junto com mudanças.
- Evitar lógica duplicada no frontend.
- Criar testes para novas rotas.
- Validar permissões no backend em evoluções futuras.

## Dívidas Técnicas Conhecidas

| Item | Risco | Ação recomendada |
|---|---|---|
| Senhas em texto puro | Alto | Implementar hash. |
| Permissão só no frontend | Alto | Criar autorização backend. |
| Sem migrations | Médio | Adotar Alembic. |
| Chart.js via CDN | Médio | Empacotar dependência. |
| Sem testes | Médio | Adicionar pytest e testes JS. |
| Venda com um item | Baixo | Permitir múltiplos itens. |
