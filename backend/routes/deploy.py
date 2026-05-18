from fastapi import APIRouter
from services.deployment_service import DeploymentService

router = APIRouter()


@router.post("/trigger")
def trigger_deployment(config_name: str = "routing-config-v24"):
    return DeploymentService.trigger_deployment(config_name)


@router.get("/list")
def list_deployments():
    return DeploymentService.list_deployments()


@router.get("/{deployment_id}")
def get_deployment(deployment_id: str):
    return DeploymentService.get_deployment(deployment_id)
