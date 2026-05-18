from fastapi import APIRouter
from services.incident_service import IncidentService

router = APIRouter()


@router.get("/list")
def list_incidents():
    return IncidentService.list_incidents()


@router.get("/{incident_id}")
def get_incident(incident_id: str):
    return IncidentService.get_incident(incident_id)


@router.get("/{incident_id}/rca")
def get_rca(incident_id: str):
    return IncidentService.get_rca(incident_id)
