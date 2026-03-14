"""Routes pour déclencher et suivre les jobs de scraping."""
import asyncio
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db, AsyncSessionLocal
from app.models import Property, ScrapeJob
from app.transport import find_nearest_transport, geocode_city
from app.scrapers.leboncoin import LeBonCoinScraper
from app.scrapers.pap import PapScraper
from app.scrapers.bienici import BienIciScraper
from app.scrapers.logicimmo import LogicImmoScraper
from app.scrapers.ouestfrance import OuestFranceScraper
from app.scrapers.paruvendu import ParuVenduScraper
from app.scrapers.base import PropertyData

router = APIRouter(prefix="/api/scrape", tags=["scraping"])

# État global du job en cours (simple flag pour usage local)
_current_job_id: Optional[int] = None


class ScrapeRequest(BaseModel):
    source: str = "all"  # "all" | "pap" | "bienici" | "logicimmo" | "ouestfrance" | "paruvendu" | "leboncoin"


class ScrapeJobResponse(BaseModel):
    id: int
    status: str
    source: str
    started_at: Optional[str]
    finished_at: Optional[str]
    properties_found: int
    properties_new: int
    error_message: Optional[str]
    created_at: str


@router.post("")
async def start_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    global _current_job_id

    # Vérifier si un job tourne déjà
    if _current_job_id is not None:
        result = await db.execute(select(ScrapeJob).where(ScrapeJob.id == _current_job_id))
        existing = result.scalar_one_or_none()
        if existing and existing.status == "running":
            return {"message": "Un scraping est déjà en cours", "job_id": _current_job_id}

    # Créer le job
    job = ScrapeJob(source=request.source, status="pending")
    db.add(job)
    await db.commit()
    await db.refresh(job)
    _current_job_id = job.id

    background_tasks.add_task(_run_scraping_job, job.id, request.source)
    return {"message": "Scraping lancé", "job_id": job.id}


@router.get("/status")
async def get_scrape_status(db: AsyncSession = Depends(get_db)):
    global _current_job_id
    if _current_job_id is None:
        return {"status": "idle", "job": None}

    result = await db.execute(select(ScrapeJob).where(ScrapeJob.id == _current_job_id))
    job = result.scalar_one_or_none()
    if not job:
        return {"status": "idle", "job": None}

    return {
        "status": job.status,
        "job": ScrapeJobResponse(
            id=job.id,
            status=job.status,
            source=job.source,
            started_at=job.started_at.isoformat() if job.started_at else None,
            finished_at=job.finished_at.isoformat() if job.finished_at else None,
            properties_found=job.properties_found or 0,
            properties_new=job.properties_new or 0,
            error_message=job.error_message,
            created_at=job.created_at.isoformat(),
        ),
    }


async def _run_scraping_job(job_id: int, source: str):
    """Exécuté en tâche de fond."""
    async with AsyncSessionLocal() as db:
        # Marquer comme démarré
        result = await db.execute(select(ScrapeJob).where(ScrapeJob.id == job_id))
        job = result.scalar_one()
        job.status = "running"
        job.started_at = datetime.utcnow()
        await db.commit()

        try:
            all_properties: List[PropertyData] = []

            # Lancer les scrapers selon la source
            if source in ("all", "pap"):
                print("[Scraping] Démarrage PAP.fr...")
                pap = PapScraper()
                pap_results = await pap.scrape()
                all_properties.extend(pap_results)
                print(f"[Scraping] PAP: {len(pap_results)} annonces trouvées")

            if source in ("all", "leboncoin"):
                print("[Scraping] Démarrage LeBonCoin...")
                lbc = LeBonCoinScraper()
                lbc_results = await lbc.scrape()
                all_properties.extend(lbc_results)
                print(f"[Scraping] LeBonCoin: {len(lbc_results)} annonces trouvées")

            if source in ("all", "bienici"):
                print("[Scraping] Démarrage BienIci...")
                bienici = BienIciScraper()
                bienici_results = await bienici.scrape()
                all_properties.extend(bienici_results)
                print(f"[Scraping] BienIci: {len(bienici_results)} annonces trouvées")

            if source in ("all", "logicimmo"):
                print("[Scraping] Démarrage Logic-Immo...")
                logicimmo = LogicImmoScraper()
                logicimmo_results = await logicimmo.scrape()
                all_properties.extend(logicimmo_results)
                print(f"[Scraping] Logic-Immo: {len(logicimmo_results)} annonces trouvées")

            if source in ("all", "ouestfrance"):
                print("[Scraping] Démarrage Ouestfrance-immo...")
                ouestfrance = OuestFranceScraper()
                ouestfrance_results = await ouestfrance.scrape()
                all_properties.extend(ouestfrance_results)
                print(f"[Scraping] Ouestfrance-immo: {len(ouestfrance_results)} annonces trouvées")

            if source in ("all", "paruvendu"):
                print("[Scraping] Démarrage ParuVendu...")
                paruvendu = ParuVenduScraper()
                paruvendu_results = await paruvendu.scrape()
                all_properties.extend(paruvendu_results)
                print(f"[Scraping] ParuVendu: {len(paruvendu_results)} annonces trouvées")

            # Sauvegarder dans la DB
            new_count = 0
            for prop_data in all_properties:
                new_count += await _save_property(db, prop_data)

            job.status = "done"
            job.properties_found = len(all_properties)
            job.properties_new = new_count
            job.finished_at = datetime.utcnow()
            print(f"[Scraping] Terminé: {len(all_properties)} trouvées, {new_count} nouvelles")

        except Exception as e:
            job.status = "error"
            job.error_message = str(e)[:500]
            job.finished_at = datetime.utcnow()
            print(f"[Scraping] Erreur: {e}")

        await db.commit()


async def _save_property(db: AsyncSession, prop_data: PropertyData) -> int:
    """Sauvegarde un bien en DB. Retourne 1 si nouveau, 0 si déjà existant."""
    # Rejeter les biens hors Seine-Maritime (76) et Eure (27)
    pc = prop_data.postal_code or ""
    if not pc[:2] in ("76", "27"):
        print(f"[Scraping] Ignoré (hors zone) : {prop_data.city} {pc}")
        return 0

    # Corriger le département à partir du code postal réel
    prop_data.department = pc[:2]

    # Vérifier si l'annonce existe déjà
    result = await db.execute(
        select(Property).where(Property.source_url == prop_data.source_url)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return 0

    # Geocoder si nécessaire
    if not prop_data.latitude or not prop_data.longitude:
        if prop_data.city or prop_data.postal_code:
            coords = await geocode_city(
                prop_data.city or "", prop_data.postal_code
            )
            if coords:
                prop_data.latitude, prop_data.longitude = coords
        await asyncio.sleep(1)  # Respecter le rate limit Nominatim

    # Trouver les transports à proximité
    transport_info = {}
    if prop_data.latitude and prop_data.longitude:
        transport_info = await find_nearest_transport(prop_data.latitude, prop_data.longitude)
        await asyncio.sleep(1)  # Respecter le rate limit Overpass

    # Créer l'entrée en DB
    prop = Property(
        **prop_data.to_dict(),
        **transport_info,
    )
    db.add(prop)
    await db.commit()
    return 1
