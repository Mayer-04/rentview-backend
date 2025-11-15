uv lock --upgrade
uv lock --upgrade --refresh
uv sync

## Feature: Reviews API

Todos los endpoints expuestos por la feature de reseñas están montados bajo el prefijo configurado en `settings.app.api_prefix` (por defecto `/api/v1`). Cada respuesta devuelve JSON con los atributos descritos en las clases de respuesta del controller.

### Crear una reseña

- **POST** `/api/v1/reviews`
- **Body**:

```json
{
  "record_id": "uuid",
  "user_id": "uuid",
  "rent_amount": 950.0,
  "review_text": "Texto libre (1-10000 caracteres)",
  "rating": 1-5,
  "image_urls": ["https://..."]  // opcional
}
```

- **Respuesta 201**: objeto `ReviewResponse` con `id`, `record_id`, `user_id`, `rent_amount`, `review_text`, `rating`, `created_at`.
- **Errores**:
  - 409 si el usuario ya reseñó ese record.
  - 422 si la calificación está fuera del rango permitido.

### Obtener una reseña

- **GET** `/api/v1/reviews/{review_id}`
- **Respuesta 200**: `ReviewResponse`.
- **Errores**: 404 si el `review_id` no existe.

### Listar reseñas de un record

- **GET** `/api/v1/reviews/record/{record_id}?limit=20&offset=0`
- **Query params**:
  - `limit` (1-100)
  - `offset` (>=0)
- **Respuesta 200**: lista de `ReviewResponse`.

### Actualizar reseña

- **PUT** `/api/v1/reviews/{review_id}`
- **Body** (todos los campos opcionales):

```json
{
  "rent_amount": 975.0,
  "review_text": "Nuevo texto",
  "rating": 4
}
```

- **Respuesta 200**: `ReviewResponse` actualizado.
- **Errores**: 404 si no existe, 422 si `rating` inválido.

### Eliminar reseña

- **DELETE** `/api/v1/reviews/{review_id}`
- **Respuesta 204** sin body.
- **Errores**: 404 si no existe.

### Imágenes de reseña

- **POST** `/api/v1/reviews/{review_id}/images`
  - **Body**: `{ "image_url": "https://..." }`
  - **Respuesta 201**: `ReviewImageResponse` (`id`, `review_id`, `image_url`, `uploaded_at`).
- **GET** `/api/v1/reviews/{review_id}/images`
  - **Respuesta 200**: lista de `ReviewImageResponse`.
- **Errores**: 404 si la reseña no existe.

### Comentarios en reseña

- **POST** `/api/v1/reviews/{review_id}/comments`
  - **Body**:

```json
{
  "user_id": "uuid",
  "comment_text": "Hasta 2000 caracteres"
}
```

- **Respuesta 201**: `ReviewCommentResponse`.
- **GET** `/api/v1/reviews/{review_id}/comments?limit=20&offset=0`
  - **Respuesta 200**: lista de `ReviewCommentResponse`.
- **Errores**: 404 si la reseña no existe.

### Votos de utilidad

- **POST** `/api/v1/reviews/{review_id}/votes`
  - **Body**: `{ "user_id": "uuid", "useful": true }`
  - **Respuesta 201**: `ReviewVoteResponse`.
- **GET** `/api/v1/reviews/{review_id}/votes/summary`
  - **Respuesta 200**:

```json
{
  "review_id": "uuid",
  "useful_votes": 3,
  "not_useful_votes": 1
}
```

### Notas de uso

- Autenticación/autorización no está implementada aún; debes inyectar `user_id` manualmente.
- Todas las rutas dependen de una base PostgreSQL con las tablas declaradas en `src/app/features/reviews/review.sql`.
- Para probar manualmente, levanta la app (`uv run fastapi dev src/app/main.py`) y realiza peticiones HTTP al host configurado (por defecto `http://localhost:8080`).

## Docker

No hace falta. Quédate en la raíz del proyecto y apunta al archivo que está en docker/ usando -f (Dockerfile) o -f de compose. Ejemplos:

- Imagen dev: `docker build -f docker/Dockerfile.dev -t arrendamos-dev .`
- Compose dev: `docker compose -f docker/docker-compose.dev.yml up --build`

## Observaciones

Para crear una reseña vía POST /api/v1/reviews solo necesitas valores UUID válidos (formato estándar xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx) en los campos record_id y user_id. El controller (src/app/features/reviews/infrastructure/fastapi/controller.py (lines 82-127)) valida únicamente que sean UUID y delega al repositorio; no hay firma digital ni token adicional en este flujo.
Lo único imprescindible es que esos UUID existan en las tablas records y users porque PostgreSQL tiene llaves foráneas (ver review.sql y las columnas con REFERENCES ... ON DELETE CASCADE). Si envías IDs inventados que no existan en la base, obtendrás un error de integridad desde la base de datos.
En pruebas locales puedes generar IDs con uuidgen o la librería uuid de Python, siempre y cuando insertes los registros correspondientes en users y records antes de llamar al endpoint.
d9428888-122b-4f5b-89f0-0c5bdae75a5b
