# Instalação e Configuração

## Pré-requisitos

- Python 3.11 ou superior recomendado.
- Docker Desktop ou PostgreSQL local.
- pgAdmin ou outro cliente SQL.
- Git.
- Navegador moderno.

## Clonar o Projeto

```powershell
cd projeto-comercial-DB
```

Se estiver começando em uma nova máquina, clone o repositório pelo endereço oficial usado pela equipe e então entre na pasta `projeto-comercial-DB`.

## Criar Ambiente Virtual

```powershell
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

## Instalar Dependências

```powershell
pip install -r requirements.txt
```

Dependências principais:

| Pacote | Uso |
|---|---|
| Flask | Aplicação web. |
| SQLAlchemy | Engine e sessões SQL. |
| psycopg[binary] | Driver PostgreSQL. |
| python-dotenv | Carregamento do `.env`. |
| gunicorn | Execução em produção Linux. |

## Subir Banco com Docker

```powershell
docker compose -f infra/docker/docker-compose.yml up -d
```

Verificar containers:

```powershell
docker ps
```

Configuração criada:

| Item | Valor |
|---|---|
| Container | `db_comercial_db` |
| Banco | `bi_comercial_db` |
| Usuário | `bi_user` |
| Senha | `bi_pass` |
| Porta local | `5782` |

## Configurar `.env`

Crie ou ajuste o arquivo `.env` na raiz:

```env
DB_HOST=localhost
DB_PORT=5782
DB_NAME=bi_comercial_db
DB_USER=bi_user
DB_PASSWORD=bi_pass
SECRET_KEY=dev-secret-key
```

## Executar Script SQL

Em uma instalação nova com volume Docker vazio, o `docker-compose.yml` já monta `db/init/cria_banco.sql` em `/docker-entrypoint-initdb.d/01-cria_banco.sql`, então o PostgreSQL executa o script automaticamente na primeira inicialização.

Execute manualmente apenas se o volume já existia antes desta configuração, se estiver usando PostgreSQL local fora do Docker, ou se precisar recriar a base.

No pgAdmin:

1. Conecte ao servidor PostgreSQL.
2. Abra o banco `bi_comercial_db`.
3. Abra a Query Tool.
4. Execute `db/init/cria_banco.sql`.

Via `psql`:

```powershell
psql -h localhost -p 5782 -U bi_user -d bi_comercial_db -f db/init/cria_banco.sql
```

## Rodar Flask

```powershell
python run.py
```

Acesse:

```text
http://127.0.0.1:5000/
```

## Usuários para Teste

| Perfil | Email | Senha |
|---|---|---|
| Admin Comercial | `admin@aurora.local` | `admin123` |
| Gerente Comercial | `gerente@aurora.local` | `gerente123` |
| Operador Comercial | `operador@aurora.local` | `operador123` |
| Leitura Comercial | `leitura@aurora.local` | `leitura123` |

## Solução de Erros Comuns

### Banco não encontrado

Erro:

```text
database "db_comercial_db" does not exist
```

Solução: confirme `DB_NAME=bi_comercial_db`.

### Porta ocupada

Erro:

```text
port is already allocated
```

Solução:

```powershell
docker ps
docker stop db_comercial_db
```

ou altere a porta no compose e no `.env`.

### Dependência não instalada

Erro:

```text
ModuleNotFoundError
```

Solução:

```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

### Tabelas não existem

Erro:

```text
relation comercial.vm_kpis_comercial_mensal does not exist
```

Solução: execute `db/init/cria_banco.sql`.

### Gráficos não aparecem

Possíveis causas:

- sem internet para carregar Chart.js via CDN;
- erro em endpoint;
- banco indisponível.

Abra o DevTools do navegador e verifique a aba Network.
