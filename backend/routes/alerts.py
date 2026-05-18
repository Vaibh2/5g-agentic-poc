from fastapi import APIRouter
from services.monitoring_service import MonitoringService

router = APIRouter()


@router.get("/current")
def get_current_alerts():
    return MonitoringService.get_active_alerts()


@router.get("/history")
def get_alert_history():
    return MonitoringService.get_alert_history()


@router.post("/simulate-spike")
def simulate_spike():
    return MonitoringService.inject_anomaly()
