# EFData Docker Deployment

## Quick Start

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings (especially database passwords)

3. Build and start the services:
```bash
docker compose up -d
```

4. Initialize the database (first time only):
```bash
docker compose exec efdata-app python -m src.econdata.init_db
```

5. Access the services:
- API: http://localhost:8001
- pgAdmin (debug mode): http://localhost:5050

## Services

- **postgres**: PostgreSQL database (port 5433)
- **efdata-app**: Main application and scheduler
- **efdata-api**: REST API service (port 8001)
- **pgadmin**: Database management UI (optional, port 5050)

## Common Commands

### View logs
```bash
docker compose logs -f efdata-app
```

### Run a one-time data collection
```bash
docker compose exec efdata-app python -m src.econdata.run_spiders
```

### Access the database
```bash
docker compose exec postgres psql -U efdata_user -d efdata
```

### Backup database
```bash
docker compose exec postgres pg_dump -U efdata_user efdata > backup.sql
```

## Production Deployment

For production, use the production compose file:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

This adds:
- Resource limits
- No exposed database ports
- Nginx reverse proxy
- Better security defaults

## Troubleshooting

### Port conflicts
If you get port conflicts, you can change the ports in docker-compose.yml:
- PostgreSQL: Change `5433:5432` to another port
- API: Change `8001:8001` to another port

### Database connection issues
Make sure the database is healthy:
```bash
docker compose ps
docker compose exec postgres pg_isready
```

### Reset everything
```bash
docker compose down -v  # Warning: This deletes all data!
docker compose up -d
```