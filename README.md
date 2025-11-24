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
  "record_id": 1,
  "title": "Opcional, hasta 120 caracteres",
  "email": "inquilino@example.com",
  "body": "Texto libre (1-10000 caracteres)",
  "rating": 1-5,
  "images": ["https://ejemplo.com/foto1.jpg", "https://ejemplo.com/foto2.png"]
}
```

- **Respuesta 201**: objeto `ReviewResponse` con `id`, `record_id`, `title`, `email`, `body`, `rating`, `images`, `created_at`, `updated_at`.
- **Errores**:
  - 404 si el `record_id` no existe.
  - 422 si el correo, el texto o la calificación no cumplen las validaciones.

### Obtener una reseña

- **GET** `/api/v1/reviews/{review_id}`
- **Respuesta 200**: `ReviewResponse`.
- **Errores**: 404 si el `review_id` no existe.

### Listar reseñas de un record

- **GET** `/api/v1/reviews/records/{record_id}?page=1&page_size=20`
- **Query params**:
  - `page` (>=1)
  - `page_size` (1-100)
- **Respuesta 200**: lista de `ReviewResponse`.

### Actualizar reseña

- **PUT** `/api/v1/reviews/{review_id}`
- **Body** (todos los campos opcionales):

```json
{
  "title": "Nuevo título",
  "email": "nuevo-correo@example.com",
  "body": "Nuevo texto",
  "rating": 4,
  "images": ["https://...jpg"] // omite para mantener, envía lista vacía para eliminar todas
}
```

- **Respuesta 200**: `ReviewResponse` actualizado.
- **Errores**: 404 si no existe, 422 si `rating` inválido.

### Eliminar reseña

- **DELETE** `/api/v1/reviews/{review_id}`
- **Respuesta 204** sin body.
- **Errores**: 404 si no existe.

### Imágenes de reseña

- Incluye las URLs en el campo `images` al crear una reseña (`POST /api/v1/reviews`).
- Endpoints específicos:
  - `POST /api/v1/reviews/{review_id}/images` → Body: `{"image_url":"https://...jpg|png"}`. Respuesta `201` con `ReviewImageResponse`.
  - `DELETE /api/v1/reviews/{review_id}/images/{image_id}` → Respuesta `204`.
- Las respuestas de `/api/v1/reviews` y `/api/v1/reviews/{review_id}` devuelven el arreglo de imágenes con `id`, `review_id`, `image_url` y `created_at`.

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

- Autenticación/autorización no está implementada aún.
- Todas las rutas dependen de una base PostgreSQL con las tablas declaradas en `src/app/features/reviews/reviews.sql`.
- Para probar manualmente, levanta la app (`uv run fastapi dev src/app/main.py`) y realiza peticiones HTTP al host configurado (por defecto `http://localhost:8080`).

## Docker

No hace falta. Quédate en la raíz del proyecto y apunta al archivo que está en docker/ usando -f (Dockerfile) o -f de compose. Ejemplos:

- Imagen dev: `docker build -f docker/Dockerfile.dev -t arrendamos-dev .`
- Compose dev: `docker compose -f docker/docker-compose.dev.yml up --build`

## Observaciones

- `record_id` debe existir en la tabla `records` (llave foránea en `src/app/features/reviews/reviews.sql` y `tablas.sql`).
- El campo `email` es obligatorio, se valida con un patrón estricto y se limita a 320 caracteres.
- `body` debe venir con texto no vacío y `rating` solo admite valores entre 1 y 5.
- Autenticación/autorización no está implementada aún.
