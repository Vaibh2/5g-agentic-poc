import asyncio, sys, yaml
sys.path.insert(0, "backend")
from services.crew_agents import CrewAgents, Orchestrator

async def test():
    path = "config-project/security-fail-config.yaml"
    with open(path) as f:
        content = f.read()

    yaml_contents = [{"file": "security-fail-config.yaml", "content": content}]
    wid = "test-security-fail"

    print("=== Deploy Agent ===")
    deploy = await CrewAgents.deploy_validation(wid, yaml_contents)
    print(f"  Success: {deploy.get('success')}")
    print(f"  Issues: {deploy.get('issues', [])}")
    if not deploy.get("success"):
        print("  >>> DEPLOY FAILED <<<")

    print("\n=== Network Agent ===")
    net = await CrewAgents.network_validation(wid, yaml_contents)
    print(f"  Issues: {net.get('network_issues', [])}")
    print(f"  Rec: {net.get('recommendation')}")

    print("\n=== Security Agent ===")
    sec = await CrewAgents.security_validation(wid, yaml_contents)
    print(f"  Issues: {sec.get('security_issues', [])}")
    print(f"  Warnings: {sec.get('security_warnings', [])}")
    print(f"  Compliance: {sec.get('compliance')}")

    print("\n=== Orchestrator ===")
    result = await Orchestrator.run_full_validation(wid, yaml_contents)
    print(f"  Final Decision: {result['final_decision']}")
    print(f"  Rollback Available: {result['rollback_available']}")
    if result["final_decision"] == "ROLLBACK_NEEDED":
        print("  >>> SECURITY TRIGGERED ROLLBACK <<<")
    elif result["final_decision"] == "PROCEED":
        print("  >>> DEPLOYMENT PROCEEDED <<<")

asyncio.run(test())
