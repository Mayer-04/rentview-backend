# Documentación Reviews

## Configuración rápida

- Requiere Postgres con tablas `records`, `record_images`, `reviews` y `review_images` (ver `src/app/features/reviews/reviews.sql` y el SQL de records).
- Variables en `.env` (`POSTGRES_URL` o `DATABASE_URL`) apuntando a tu base.
- Levantar API: `make run` (carga `.env`) o `uv run fastapi dev src/app/main.py --port 8080`.
- Prefijo de rutas: `/api/v1` (configurable en `settings.app.api_prefix`).

## Endpoints Reviews

- Crear reseña: `POST /api/v1/reviews`
- Listar reseñas de un record: `GET /api/v1/reviews/records/{record_id}?limit=20&offset=0`
- Obtener una reseña: `GET /api/v1/reviews/{review_id}`
- Actualizar reseña: `PUT /api/v1/reviews/{review_id}`
- Eliminar reseña: `DELETE /api/v1/reviews/{review_id}`

### Validaciones clave

- `record_id` debe existir (FK a `records`), `rating` 1–5, `body` no vacío/solo espacios, `title` máx 120 chars.
- En update se exige al menos un campo (`title`, `body` o `rating`).
- Errores esperados: 404 si record/review no existe, 422 si la validación falla, 500 si hay error de BD.

## Datos de prueba (curl)

Sustituye `record_id` y `review_id` por IDs reales presentes en tu base.

### Casos exitosos

```bash
# Crear mínimo (sin título)
curl -X POST http://localhost:8080/api/v1/reviews \
  -H "Content-Type: application/json" \
  -d '{"record_id":1,"title":null,"body":"Buena ubicación","rating":4}'

# Crear con título
curl -X POST http://localhost:8080/api/v1/reviews \
  -H "Content-Type: application/json" \
  -d '{"record_id":2,"title":"Limpio","body":"Todo correcto","rating":5}'

# Listar reseñas de un record
curl http://localhost:8080/api/v1/reviews/records/1?limit=20&offset=0

# Obtener una reseña
curl http://localhost:8080/api/v1/reviews/10

# Actualizar reseña
curl -X PUT http://localhost:8080/api/v1/reviews/10 \
  -H "Content-Type: application/json" \
  -d '{"title":"Nuevo título","body":"Texto actualizado","rating":5}'

# Eliminar reseña
curl -X DELETE http://localhost:8080/api/v1/reviews/10
```

### Casos fallidos (deben responder 4xx)

```bash
# record_id inexistente -> 404
curl -X POST http://localhost:8080/api/v1/reviews \
  -H "Content-Type: application/json" \
  -d '{"record_id":9999,"body":"No importa","rating":4}'

# record_id negativo -> 422
curl -X POST http://localhost:8080/api/v1/reviews \
  -H "Content-Type: application/json" \
  -d '{"record_id":-1,"body":"Texto","rating":3}'

# body vacío -> 422
curl -X POST http://localhost:8080/api/v1/reviews \
  -H "Content-Type: application/json" \
  -d '{"record_id":1,"body":"   ","rating":4}'

# rating fuera de rango -> 422
curl -X POST http://localhost:8080/api/v1/reviews \
  -H "Content-Type: application/json" \
  -d '{"record_id":1,"body":"Texto","rating":0}'

# título >120 chars -> 422
curl -X POST http://localhost:8080/api/v1/reviews \
  -H "Content-Type: application/json" \
  -d '{"record_id":1,"title":"'$(python - <<'PY'; print("x"*121); PY)'","body":"Texto","rating":4}'
```
