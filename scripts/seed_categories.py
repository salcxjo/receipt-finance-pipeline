"""Seed the fixed v1 category taxonomy (see SRS §8 open questions).

Run once against a fresh DB: python -m scripts.seed_categories
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.models import Category
from src.common.config import settings

DEFAULT_CATEGORIES = [
    "Groceries",
    "Dining",
    "Transport",
    "Utilities",
    "Entertainment",
    "Health",
    "Household",
    "Clothing",
    "Electronics",
    "Personal Care",
    "Subscriptions",
    "Travel",
    "Gifts",
    "Education",
    "Other",
]


def main() -> None:
    engine = create_engine(settings.database_url)
    with Session(engine) as session:
        existing = {c.name for c in session.query(Category).all()}
        for name in DEFAULT_CATEGORIES:
            if name not in existing:
                session.add(Category(name=name))
        session.commit()
    print(f"Seeded {len(DEFAULT_CATEGORIES)} categories.")


if __name__ == "__main__":
    main()
