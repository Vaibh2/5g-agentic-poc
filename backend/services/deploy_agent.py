import os
import json
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List

print("📦 Loading deploy_agent.py...", file=sys.stderr)

try:
    from services.crew_agents import Orchestrator, CrewAgents
    CREWAI_AVAILABLE = True
    print("✅ CrewAI module imported successfully", file=sys.stderr)
except ImportError as e:
    CREWAI_AVAILABLE = False
    print(f"⚠️ CrewAI not available - using mock mode: {e}", file=sys.stderr)

WORKFLOWS_FILE = Path(__file__).parent.parent / "data" / "workflows.json"


def _load_workflows():
    if WORKFLOWS_FILE.exists():
        return json.loads(WORKFLOWS_FILE.read_text())
    return []


def _save_workflows(workflows):
    WORKFLOWS_FILE.parent.mkdir(parents=True, exist_ok=True)
    WORKFLOWS_FILE.write_text(json.dumps(workflows, indent=2))


def _update_workflow(workflow_id: str, status: str = None, narration: str = None, step: str = None):
    workflows = _load_workflows()
    for wf in workflows:
        if wf["workflow_id"] == workflow_id:
            if status:
                wf["status"] = status
            if narration:
                wf["agent_narrations"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": "Deploy Agent",
                    "message": narration
                })
            if step:
                wf["steps"].append({
                    "step": step,
                    "timestamp": datetime.utcnow().isoformat()
                })
            break
    _save_workflows(workflows)


