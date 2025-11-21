```bash

// Ejemplo 1: apartamento con imágenes
{
  "address": "Cra 15 #123-45, Apt 302",
  "country": "Colombia",
  "city": "Bogotá",
  "housing_type": "apartamento",
  "monthly_rent": 2500000.00,
  "images": [
    "https://example.com/fotos/bogota-apto-302-1.jpg",
    "https://example.com/fotos/bogota-apto-302-2.png"
  ]
}

// Ejemplo 2: casa sin imágenes
{
  "address": "Av. Las Palmas 98",
  "country": "México",
  "city": "Guadalajara",
  "housing_type": "casa",
  "monthly_rent": 18000.50,
  "images": []
}

// Ejemplo 3: local comercial
{
  "address": "Calle 42 #8-10, Local 101",
  "country": "Colombia",
  "city": "Medellín",
  "housing_type": "comercial",
  "monthly_rent": 5200000.00,
  "images": ["https://example.com/fotos/local-101-frente.jpg"]
}

```

- Cuando elimino necesito un mensaje
- Si al hacer un get de los records y esta está vacía deberia darme un error más detallado
- Vistas para el frontend

http://localhost:8080/api/v1/records