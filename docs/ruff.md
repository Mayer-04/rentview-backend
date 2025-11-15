# Documentación

## Ruff

Ruff es dos herramientas en una:

- Linter: detecta problemas (errores comunes, imports no usados, malas prácticas, etc.).
- Formatter: formatea tu código como lo haría Black, pero más rápido y con algunas opciones extra.

## Importaciones

- Usar importaciones **absolutas**.

```python
from app.domain.models import User
```

- Usar importaciones **relativas** solo dentro del mismo paquete.

```python
from .models import User
```

## Comandos Makefile

| Comando          | Descripción                                         | Ejemplo de uso   |
| ---------------- | --------------------------------------------------- | ---------------- |
| `make help`      | Muestra la ayuda con todos los comandos disponibles | `make help`      |
| `make run`       | Inicia el servidor FastAPI en modo desarrollo       | `make run`       |
| `make lint`      | Ejecuta Ruff para análisis de código                | `make lint`      |
| `make fix`       | Corrige problemas automáticamente con Ruff          | `make fix`       |
| `make fmt`       | Formatea el código con Ruff                         | `make fmt`       |
| `make test`      | Ejecuta los tests con pytest                        | `make test`      |
| `make clean`     | Elimina archivos temporales y cachés                | `make clean`     |
| `make check`     | Ejecuta lint y test (ideal para CI/CD)              | `make check`     |
| `make precommit` | Corrección + formato + tests antes de hacer commit  | `make precommit` |

## Routes

La ubicación de las rutas (routes) depende del rol que cumplen en la aplicación. Las rutas no forman parte del dominio, sino de la capa de infraestructura, porque son un mecanismo de entrada/salida.

los routes van en los adaptadores de entrada, como parte de la infraestructura, nunca dentro del dominio.

### ¿Por qué los routes son adaptadores de entrada?

- En hexagonal, un adaptador de entrada es cualquier mecanismo que permite que un estímulo externo (ej. un request HTTP) se traduzca en una llamada a un puerto de la aplicación (caso de uso).

- El router o controlador HTTP cumple exactamente esa función:
  - Recibe la petición HTTP (mundo externo).
  - Transforma parámetros/headers/body en un comando o DTO comprensible para el dominio.
  - Llama al servicio de aplicación (un puerto expuesto por el dominio).
  - Devuelve la respuesta al mundo externo.

## Backend

- Arquitectura Hexagonal y Vertical Slicing (Screaming architecture)
- Patrones de diseño: Repository, Factory, DDD (Muchos patrones de diseño)

## Más facil

- Modelo, Vista, Controlador (MVC)
- Casi no utilizamos patrones de diseño (aunque el profesor lo pide)
