from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models import Property

router = APIRouter(prefix="/api/properties", tags=["properties"])


class PropertyResponse(BaseModel):
    id: int
    title: str
    price: Optional[float]
    surface: Optional[float]
    exterior_surface: Optional[float]
    rooms: Optional[int]
    bedrooms: Optional[int]
    address: Optional[str]
    city: Optional[str]
    postal_code: Optional[str]
    department: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    description: Optional[str]
    images: Optional[list]
    source: str
    source_url: str
    property_type: Optional[str]
    scraped_at: str
    nearest_train_min: Optional[float]
    nearest_train_name: Optional[str]
    nearest_bus_min: Optional[float]
    nearest_bus_name: Optional[str]
    nearest_tram_min: Optional[float]
    nearest_tram_name: Optional[str]

    model_config = {"from_attributes": True}


class PropertiesListResponse(BaseModel):
    total: int
    page: int
    limit: int
    results: List[PropertyResponse]


@router.get("", response_model=PropertiesListResponse)
async def get_properties(
    # Filtres prix
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    # Filtres surface habitable
    min_surface: Optional[float] = Query(None),
    max_surface: Optional[float] = Query(None),
    # Filtres surface extérieure
    min_exterior: Optional[float] = Query(None),
    max_exterior: Optional[float] = Query(None),
    # Filtres transport (temps de marche max en minutes)
    max_train_walk: Optional[float] = Query(None),
    max_bus_walk: Optional[float] = Query(None),
    max_tram_walk: Optional[float] = Query(None),
    # Département
    department: Optional[str] = Query(None, description="76, 27 ou all"),
    # Type de bien
    property_type: Optional[str] = Query(None, description="Maison, Appartement, Terrain, etc."),
    # Source
    source: Optional[str] = Query(None, description="leboncoin ou pap"),
    # Pagination
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    conditions = []

    if min_price is not None:
        conditions.append(Property.price >= min_price)
    if max_price is not None:
        conditions.append(Property.price <= max_price)
    if min_surface is not None:
        conditions.append(Property.surface >= min_surface)
    if max_surface is not None:
        conditions.append(Property.surface <= max_surface)
    if min_exterior is not None:
        conditions.append(Property.exterior_surface >= min_exterior)
    if max_exterior is not None:
        conditions.append(Property.exterior_surface <= max_exterior)

    if max_train_walk is not None:
        conditions.append(Property.nearest_train_min <= max_train_walk)
    if max_bus_walk is not None:
        conditions.append(Property.nearest_bus_min <= max_bus_walk)
    if max_tram_walk is not None:
        conditions.append(Property.nearest_tram_min <= max_tram_walk)

    if department and department != "all":
        conditions.append(Property.department == department)
    if property_type:
        conditions.append(Property.property_type == property_type)
    if source:
        conditions.append(Property.source == source)

    where_clause = and_(*conditions) if conditions else True

    # Compter le total
    count_query = select(func.count()).select_from(Property).where(where_clause)
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Récupérer les résultats paginés
    offset = (page - 1) * limit
    query = (
        select(Property)
        .where(where_clause)
        .order_by(Property.scraped_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    properties = result.scalars().all()

    return PropertiesListResponse(
        total=total,
        page=page,
        limit=limit,
        results=[_prop_to_response(prop) for prop in properties],
    )


def _prop_to_response(prop: Property) -> PropertyResponse:
    return PropertyResponse(
        id=prop.id,
        title=prop.title or "",
        price=prop.price,
        surface=prop.surface,
        exterior_surface=prop.exterior_surface,
        rooms=prop.rooms,
        bedrooms=prop.bedrooms,
        address=prop.address,
        city=prop.city,
        postal_code=prop.postal_code,
        department=prop.department,
        latitude=prop.latitude,
        longitude=prop.longitude,
        description=prop.description,
        images=prop.images,
        source=prop.source or "",
        source_url=prop.source_url or "",
        property_type=prop.property_type,
        scraped_at=prop.scraped_at.isoformat() if prop.scraped_at else "",
        nearest_train_min=prop.nearest_train_min,
        nearest_train_name=prop.nearest_train_name,
        nearest_bus_min=prop.nearest_bus_min,
        nearest_bus_name=prop.nearest_bus_name,
        nearest_tram_min=prop.nearest_tram_min,
        nearest_tram_name=prop.nearest_tram_name,
    )


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(property_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Bien non trouvé")
    return _prop_to_response(prop)


@router.get("/stats/summary")
async def get_stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count()).select_from(Property))).scalar_one()
    total_76 = (await db.execute(
        select(func.count()).select_from(Property).where(Property.department == "76")
    )).scalar_one()
    total_27 = (await db.execute(
        select(func.count()).select_from(Property).where(Property.department == "27")
    )).scalar_one()
    last_scrape_result = await db.execute(
        select(Property.scraped_at).order_by(Property.scraped_at.desc()).limit(1)
    )
    last_scrape = last_scrape_result.scalar_one_or_none()
    return {
        "total": total,
        "total_76": total_76,
        "total_27": total_27,
        "last_scrape": last_scrape.isoformat() if last_scrape else None,
    }
