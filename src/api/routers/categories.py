"""Category endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import Category
from src.api.deps import get_db

router = APIRouter()


@router.get("/")
def list_categories(db: Session = Depends(get_db)) -> list[dict]:
    categories = db.query(Category).order_by(Category.name).all()
    return [{"id": str(c.id), "name": c.name} for c in categories]
