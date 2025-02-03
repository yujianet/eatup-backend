from fastapi import APIRouter
from .food import router as food_router
from .image_recognition import router as image_recognition_router

router = APIRouter()

router.include_router(food_router)
router.include_router(image_recognition_router)
