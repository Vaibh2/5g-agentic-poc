import uuid
import json
import random
from datetime import datetime
from pathlib import Path

from services.slack_notification import send_deployment_alert, send_rollback_alert

DATA_FILE = Path(__file__).parent.parent / "data" / "deployments.json"


def _load():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return []


def _save(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, indent=2))


CONFIG_DIFFS = {
    "routing-config-v24": {
        "change_summary": "Optimized MTU size from 1500 to 9000 for jumbo frames",
        "files_changed": ["network/routing.tf", "network/mtu_settings.tf"],
        "lines_added": 14,
        "lines_removed": 3,
        "risk_level": "HIGH",
        "diff_snippet": """
- mtu_size = 1500
+ mtu_size = 9000
+ enable_jumbo_frames = true
+ fragmentation_policy = "none"
        """.strip(),
    },
    "routing-config-v23": {
        "change_summary": "Added BGP route optimization for sector 7",
        "files_changed": ["network/bgp.tf"],
        "lines_added": 6,
        "lines_removed": 2,
        "risk_level": "MEDIUM",
        "diff_snippet": """
+ bgp_route_preference = "sector_7_primary"
+ failover_timeout = 30
        """.strip(),
    },
}


class DeploymentService:

    @staticmethod
    def trigger_deployment(config_name: str) -> dict:
        deployments = _load()
        dep_id = f"dep_{uuid.uuid4().hex[:6].upper()}"
        config_diff = CONFIG_DIFFS.get(config_name, CONFIG_DIFFS["routing-config-v24"])
        deployment = {
            "deployment_id": dep_id,
            "config_name": config_name,
            "config_version": f"v{random.randint(20, 30)}",
            "status": "deploying",
            "timestamp": datetime.utcnow().isoformat(),
            "deployed_by": "ci-pipeline",
            "diff": config_diff,
            "logs": [
                f"[{datetime.utcnow().isoformat()}] Initiating deployment {dep_id}",
                f"[{datetime.utcnow().isoformat()}] Applying Terraform config: {config_name}",
                f"[{datetime.utcnow().isoformat()}] Pushing to 5G tower cluster: SECTOR-7",
                f"[{datetime.utcnow().isoformat()}] Config propagated to 48 nodes",
            ],
        }
        deployments.append(deployment)
        _save(deployments)
        return deployment

    @staticmethod
    def list_deployments() -> list:
        return list(reversed(_load()))

    @staticmethod
    def get_deployment(deployment_id: str) -> dict:
        for dep in _load():
            if dep["deployment_id"] == deployment_id:
                return dep
        return {"error": "Not found"}

    @staticmethod
    def mark_rolled_back(deployment_id: str):
        deployments = _load()
        for dep in deployments:
            if dep["deployment_id"] == deployment_id:
                dep["status"] = "rolled_back"
                dep["rollback_timestamp"] = datetime.utcnow().isoformat()
                send_rollback_alert(
                    deployment_id=dep["deployment_id"],
                    config_name=dep.get("config_name", "unknown"),
                    reason="Deployment failed - automatic rollback"
                )
        _save(deployments)

    @staticmethod
    def trigger_failed_deployment(config_name: str, error_message: str = "Configuration validation failed") -> dict:
        deployments = _load()
        dep_id = f"dep_{uuid.uuid4().hex[:6].upper()}"
        config_diff = CONFIG_DIFFS.get(config_name, CONFIG_DIFFS["routing-config-v24"])
        deployment = {
            "deployment_id": dep_id,
            "config_name": config_name,
            "config_version": f"v{random.randint(20, 30)}",
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "deployed_by": "ci-pipeline",
            "diff": config_diff,
            "error_message": error_message,
            "logs": [
                f"[{datetime.utcnow().isoformat()}] Initiating deployment {dep_id}",
                f"[{datetime.utcnow().isoformat()}] Applying Terraform config: {config_name}",
                f"[{datetime.utcnow().isoformat()}] ERROR: {error_message}",
            ],
        }
        deployments.append(deployment)
        _save(deployments)

        send_deployment_alert(
            deployment_id=dep_id,
            config_name=config_name,
            status="failed",
            error_message=error_message
        )

        return deployment
