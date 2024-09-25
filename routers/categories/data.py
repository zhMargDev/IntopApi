from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.models import Category
from schemas.category import CategoryOut
from documentation.categories import data as categories_documentation

router = APIRouter()

# Роутер для получения всех категорий с их подкатегориями
@router.get('/all', response_model=List[CategoryOut],
            summary="Получение всех категгори и вложенных подкатегорий.",
            description=categories_documentation.get_all_categories)
async def get_all_categories(db: AsyncSession = Depends(get_db)):
    async def fetch_categories(parent_id: int = None):
        query = select(Category).filter(Category.parent_id == parent_id)
        result = await db.execute(query)
        categories = result.scalars().all()
        result_list = []
        for category in categories:
            children = await fetch_categories(parent_id=category.id)
            result_list.append(CategoryOut(
                id=category.id,
                name=category.name,
                subcategories=children
            ))
        return result_list

    return await fetch_categories()

# Роутер для получения категории по id с её подкатегориями
@router.get('/by_id/{category_id}', response_model=CategoryOut,
            summary="Получение категории и его субкатегорий по id",
            description=categories_documentation.get_category_by_id)
async def get_category_by_id(category_id: int, db: AsyncSession = Depends(get_db)):
    async def fetch_category_with_subcategories(category_id: int):
        query = select(Category).filter(Category.id == category_id)
        result = await db.execute(query)
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        subcategories = await fetch_categories(parent_id=category.id)
        return CategoryOut(
            id=category.id,
            name=category.name,
            subcategories=subcategories
        )

    async def fetch_categories(parent_id: int):
        query = select(Category).filter(Category.parent_id == parent_id)
        result = await db.execute(query)
        categories = result.scalars().all()
        result_list = []
        for category in categories:
            children = await fetch_categories(parent_id=category.id)
            result_list.append(CategoryOut(
                id=category.id,
                name=category.name,
                subcategories=children
            ))
        return result_list

    return await fetch_category_with_subcategories(category_id)