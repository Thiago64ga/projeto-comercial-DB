# Guia De Execucao

## 1. Instalar Dependencias

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configurar Banco

O `.env` deve apontar para o PostgreSQL do Docker:

```env
DB_HOST=localhost
DB_PORT=5782
DB_NAME=bi_comercial_db
DB_USER=bi_user
DB_PASSWORD=bi_pass
```

Subir o banco:

```powershell
docker compose -f infra/docker/docker-compose.yml up -d
```

Em banco novo, o arquivo `db/init/cria_banco.sql` roda automaticamente. Para entrega academica ou execucao manual em um unico arquivo, use `db/banco_completo.sql`.

Em banco ja existente, execute os fixes em `db/fixes/` quando necessario.

## 3. Executar Aplicacao

```powershell
venv\Scripts\python.exe run.py
```

Acesse:

```text
http://127.0.0.1:5000/
```

Login inicial:

```text
admin@aurora.local
admin123
```

## 4. Testar Cadastros

1. Entre como Admin Comercial.
2. Acesse `Gerenciar Usuarios` e cadastre um usuario.
3. Acesse `Produtos`, `Filiais` ou `Categorias` e cadastre um item.
4. Acesse `Nova Venda` e registre uma venda.
5. Acesse `Rotinas SQL`, confira as triggers/procedures/functions e clique em `Executar demo`.
6. Confira a mensagem de sucesso e a atualizacao automatica da tabela/dashboard.

## 5. Validar Banco

```sql
SELECT COUNT(*)
FROM information_schema.tables
WHERE table_schema = 'comercial'
  AND table_type = 'BASE TABLE';
```

```sql
SELECT COUNT(DISTINCT trigger_name)
FROM information_schema.triggers
WHERE trigger_schema = 'comercial';
```

```sql
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'comercial'
ORDER BY routine_name;
```
