#!/bin/bash

set -e

case "$1" in
  start)
    echo "Iniciando serviços..."
    docker-compose up -d
    echo "Serviços iniciados!"
    echo "Frontend: http://localhost:5173"
    echo "Backend: http://localhost:5042"
    echo "Swagger: http://localhost:5042/swagger"
    ;;
  
  stop)
    echo "Parando serviços..."
    docker-compose down
    echo "Serviços parados!"
    ;;
  
  restart)
    echo "Reiniciando serviços..."
    docker-compose down
    docker-compose up -d
    echo "Serviços reiniciados!"
    ;;
  
  rebuild)
    echo "Reconstruindo e iniciando serviços..."
    docker-compose up -d --build
    echo "Serviços reconstruídos e iniciados!"
    ;;
  
  logs)
    if [ -z "$2" ]; then
      docker-compose logs -f
    else
      docker-compose logs -f "$2"
    fi
    ;;
  
  status)
    docker-compose ps
    ;;
  
  clean)
    echo "Limpando containers, volumes e imagens..."
    docker-compose down -v
    docker system prune -a -f
    echo "Limpeza concluída!"
    ;;
  
  reset)
    echo "Resetando banco de dados..."
    docker-compose down
    docker volume rm tcc_postgres_data 2>/dev/null || true
    docker-compose up -d
    echo "Banco de dados resetado!"
    ;;
  
  backend-shell)
    docker exec -it unb_portal_backend bash
    ;;
  
  frontend-shell)
    docker exec -it unb_portal_frontend sh
    ;;
  
  db-shell)
    docker exec -it unb_portal_postgres psql -U postgres -d unb_portal_dev
    ;;
  
  migration)
    if [ -z "$2" ]; then
      echo "Uso: ./docker.sh migration <nome-da-migration>"
      exit 1
    fi
    docker exec -it unb_portal_backend dotnet ef migrations add "$2" --project /src/Backend
    echo "Migration '$2' criada!"
    ;;
  
  migrate)
    echo "Aplicando migrations..."
    docker exec -it unb_portal_backend dotnet ef database update --project /src/Backend
    echo "Migrations aplicadas!"
    ;;
  
  backup)
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    echo "Criando backup em $BACKUP_FILE..."
    docker exec unb_portal_postgres pg_dump -U postgres unb_portal_dev > "$BACKUP_FILE"
    echo "Backup criado: $BACKUP_FILE"
    ;;
  
  restore)
    if [ -z "$2" ]; then
      echo "Uso: ./docker.sh restore <arquivo-backup.sql>"
      exit 1
    fi
    echo "Restaurando backup de $2..."
    docker exec -i unb_portal_postgres psql -U postgres unb_portal_dev < "$2"
    echo "Backup restaurado!"
    ;;
  
  help|*)
    echo "Uso: ./docker.sh <comando> [argumentos]"
    echo ""
    echo "Comandos disponíveis:"
    echo "  start              - Inicia todos os serviços"
    echo "  stop               - Para todos os serviços"
    echo "  restart            - Reinicia todos os serviços"
    echo "  rebuild            - Reconstrói e inicia os serviços"
    echo "  logs [servico]     - Mostra logs (todos ou de um serviço específico)"
    echo "  status             - Mostra status dos containers"
    echo "  clean              - Remove containers, volumes e imagens"
    echo "  reset              - Reseta o banco de dados"
    echo "  backend-shell      - Acessa shell do backend"
    echo "  frontend-shell     - Acessa shell do frontend"
    echo "  db-shell           - Acessa psql do PostgreSQL"
    echo "  migration <nome>   - Cria nova migration"
    echo "  migrate            - Aplica migrations pendentes"
    echo "  backup             - Cria backup do banco de dados"
    echo "  restore <arquivo>  - Restaura backup do banco de dados"
    echo "  help               - Mostra esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  ./docker.sh start"
    echo "  ./docker.sh logs unb-portal-backend"
    echo "  ./docker.sh migration AddNewField"
    echo "  ./docker.sh backup"
    ;;
esac
