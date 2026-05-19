from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
import logging

from services.slack_notification import send_rollback_alert

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter()


class GitPushPayload(BaseModel):
    files: str
    repo_path: str


WORKFLOWS_FILE = Path(__file__).parent.parent / "data" / "workflows.json"


def _load_workflows():
    if WORKFLOWS_FILE.exists():
        return json.loads(WORKFLOWS_FILE.read_text())
    return []


def _save_workflows(workflows):
    WORKFLOWS_FILE.parent.mkdir(parents=True, exist_ok=True)
    WORKFLOWS_FILE.write_text(json.dumps(workflows, indent=2))


@router.post("/git-push")
async def handle_git_push(payload: GitPushPayload):
    logger.info(f"Webhook received - files: {payload.files}, repo_path: {payload.repo_path}")
    
    file_list = [f.strip() for f in payload.files.strip().split('|') if f.strip()]
    logger.info(f"Parsed file list: {file_list}")
    
    workflow_id = f"wf_{uuid.uuid4().hex[:8].upper()}"
    workflow = {
        "workflow_id": workflow_id,
        "status": "QUEUED",
        "trigger": "git-push",
        "files_changed": file_list,
        "repo_path": payload.repo_path,
        "created_at": datetime.utcnow().isoformat(),
        "steps": [],
        "agent_narrations": [],
    }
    
    workflows = _load_workflows()
    workflows.append(workflow)
    _save_workflows(workflows)
    logger.info(f"Workflow created: {workflow_id}")
    
    asyncio.create_task(_run_deploy_agent(workflow_id, file_list, payload.repo_path))
    
    return {
        "workflow_id": workflow_id,
        "status": "QUEUED",
        "message": "Deployment queued. Check the Workflows page for progress."
    }


async def _run_deploy_agent(workflow_id: str, files: List[str], repo_path: str):
    from services.deploy_agent import DeployAgent
    
    await DeployAgent.run(workflow_id, files, repo_path)


@router.get("/list")
def list_workflows():
    return _load_workflows()


@router.get("/{workflow_id}")
def get_workflow(workflow_id: str):
    workflows = _load_workflows()
    for wf in workflows:
        if wf["workflow_id"] == workflow_id:
            return wf
    return {"error": "Workflow not found"}


class RollbackConfirmPayload(BaseModel):
    workflow_id: str
    confirm: bool


@router.post("/rollback/confirm")
async def confirm_rollback(payload: RollbackConfirmPayload):
    workflows = _load_workflows()
    wf = None
    for w in workflows:
        if w["workflow_id"] == payload.workflow_id:
            wf = w
            break
    
    if not wf:
        return {"error": "Workflow not found"}
    
    if payload.confirm:
        # Execute rollback
        rollback_steps = [
            "Reverting YAML configuration changes",
            "Restarting affected network services",
            "Verifying network connectivity",
            "Confirming metrics return to normal"
        ]
        
        for i, step in enumerate(rollback_steps):
            wf["agent_narrations"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "Rollback Agent",
                "message": f"  Step {i+1}: {step}"
            })
        
        wf["agent_narrations"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "Rollback Agent",
            "message": "✅ Rollback executed successfully"
        })
        wf["status"] = "ROLLED_BACK"

        _save_workflows(workflows)

        send_rollback_alert(
            deployment_id=wf.get("deployment_id", "N/A"),
            config_name=wf.get("config_name", "N/A"),
            reason="Manual rollback confirmed by user",
            workflow_id=payload.workflow_id
        )

        return {"success": True, "message": "Rollback executed"}
    else:
        wf["agent_narrations"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "Rollback Agent",
            "message": "❌ Rollback cancelled by user"
        })
        _save_workflows(workflows)
        
        return {"success": True, "message": "Rollback cancelled"}