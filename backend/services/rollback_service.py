import asyncio
from datetime import datetime
from services.deployment_service import DeploymentService
from services.monitoring_service import MonitoringService


class RollbackService:

    @staticmethod
    async def execute(deployment_id: str) -> dict:
        await asyncio.sleep(1)  # Simulate rollback time

        DeploymentService.mark_rolled_back(deployment_id)
        MonitoringService.restore_baseline()

        return {
            "rollback_id": f"RBK_{datetime.utcnow().strftime('%H%M%S')}",
            "deployment_id": deployment_id,
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Previous stable configuration restored. Network metrics normalized.",
            "recovery_actions": [
                "Reverted routing config to last stable version",
                "MTU reset to 1500 across all nodes",
                "BGP routes re-converged",
                "Monitoring confirmed baseline restoration",
            ],
        }
