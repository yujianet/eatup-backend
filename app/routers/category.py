from fastapi import APIRouter
from ..data import category_presets

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("")
def get_all_categories():
    return category_presets