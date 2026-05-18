import json
from pathlib import Path

INCIDENTS_FILE = Path(__file__).parent.parent / "data" / "incidents.json"
DECISIONS_FILE = Path(__file__).parent.parent / "data" / "decisions.json"


class IncidentService:

    @staticmethod
    def list_incidents() -> list:
        if INCIDENTS_FILE.exists():
            return json.loads(INCIDENTS_FILE.read_text())
        return []

    @staticmethod
    def get_incident(incident_id: str) -> dict:
        for inc in IncidentService.list_incidents():
            if inc["id"] == incident_id:
                return inc
        return {"error": "Not found"}

    @staticmethod
    def get_rca(incident_id: str) -> dict:
        # Pull RCA from AI decisions if available
        if DECISIONS_FILE.exists():
            decisions = json.loads(DECISIONS_FILE.read_text())
            for dec in decisions:
                if dec.get("deployment_id") == incident_id:
                    analysis = dec.get("llm_analysis", {})
                    return {
                        "incident_id": incident_id,
                        "root_cause": analysis.get("root_cause"),
                        "confidence": analysis.get("confidence"),
                        "affected_services": analysis.get("affected_services"),
                        "reasoning_trace": analysis.get("reasoning_trace"),
                        "recommended_action": analysis.get("recommended_action"),
                        "severity": analysis.get("severity"),
                        "timeline": dec.get("timeline"),
                        "rollback": dec.get("rollback_result"),
                        "generated_at": dec.get("timestamp"),
                    }
        return {"error": "No RCA found for this incident"}