class DeployAgent:
    
    @staticmethod
    async def run(workflow_id: str, files: List[str], repo_path: str):
        _update_workflow(workflow_id, narration="🚀 Deploy Agent started - Waiting for task assignment...")
        
        await asyncio.sleep(1)
        _update_workflow(workflow_id, status="RUNNING", narration="📥 Fetching changed files from repository...")
        
        yaml_contents = []
        for file_path in files:
            full_path = os.path.join(repo_path, file_path)
            content = None
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                except Exception as e:
                    pass
            
            if content is None:
                content = f"# Mock config from {file_path}\nmtu: 1500\nnetwork: 5g\nsector: test-sector\n"
                _update_workflow(workflow_id, narration=f"📄 Using default config for: {file_path}")
            else:
                _update_workflow(workflow_id, narration=f"📄 Read file: {file_path}")
            
            yaml_contents.append({
                "file": file_path,
                "content": content
            })
        
        if not yaml_contents:
            _update_workflow(workflow_id, status="FAILED", narration="❌ No valid YAML files found to deploy")
            return
        
        await asyncio.sleep(1)
        _update_workflow(workflow_id, narration="🔍 Analyzing YAML configuration...")
        
        # Run CrewAI agent to analyze
        analysis_result = await DeployAgent._run_crewai_analysis(yaml_contents, workflow_id)
        
        await asyncio.sleep(1)
        
        if analysis_result.get("success"):
            _update_workflow(workflow_id, narration="✅ Validation passed - Proceeding with deployment...")
            await asyncio.sleep(1)
            _update_workflow(workflow_id, narration="🚀 Initiating deployment to 5G infrastructure...")
            await asyncio.sleep(2)
            _update_workflow(workflow_id, narration="⏳ Waiting for infrastructure to provision...")
            await asyncio.sleep(1)
            _update_workflow(workflow_id, narration="✅ Deployment completed successfully!")
            _update_workflow(workflow_id, status="SUCCESS")
        else:
            agent_results = analysis_result.get("agent_results", {})
            rollback_info = agent_results.get("rollback", {})
            
            _update_workflow(workflow_id, narration=f"❌ Deployment failed: {analysis_result.get('error', 'Unknown error')}")
            _update_workflow(workflow_id, status="FAILED")
            
            # Show rollback agent's recommendation
            if rollback_info:
                _update_workflow(workflow_id, narration=f"🔄 Rollback Agent: {rollback_info.get('reason', 'Analyzing failure...')}")
                _update_workflow(workflow_id, narration=f"⚠️ Risk Level: {rollback_info.get('risk_level', 'MEDIUM')}")
                _update_workflow(workflow_id, narration=f"⏱️ Est. Recovery Time: {rollback_info.get('estimated_recovery_time', 30)}s")
                
                if rollback_info.get("confirmation_required"):
                    _update_workflow(workflow_id, narration="❓ Rollback awaiting confirmation...")
                    _update_workflow(workflow_id, step="ROLLBACK_PENDING")
            
            _update_workflow(workflow_id, step="ROLLBACK_NEEDED")

    @staticmethod
    async def _run_crewai_analysis(yaml_contents: List[dict], workflow_id: str) -> dict:
        try:
            print(f"\n{'='*50}", file=sys.stderr)
            print(f"🎯 [_run_crewai_analysis] Starting for workflow {workflow_id}", file=sys.stderr)
            print(f"CREWAI_AVAILABLE: {CREWAI_AVAILABLE}", file=sys.stderr)
            print(f"{'='*50}\n", file=sys.stderr)
            
            if not CREWAI_AVAILABLE:
                # Fallback to simple analysis
                print("🎭 Using mock analysis (CREWAI not available)", file=sys.stderr)
                _update_workflow(workflow_id, narration="🧠 Running validation (mock mode)...")
                return await DeployAgent._simple_analysis(yaml_contents)
            
            _update_workflow(workflow_id, narration="🧠 Starting CrewAI multi-agent validation...")
            
            print("🚀 Calling Orchestrator.run_full_validation()...", file=sys.stderr)
            
            # Use Orchestrator to run full agent pipeline
            validation_result = await Orchestrator.run_full_validation(
                workflow_id=workflow_id,
                yaml_contents=yaml_contents,
                deployment_context={"workflow_id": workflow_id}
            )
            
            print(f"📊 Orchestrator returned: {validation_result.get('final_decision')}", file=sys.stderr)
            
            # Extract result for deployment decision
            if validation_result["final_decision"] == "PROCEED":
                print("✅ Deployment approved by agents", file=sys.stderr)
                return {
                    "success": True,
                    "summary": "All agent validations passed - proceeding with deployment",
                    "agent_results": validation_result["results"]
                }
            else:
                print("❌ Deployment rejected - rollback recommended", file=sys.stderr)
                return {
                    "success": False,
                    "error": "Agent validation failed - rollback recommended",
                    "rollback_available": validation_result["rollback_available"],
                    "confirmation_required": validation_result.get("confirmation_required", True),
                    "agent_results": validation_result["results"]
                }
            
        except Exception as e:
            print(f"❌ [_run_crewai_analysis] Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def _simple_analysis(yaml_contents: List[dict]) -> dict:
        """Simple analysis without full CrewAI - can be enhanced later"""
        
        issues = []
        warnings = []
        
        for f in yaml_contents:
            content = f['content'].lower()
            
            # Check for MTU issues
            if 'mtu' in content and '9000' in content:
                warnings.append(f"File {f['file']}: MTU set to 9000 - requires jumbo frame support")
            
            if 'mtu' in content and '1500' not in content and '9000' not in content:
                warnings.append(f"File {f['file']}: MTU not specified - using default")
                
            # Check for basic YAML structure
            if not content.strip():
                issues.append(f"File {f['file']}: Empty file")
        
        if issues:
            return {
                "success": False,
                "error": "; ".join(issues)
            }
        
        return {
            "success": True,
            "summary": f"Configuration validated. {len(warnings)} warnings (non-blocking)."
        }
    
    @staticmethod
    def get_workflows():
        return list(reversed(_load_workflows()))
    
    @staticmethod
    def get_workflow(workflow_id: str):
        workflows = _load_workflows()
        for wf in workflows:
            if wf["workflow_id"] == workflow_id:
                return wf
        return None