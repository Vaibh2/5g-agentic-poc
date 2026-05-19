from fastapi import APIRouter, Query
from services.deployment_service import DeploymentService

router = APIRouter()


@router.post("/trigger")
def trigger_deployment(config_name: str = "routing-config-v24"):
    result = DeploymentService.trigger_deployment(config_name)
    from services.slack_notification import send_deployment_alert
    send_deployment_alert(
        deployment_id=result["deployment_id"],
        config_name=result["config_name"],
        status="success"
    )
    return result


@router.post("/trigger-failed")
def trigger_failed_deployment(
    config_name: str = "routing-config-v24",
    error_message: str = Query("Configuration validation failed")
):
    return DeploymentService.trigger_failed_deployment(config_name, error_message)


@router.get("/list")
def list_deployments():
    return DeploymentService.list_deployments()


@router.get("/{deployment_id}")
def get_deployment(deployment_id: str):
    return DeploymentService.get_deployment(deployment_id)
