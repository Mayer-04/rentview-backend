## Endpoints feature Comments y Guardados

Prefijo global configurado en `settings.app.api_prefix` (por defecto `/api/v1`). Los ejemplos asumen ese prefijo.

### Comentarios sobre reseñas
- `POST /api/v1/reviews/{review_id}/comments`
  - Body: `{"body": "Tu comentario (1-2000 caracteres)"}`.
  - Respuestas: `201` con comentario creado; `404` si la reseña no existe.
- `GET /api/v1/reviews/{review_id}/comments?limit=20&offset=0`
  - Respuestas: `200` con lista ordenada por `created_at DESC`; `404` si la reseña no existe.
- `PUT /api/v1/reviews/{review_id}/comments/{comment_id}`
  - Body: `{"body": "Texto actualizado (1-2000 caracteres)"}`.
  - Respuestas: `200` con el comentario actualizado; `404` si no existe el comentario (o la reseña asociada).
- `DELETE /api/v1/reviews/{review_id}/comments/{comment_id}`
  - Respuestas: `204` si se eliminó; `404` si no existe.

### Guardados de records
- `POST /api/v1/saved-records`
  - Body: `{"record_id": 123}`.
  - Respuestas: `201` si se guardó; `200` si ya estaba guardado (`already_saved=true` en la respuesta); `404` si el record no existe.
- `GET /api/v1/saved-records?limit=50&offset=0`
  - Respuestas: `200` con lista ordenada por `saved_at DESC`.
- `DELETE /api/v1/saved-records/{record_id}`
  - Respuestas: `204` si se eliminó; `404` si no estaba guardado.

### Salud
- `GET /health` → `{"status":"ok"}` (sin prefijo).

## Pasos para ejecutar la aplicación
1) **Configurar entorno**  
   - Requiere Python 3.13 y Postgres accesible.  
   - Crear `.env` con `DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname`.
2) **Instalar dependencias**  
   - `uv sync` (o `pip install -r` equivalente si no usas `uv`).
3) **Crear tablas necesarias**  
   - Ejecutar los SQL de records/reviews (de tu compañero) y luego:  
     - `src/app/features/comments/comments.sql`  
     - `src/app/features/comments/saved_records.sql`
4) **Levantar API**  
   - `uv run fastapi dev src/app/main.py` (por defecto en `http://localhost:8080`).
5) **Probar**  
   - Usa los ejemplos de datos de prueba de abajo o las solicitudes cURL.

## Datos de prueba rápidos

### Inserción mínima en Postgres
```sql
-- Record base
INSERT INTO records (address, country, city, housing_type, monthly_rent)
VALUES ('Calle 123', 'Colombia', 'Bogotá', 'apartamento', 1200000)
RETURNING id;

-- Usa el id devuelto para crear review
INSERT INTO reviews (record_id, title, body, rating)
VALUES (<record_id>, 'Buen lugar', 'Todo correcto, salvo ruido nocturno', 4)
RETURNING id;
```

### Ejemplos de peticiones
```bash
# Crear comentario
curl -X POST http://localhost:8080/api/v1/reviews/1/comments \
  -H "Content-Type: application/json" \
  -d '{"body":"¿El ruido sigue siendo un problema?"}'

# Listar comentarios
curl "http://localhost:8080/api/v1/reviews/1/comments?limit=10&offset=0"

# Actualizar comentario
curl -X PUT http://localhost:8080/api/v1/reviews/1/comments/1 \
  -H "Content-Type: application/json" \
  -d '{"body":"Actualización: el ruido bajó con nuevos vecinos"}'

# Eliminar comentario
curl -X DELETE http://localhost:8080/api/v1/reviews/1/comments/1

# Guardar record
curl -X POST http://localhost:8080/api/v1/saved-records \
  -H "Content-Type: application/json" \
  -d '{"record_id":1}'

# Listar guardados
curl "http://localhost:8080/api/v1/saved-records"

# Eliminar guardado
curl -X DELETE http://localhost:8080/api/v1/saved-records/1
```
