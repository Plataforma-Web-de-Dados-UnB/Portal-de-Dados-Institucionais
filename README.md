# Portal de Dados - Universidade de Brasília

Sistema completo para visualização e gerenciamento de dados públicos da UnB, com dashboards interativos e controle de acesso.

## Estrutura do Projeto

```
tcc/
├── Backend/           # API REST em .NET 10
├── Frontend/          # Interface em React + Vite
├── ParkManager/       # Projeto de referência
├── AIDA-Desafio/      # Projeto de referência
└── docker-compose.yml # Orquestração dos serviços
```

## Tecnologias

### Backend
- .NET 10.0
- ASP.NET Core Identity
- Entity Framework Core
- PostgreSQL
- JWT Authentication
- Swagger/OpenAPI

### Frontend
- React 19
- TypeScript
- Vite
- React Compiler

## Executar com Docker

### 1. Configurar Variáveis de Ambiente

Copie o arquivo de exemplo e configure as variáveis:

```bash
cp .env.example .env
```

Edite o arquivo `.env` conforme necessário.

### 2. Iniciar os Serviços

```bash
docker-compose up -d
```

Isso irá iniciar:
- **PostgreSQL** na porta 5432
- **Backend API** na porta 5042
- **Frontend** na porta 5173

### 3. Verificar Status

```bash
docker-compose ps
```

### 4. Ver Logs

```bash
# Todos os serviços
docker-compose logs -f

# Apenas backend
docker-compose logs -f unb-portal-backend

# Apenas frontend
docker-compose logs -f unb-portal-frontend
```

### 5. Parar os Serviços

```bash
docker-compose down
```

Para remover também os volumes (dados do banco):

```bash
docker-compose down -v
```

## Acessar a Aplicação

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5042
- **Swagger**: http://localhost:5042/swagger

## Usuário Padrão

Um Super Administrador é criado automaticamente:

- **Email**: admin@unb.br
- **Senha**: Admin123!

## Desenvolvimento Local (sem Docker)

### Backend

```bash
cd Backend
dotnet restore
dotnet ef database update
dotnet run
```

### Frontend

```bash
cd Frontend
npm install
npm run dev
```

## Migrations

As migrations são aplicadas automaticamente quando o backend inicia (via `Program.cs`).

Para criar novas migrations:

```bash
cd Backend
dotnet ef migrations add NomeDaMigration
```

## Estrutura de Dados

### Perfis de Usuário

1. **Visitante**: Acesso público aos dashboards
2. **Administrador**: Gerenciamento de painéis e dados (requer aprovação)
3. **SuperAdministrador**: Controle total incluindo aprovação de usuários

### Fluxo de Aprovação

1. Administrador se cadastra (status: Pendente)
2. SuperAdmin aprova ou rejeita
3. Apenas usuários Ativos podem fazer login

## API Endpoints

### Autenticação (Público)
- `POST /Usuario/register` - Cadastro
- `POST /Usuario/login` - Login

### Perfil (Autenticado)
- `GET /Usuario/perfil` - Ver perfil
- `PUT /Usuario/senha` - Redefinir senha

### Administração (SuperAdmin)
- `GET /Admin/usuarios` - Listar administradores
- `GET /Admin/usuarios/{id}` - Detalhes
- `PUT /Admin/usuarios/{id}/status` - Aprovar/rejeitar/revogar

## Troubleshooting

### Porta já em uso

Se alguma porta estiver em uso, edite o `docker-compose.yml`:

```yaml
ports:
  - "NOVA_PORTA:5042"  # Para o backend
  - "NOVA_PORTA:5173"  # Para o frontend
```

### Problemas com migrations

Entre no container e execute manualmente:

```bash
docker exec -it unb_portal_backend bash
cd /src/Backend
dotnet ef database update
```

### Limpar tudo e recomeçar

```bash
docker-compose down -v
docker system prune -a
docker-compose up -d --build
```

## Contribuindo

1. Crie uma branch para sua feature
2. Faça commit das mudanças
3. Abra um Pull Request

## Licença

Este projeto está sob a licença especificada no arquivo LICENSE.
