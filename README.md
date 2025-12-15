# Rentview backend (FastAPI + PostgreSQL)

Backend modular con FastAPI y PostgreSQL para gestionar viviendas (records), reseñas, comentarios y guardados. Sigue un enfoque de _vertical slicing_ por feature (`records`, `reviews`, `comments`) y separa dominio, aplicación e infraestructura.

## Stack y arquitectura

- Python 3.13, FastAPI, SQLAlchemy 2, Pydantic v2, PostgreSQL (psycopg3), uv para gestión de dependencias.
- Estructura por feature: `src/app/features/<feature>/{domain,application,infrastructure}`. Código compartido en `src/app/shared` (DB, settings, email, paginación, logging).
- API documentada automáticamente en `/docs` o `/redoc` (prefijo configurable con `settings.app.api_prefix`, por defecto `/api/v1`).

## Requisitos previos

- Python 3.13 y [uv](https://github.com/astral-sh/uv) instalados. Alternativa: `python -m venv` + `pip`, ajustando los comandos.
- PostgreSQL accesible o Docker para levantarlo localmente.
- Opcional: `make` y Docker Compose.

## Configuración rápida

1. **Variables de entorno**: copia `.env.example` a `.env` y completa al menos `DATABASE_URL` o `POSTGRES_URL`. Ejemplo:

```bash
   APP_ENV=local
   PORT=8080
   DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/rentview
   EMAIL_ENABLED=false  # desactiva envío de correos en desarrollo
```

2. **Dependencias**: `uv sync` (o `make install`). Creará `.venv` local.
3. **Base de datos**: crea la base y tablas con los scripts de `db_scripts` (o los SQL específicos en cada feature). Con Docker Compose se aplican automáticamente al iniciar el contenedor de Postgres.
4. **Levantar API (dev)**: `make run` carga `.env` y ejecuta `fastapi dev src/app/main.py` en `http://localhost:8080`. Sin `make`: `uv run fastapi dev src/app/main.py --host 0.0.0.0 --port 8080`.
5. **Docker Compose**: `docker compose up --build` (usa `docker-compose.yml`, expone FastAPI en `${PORT:-8080}` y Postgres en `${POSTGRES_PORT:-5432}` con datos de `db_scripts`).

## Variables importantes

- `DATABASE_URL` / `POSTGRES_URL`: cadena SQLAlchemy, ej. `postgresql+psycopg://user:pass@host:5432/dbname`.
- `APP_ENV`, `APP_DEBUG`, `PORT`: controlan entorno, modo debug y puerto de FastAPI.
- Pool BD: `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, `DATABASE_POOL_TIMEOUT` (ver `src/app/shared/infrastructure/settings.py`).
- Email (opcional): `EMAIL_ENABLED`, `EMAIL_PROVIDER=smtp`, `EMAIL_FROM`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `SMTP_USE_SSL`, `SMTP_TIMEOUT`. Si `EMAIL_ENABLED=false`, los correos se omiten.
- CORS: por defecto permite `http://localhost:{5173,5174,5175,5000,8000}`; ajustable en `settings.cors`.

## Endpoints principales

### Salud

- `GET /health` → `{ "status": "ok" }` (sin prefijo).

### Records (viviendas) — prefijo `/api/v1/records`

- `POST /records`: crea record con `address`, `country`, `city`, `housing_type` (`apartamento|casa|comercial`), `monthly_rent` > 0 y `images` opcionales (.jpg/.png).
- `GET /records?page=1&page_size=20`: lista paginada (`items` + `meta` con `totalPages`).
- `GET /records/{record_id}`: detalle con imágenes, `reviews_count` y `average_rating` derivados.
- `PUT /records/{record_id}`: actualiza campos; al menos uno es obligatorio. `images=[]` reemplaza todas; omitirlo conserva.
- `DELETE /records/{record_id}`: elimina record y sus imágenes (cascada).
  Errores comunes: 404 si no existe, 422 si faltan campos o imágenes no son .jpg/.png.

### Reviews — prefijo `/api/v1/reviews`

- `POST /reviews`: crea reseña (`record_id` debe existir, `email` válido ≤320 chars, `body` no vacío, `rating` 1–5, `images` .jpg/.png). Envía correo si está configurado `EMAIL_ENABLED`.
- `GET /reviews/records/{record_id}?page=1&page_size=20`: lista reseñas de un record (404 si no hay datos para la página solicitada).
- `GET /reviews/{review_id}`: detalle.
- `PUT /reviews/{review_id}`: actualiza (se exige al menos un campo). `images=[]` reemplaza; omitirlo conserva.
- `DELETE /reviews/{review_id}`.
- `POST /reviews/{review_id}/images`: agrega imagen (.jpg/.png).
- `DELETE /reviews/{review_id}/images/{image_id}`.
  Errores comunes: 404 si record/review no existe, 422 si validación falla.

### Comments & saved records — prefijos `/api/v1/reviews/{review_id}/comments` y `/api/v1/saved-records`

- `POST /reviews/{review_id}/comments`: cuerpo 1–2000 chars.
- `GET /reviews/{review_id}/comments?page=1&page_size=20`.
- `PUT /reviews/{review_id}/comments/{comment_id}` y `DELETE` correspondiente.
- `POST /saved-records`: guarda un record; si ya estaba, responde 200 con `already_saved=true`.
- `GET /saved-records?page=1&page_size=50`, `DELETE /saved-records/{record_id}`.
  Errores comunes: 404 si review/record no existe, 422 si la paginación es inválida.

## Base de datos y seeds

- Esquemas mínimos por feature: `src/app/features/records/records.sql`, `src/app/features/reviews/...` (ver `db_scripts/01_tables.sql`), `src/app/features/comments/comments.sql`, `src/app/features/comments/saved_records.sql`.
- Datos de muestra en `db_scripts/02_records.sql`, `03_reviews.sql`, `04_comments.sql`, `05_saved_records.sql`. Con Docker Compose se cargan automáticamente en el contenedor de Postgres.

## Calidad y comandos útiles

- Lint: `make lint` / autocorrección `make fix` / formato `make fmt` (Ruff).
- Tipado: `make typecheck` (mypy).
- Tests: `make test` o `make cov` para cobertura. Reporte HTML en `htmlcov/index.html`.
- Pipeline local: `make check` (lint + typecheck + tests) o `make precommit` si usas pre-commit hooks.

## Notas de diseño y buenas prácticas

- Mantén la separación por capas: los controladores FastAPI solo adaptan requests/responses; la lógica vive en servicios de aplicación y dominio.
- Reutiliza los DTO/commands definidos por feature en lugar de pasar diccionarios sin tipar.
- Usa las validaciones de los servicios (rating, email, URLs de imagen) antes de persistir para mantener las reglas de negocio coherentes con la BD.
- Para nuevos endpoints, replica la estructura `domain/` (modelos + excepciones) → `application/` (DTOs/commands + servicios) → `infrastructure/` (repositorios y controladores).
