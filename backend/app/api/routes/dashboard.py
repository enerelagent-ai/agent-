from analytics.calculations import investment_summary_by_district_conn
from fastapi import APIRouter

from app.config import settings
from app.schemas.dashboard import DistrictInvestmentSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/investment-summary", response_model=list[DistrictInvestmentSummary])
def investment_summary() -> list[dict]:
    return investment_summary_by_district_conn(settings.database_url)
