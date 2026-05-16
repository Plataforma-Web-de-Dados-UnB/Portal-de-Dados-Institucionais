# Guia Rápido - Docker

## Configuração Inicial

### 1. Criar arquivo .env

```bash
cp .env.example .env
```

Conteúdo padrão do `.env`:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=unb_portal_dev
JWT_KEY=ChaveSecretaSuperSeguraParaJWT2024UnBPortalDeDados
JWT_ISSUER=UnBPortalAPI
JWT_AUDIENCE=UnBPortalClients
FRONTEND_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5042
```

## Comandos Principais

### Iniciar todos os serviços

```bash
docker-compose up -d
```

### Iniciar com rebuild (após mudanças no código)

```bash
docker-compose up -d --build
```

### Ver logs em tempo real

```bash
# Todos os serviços
docker-compose logs -f

# Apenas backend
docker-compose logs -f unb-portal-backend

# Apenas frontend
docker-compose logs -f unb-portal-frontend

# Apenas banco de dados
docker-compose logs -f unb-portal-postgres
```

### Verificar status dos containers

```bash
docker-compose ps
```

### Parar os serviços

```bash
docker-compose down
```

### Parar e remover volumes (limpar banco de dados)

```bash
docker-compose down -v
```

## Acessar os Serviços

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5042
- **Swagger**: http://localhost:5042/swagger
- **PostgreSQL**: localhost:5432

## Executar Comandos nos Containers

### Backend

```bash
# Acessar shell do container
docker exec -it unb_portal_backend bash

# Executar migrations
docker exec -it unb_portal_backend dotnet ef database update --project /src/Backend

# Ver migrations
docker exec -it unb_portal_backend dotnet ef migrations list --project /src/Backend

# Criar nova migration
docker exec -it unb_portal_backend dotnet ef migrations add NomeDaMigration --project /src/Backend
```

### Frontend

```bash
# Acessar shell do container
docker exec -it unb_portal_frontend sh

# Instalar nova dependência
docker exec -it unb_portal_frontend npm install nome-do-pacote

# Executar lint
docker exec -it unb_portal_frontend npm run lint
```

### PostgreSQL

```bash
# Acessar psql
docker exec -it unb_portal_postgres psql -U postgres -d unb_portal_dev

# Fazer backup do banco
docker exec unb_portal_postgres pg_dump -U postgres unb_portal_dev > backup.sql

# Restaurar backup
docker exec -i unb_portal_postgres psql -U postgres unb_portal_dev < backup.sql
```

## Troubleshooting

### Porta já em uso

Edite `docker-compose.yml` e altere a porta externa:

```yaml
ports:
  - "NOVA_PORTA:5042"  # Backend
  - "NOVA_PORTA:5173"  # Frontend
  - "NOVA_PORTA:5432"  # PostgreSQL
```

### Container não inicia

```bash
# Ver logs detalhados
docker-compose logs nome-do-servico

# Verificar se há conflitos
docker ps -a

# Remover containers antigos
docker-compose down
docker system prune -a
```

### Banco de dados não conecta

```bash
# Verificar se o PostgreSQL está saudável
docker-compose ps

# Verificar logs do PostgreSQL
docker-compose logs unb-portal-postgres

# Testar conexão
docker exec -it unb_portal_postgres pg_isready -U postgres
```

### Hot reload não funciona

Para o Frontend, certifique-se de que `CHOKIDAR_USEPOLLING=true` está no `docker-compose.yml`.

Para o Backend, o `dotnet watch` já está configurado.

### Limpar tudo e recomeçar

```bash
# Parar e remover tudo
docker-compose down -v

# Remover imagens antigas
docker rmi $(docker images -q unb-portal*)

# Limpar cache do Docker
docker system prune -a

# Rebuild completo
docker-compose up -d --build
```

## Desenvolvimento

### Workflow Recomendado

1. Faça alterações no código
2. O hot reload detecta automaticamente (backend e frontend)
3. Se adicionar pacotes/dependências, rebuild:
   ```bash
   docker-compose up -d --build nome-do-servico
   ```

### Adicionar Nova Migration

```bash
# Criar migration
docker exec -it unb_portal_backend dotnet ef migrations add NomeDaMigration --project /src/Backend

# Aplicar migration
docker exec -it unb_portal_backend dotnet ef database update --project /src/Backend
```

### Resetar Banco de Dados

```bash
# Parar serviços
docker-compose down

# Remover volume do PostgreSQL
docker volume rm tcc_postgres_data

# Reiniciar (migrations serão aplicadas automaticamente)
docker-compose up -d
```

## Produção

Para deploy em produção, crie um `docker-compose.prod.yml`:

```yaml
services:
  unb-portal-backend:
    build:
      target: prod
    environment:
      - ASPNETCORE_ENVIRONMENT=Production
```

E execute:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoramento

### Ver uso de recursos

```bash
docker stats
```

### Ver espaço em disco

```bash
docker system df
```

### Limpar recursos não utilizados

```bash
docker system prune -a --volumes
```
