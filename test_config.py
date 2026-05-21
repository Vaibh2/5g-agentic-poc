"""
Test script to validate working-config.yaml with CrewAI agents
Run: python test_config.py
"""
import asyncio
import sys
from pathlib import Path
import yaml

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from services.crew_agents import CrewAgents, Orchestrator

async def test_config():
    config_file = Path(__file__).parent / "config-project" / "working-config.yaml"
    
    print(f"\n{'='*60}")
    print(f"Testing YAML Configuration Validation")
    print(f"{'='*60}\n")
    
    # Load and parse YAML
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Verify it's valid YAML
    try:
        parsed = yaml.safe_load(content)
        print("[PASS] YAML syntax is valid")
    except yaml.YAMLError as e:
        print(f"[FAIL] YAML syntax error: {e}")
        return
    
    # Prepare for CrewAI validation
    yaml_contents = [{
        "file": "working-config.yaml",
        "content": content
    }]
    
    workflow_id = "test-workflow-001"
    
    print(f"\n[1/3] Running Deploy Agent validation...")
    deploy_result = await CrewAgents.deploy_validation(workflow_id, yaml_contents)
    print(f"  Success: {deploy_result.get('success')}")
    print(f"  Issues: {deploy_result.get('issues', [])}")
    print(f"  Warnings: {deploy_result.get('warnings', [])}")
    print(f"  Summary: {deploy_result.get('summary')}")
    
    if not deploy_result.get('success'):
        print(f"\n[FAIL] Deploy validation failed!")
        return
    
    print(f"\n[2/3] Running Network Agent validation...")
    network_result = await CrewAgents.network_validation(workflow_id, yaml_contents)
    print(f"  Network Issues: {network_result.get('network_issues', [])}")
    print(f"  Network Warnings: {network_result.get('network_warnings', [])}")
    print(f"  Recommendation: {network_result.get('recommendation')}")
    print(f"  Details: {network_result.get('details')}")
    
    if network_result.get('recommendation') == 'REJECT':
        print(f"\n[FAIL] Network validation rejected!")
        return
    
    print(f"\n[3/3] Running Security Agent validation...")
    security_result = await CrewAgents.security_validation(workflow_id, yaml_contents)
    print(f"  Security Issues: {security_result.get('security_issues', [])}")
    print(f"  Security Warnings: {security_result.get('security_warnings', [])}")
    print(f"  Compliance: {security_result.get('compliance')}")
    print(f"  Details: {security_result.get('details')}")
    
    if not security_result.get('compliance'):
        print(f"\n[FAIL] Security validation failed!")
        return
    
    print(f"\n{'='*60}")
    print(f"[SUCCESS] ALL VALIDATIONS PASSED!")
    print(f"{'='*60}\n")
    
    # Also test full orchestrator workflow
    print(f"\nTesting full Orchestrator workflow...")
    full_result = await Orchestrator.run_full_validation(workflow_id, yaml_contents)
    print(f"  Final Decision: {full_result['final_decision']}")
    print(f"  Rollback Available: {full_result['rollback_available']}")
    
    if full_result['final_decision'] == 'PROCEED':
        print(f"\n[SUCCESS] Orchestrator approved deployment!")
    else:
        print(f"\n[FAIL] Orchestrator did not approve: {full_result['final_decision']}")

if __name__ == "__main__":
    asyncio.run(test_config())
