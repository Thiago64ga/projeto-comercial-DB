# Deploy

## Visão Geral

O projeto pode ser executado localmente com Flask ou publicado em ambiente Linux usando Gunicorn e Nginx. O banco pode rodar em Docker ou em serviço PostgreSQL gerenciado.

## Deploy Local

```powershell
venv\Scripts\activate
python run.py
```

Acesso:

```text
http://127.0.0.1:5000/
```

## Deploy com Docker para Banco

```powershell
docker compose -f infra/docker/docker-compose.yml up -d
```

Depois:

```powershell
python run.py
```

## Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `DB_HOST` | Host PostgreSQL. |
| `DB_PORT` | Porta PostgreSQL. |
| `DB_NAME` | Nome do banco. |
| `DB_USER` | Usuário do banco. |
| `DB_PASSWORD` | Senha do banco. |
| `SECRET_KEY` | Chave usada pela sessão Flask. |

Exemplo produção:

```env
DB_HOST=10.0.0.10
DB_PORT=5432
DB_NAME=bi_comercial_db
DB_USER=bi_user
DB_PASSWORD=senha-forte
SECRET_KEY=gere-uma-chave-longa-e-segura
```

## Deploy Linux com Gunicorn

Instale dependências:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Execute:

```bash
gunicorn "run:app" --bind 0.0.0.0:8000 --workers 3
```

## Serviço systemd

Exemplo:

```ini
[Unit]
Description=Rede Comercial Aurora BI
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/projeto-comercial-DB
EnvironmentFile=/opt/projeto-comercial-DB/.env
ExecStart=/opt/projeto-comercial-DB/venv/bin/gunicorn "run:app" --bind 127.0.0.1:8000 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```

## Nginx

Exemplo:

```nginx
server {
    listen 80;
    server_name exemplo.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Banco em Produção

Recomendações:

- usar senha forte;
- restringir IPs;
- habilitar backups automáticos;
- separar usuário de leitura e escrita;
- não expor porta do banco publicamente.

## Segurança Básica

- Definir `debug=False` em produção.
- Usar HTTPS.
- Remover senhas padrão.
- Implementar hash de senha.
- Manter rotas protegidas por sessão e evoluir para Flask-Login ou sessão server-side se necessário.
- Manter dependências atualizadas.
- Não versionar `.env` real de produção.

## Deploy Docker Completo

Melhoria futura: criar `Dockerfile` para aplicação Flask.

Exemplo conceitual:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:8000"]
```

## Checklist de Produção

- [ ] Banco criado e populado.
- [ ] `.env` configurado.
- [ ] Dependências instaladas.
- [ ] Gunicorn funcionando.
- [ ] Nginx encaminhando.
- [ ] HTTPS configurado.
- [ ] Logs habilitados.
- [ ] Backup do banco configurado.
- [ ] Senhas padrão alteradas.
