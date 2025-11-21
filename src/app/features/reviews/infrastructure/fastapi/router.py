from fastapi import APIRouter

from app.features.reviews.infrastructure.fastapi import controllers

reviews_router = APIRouter(prefix="/reviews", tags=["reviews"])

reviews_router.add_api_route(
    "",
    controllers.create_review,
    methods=["POST"],
    response_model=controllers.ReviewResponse,
    status_code=201,
    summary="Crear una nueva reseña",
)
reviews_router.add_api_route(
    "/records/{record_id}",
    controllers.list_reviews_for_record,
    methods=["GET"],
    response_model=list[controllers.ReviewResponse],
    summary="Listar reseñas de una vivienda",
)
reviews_router.add_api_route(
    "/{review_id}",
    controllers.get_review,
    methods=["GET"],
    response_model=controllers.ReviewResponse,
    summary="Obtener una reseña",
)
reviews_router.add_api_route(
    "/{review_id}",
    controllers.update_review,
    methods=["PUT"],
    response_model=controllers.ReviewResponse,
    summary="Actualizar una reseña",
)
reviews_router.add_api_route(
    "/{review_id}",
    controllers.delete_review,
    methods=["DELETE"],
    status_code=204,
    summary="Eliminar una reseña",
)

__all__ = ["reviews_router"]
