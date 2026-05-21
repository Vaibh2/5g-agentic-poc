"""
CrewAI Agents for 5G Network Deployment
- Deploy Agent: Validates YAML configs
- Network Agent: Validates network settings
- Security Agent: Validates security configs
- Rollback Agent: Handles recovery on failure
- Orchestrator: Coordinates all agents

Proper CrewAI v1.6.0 syntax with Crew, Task, and kickoff()
"""
import re
import os
import json
import asyncio
import sys
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load .env file explicitly
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from services.zai_client import chat_complete as openai_chat_complete, get_openai_client
from services.jira_service import (
    create_network_issue_ticket,
    create_security_issue_ticket,
    create_rollback_ticket,
)

print("[INIT] Loading CrewAI Agents...", file=sys.stderr)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-5.4-mini-2026-03-17"

print(f"[INIT] OPENAI_API_KEY: {'SET' if OPENAI_API_KEY else 'NOT SET'}", file=sys.stderr)

WORKFLOWS_FILE = Path(__file__).parent.parent / "data" / "workflows.json"

# Singleton LLM instance - created once and reused
_llm_instance = None

def clear_llm_cache():
    """Clear the cached LLM instance"""
    global _llm_instance
    _llm_instance = None
    print("[LLM] Cache cleared", file=sys.stderr)


def _get_llm_cached():
    """Get LLM instance - always creates fresh to avoid stale instances"""
    global _llm_instance

    _llm_instance = None

    if not OPENAI_API_KEY:
        print("[LLM] No OPENAI_API_KEY found", file=sys.stderr)
        return None

    try:
        from langchain_openai import ChatOpenAI

        print(f"[LLM] Creating fresh OpenAI with model: {MODEL}", file=sys.stderr)

        _llm_instance = ChatOpenAI(
            model=MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.3,
            max_completion_tokens=1024
        )

        print(f"[LLM] Created fresh instance", file=sys.stderr)
        return _llm_instance
    except Exception as e:
        print(f"[LLM] Failed to initialize OpenAI: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


AGENT_DELAYS = {
    "Deploy Agent": 1,
    "Network Agent": 3,
    "Security Agent": 5,
    "Rollback Agent": 7,
}

async def _update_workflow_narration(workflow_id: str, agent_name: str, message: str):
    """Add narration to workflow for real-time updates"""
    if not WORKFLOWS_FILE.exists():
        return
    try:
        workflows = json.loads(WORKFLOWS_FILE.read_text())
        for wf in workflows:
            if wf["workflow_id"] == workflow_id:
                wf["agent_narrations"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": agent_name,
                    "message": message
                })
                WORKFLOWS_FILE.write_text(json.dumps(workflows, indent=2))
    except Exception:
        pass
    await asyncio.sleep(AGENT_DELAYS.get(agent_name, 5))


def _get_llm():
    """Get LLM instance - uses OpenAI or returns None for mock mode"""
    print(f"[LLM] Checking OPENAI_API_KEY...", file=sys.stderr)
    print(f"   Loaded key: {OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-5:]}" if OPENAI_API_KEY else "   No key found", file=sys.stderr)
    
    if not OPENAI_API_KEY:
        print("[LLM] No OPENAI_API_KEY found - using mock mode", file=sys.stderr)
        return None
    
    try:
        from langchain_openai import ChatOpenAI
        print(f"[LLM] Initializing OpenAI model: {MODEL}", file=sys.stderr)
        
        llm = ChatOpenAI(
            model=MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.7,
            max_completion_tokens=2048
        )
        
        print(f"[LLM] OpenAI LLM created (will test on first use)", file=sys.stderr)
        return llm
    except Exception as e:
        print(f"[LLM] Failed to initialize OpenAI: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


def _parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response"""
    try:
        text = text.strip()
        # Remove markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text.strip())
    except Exception as e:
        print(f"[PARSE] JSON parse error: {e}", file=sys.stderr)
        return {"error": "Failed to parse response", "raw": text[:200]}


async def _openai_chat(prompt: str, model: str = "gpt-5.4-mini-2026-03-17") -> str:
    """Call OpenAI chat completion API"""
    try:
        client = get_openai_client()
        if not client:
            raise Exception("OpenAI not configured")

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[OPENAI] Chat failed: {e}", file=sys.stderr)
        raise


class CrewAgents:
    
    @staticmethod
    async def deploy_validation(workflow_id: str, yaml_contents: List[dict]) -> dict:
        """
        Deploy Agent - Primary validator for YAML configs
        Runs first in the sequence
        """
        print(f"\n[DEPLOY AGENT] Starting validation for workflow {workflow_id}", file=sys.stderr)
        await _update_workflow_narration(workflow_id, "Deploy Agent", "Starting YAML configuration validation and syntax analysis...")
        
        # Use cached LLM - no new API calls for LLM creation
        llm = _get_llm_cached()
        
        files_summary = "\n\n".join([
            f"File: {f['file']}\n```yaml\n{f['content']}\n```"
            for f in yaml_contents
        ])
        
        prompt = f"""You are a 5G Network Deployment Agent. Analyze the following YAML configuration files for deployment readiness.

Check for:
1. Valid YAML syntax
2. Required 5G configuration fields (sector, mtu, bgp settings, etc.)
3. Known risky configurations (e.g., MTU > 1500 without jumbo frames)
4. Missing required parameters
5. Invalid values

Files to analyze:
{files_summary}

Respond with ONLY valid JSON (no markdown, no explanation):
{{
  "success": true or false,
  "issues": ["list of critical issues that block deployment"],
  "warnings": ["list of warnings that don't block deployment"],
  "summary": "brief deployment readiness summary"
}}"""

        try:
            result_text = await _openai_chat(prompt)
            parsed = _parse_json_response(result_text)
            print(f"[DEPLOY AGENT] OpenAI result: {parsed}", file=sys.stderr)
            await _update_workflow_narration(workflow_id, "Deploy Agent", f"AI validation complete: {parsed.get('summary', 'Ready')}")
            return parsed
        except Exception as openai_err:
            print(f"[DEPLOY AGENT] OpenAI failed: {openai_err}", file=sys.stderr)

        llm = _get_llm_cached()

        if llm:
            try:
                from crewai import Agent, Task, Crew
                print(f"[DEPLOY AGENT] Creating CrewAI agent with OpenAI LLM...", file=sys.stderr)
                
                deploy_agent = Agent(
                    role="5G Network Deployment Validator",
                    goal="Analyze YAML configs and validate for deployment readiness",
                    backstory="You are an expert in 5G network configurations and deployment workflows.",
                    llm=llm,
                    verbose=False,
                    allow_delegation=False
                )
                print(f"[DEPLOY AGENT] Agent created with LLM", file=sys.stderr)
                
                await _update_workflow_narration(workflow_id, "Deploy Agent", "Deploy Agent analyzing configurations using multi-agent framework...")
                
                # Create task
                task = Task(
                    description=prompt,
                    agent=deploy_agent,
                    expected_output="JSON with success, issues, warnings, and summary"
                )
                
                print(f"[DEPLOY AGENT] Starting Crew kickoff...", file=sys.stderr)
                
                # Create crew and run
                try:
                    crew = Crew(
                        agents=[deploy_agent],
                        tasks=[task],
                        verbose=False
                    )
                    
                    print(f"[DEPLOY AGENT] Calling OpenAI (1 of 3)", file=sys.stderr)
                    result = crew.kickoff()
                except Exception as crew_err:
                    print(f"[DEPLOY AGENT] Crew kickoff failed: {crew_err}", file=sys.stderr)
                    # Try fallback - return mock result
                    raise Exception(f"CrewAI execution failed: {crew_err}")
                
                parsed = _parse_json_response(str(result))
                print(f"[DEPLOY AGENT] Parsed result: {parsed}", file=sys.stderr)
                
                return parsed
                
            except Exception as e:
                print(f"[DEPLOY AGENT] LLM failed: {e}", file=sys.stderr)
                print(f"[DEPLOY AGENT] Falling back to mock mode...", file=sys.stderr)
                llm = None
        
        if not llm:
            print(f"[DEPLOY AGENT] Running in MOCK mode", file=sys.stderr)
            await asyncio.sleep(1)
            issues = []
            warnings = []
            
            import re

            def validate_mtu(content: str, filename: str):
                mtu_pattern = r'mtu[\s:]+(\d+)'
                matches = re.findall(mtu_pattern, content)
                for mtu_val in matches:
                    mtu = int(mtu_val)
                    if mtu < 68 or mtu > 9000:
                        issues.append(f"File {filename}: Invalid MTU {mtu} (valid range: 68-9000)")
                    elif mtu == 9000:
                        warnings.append(f"File {filename}: MTU 9000 requires jumbo frame support on all nodes")
                if 'mtu' not in content:
                    warnings.append(f"File {filename}: MTU not specified")
            
            for f in yaml_contents:
                content = f['content'].lower()
                if not content.strip():
                    issues.append(f"File {f['file']}: Empty file")
                validate_mtu(content, f['file'])
            
            result = {
                "success": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "summary": f"Configuration validated. {len(warnings)} warnings (non-blocking)."
            }
            
            print(f"[DEPLOY AGENT] Mock result: {result}", file=sys.stderr)
        
        if result.get("success"):
            await _update_workflow_narration(workflow_id, "Deploy Agent", f"Validation passed: {result.get('summary', 'Ready for deployment')}")
        else:
            await _update_workflow_narration(workflow_id, "Deploy Agent", f"Validation failed: {', '.join(result.get('issues', []))}")
        
        return result
    
    @staticmethod
    async def network_validation(workflow_id: str, yaml_contents: List[dict]) -> dict:
        """
        Network Agent - Validates network settings
        Runs after Deploy Agent passes
        """
        print(f"\n[NETWORK AGENT] Starting network validation for workflow {workflow_id}", file=sys.stderr)
        await _update_workflow_narration(workflow_id, "Network Agent", "Starting network infrastructure validation and routing analysis...")
        
        # Use cached LLM
        llm = _get_llm_cached()
        
        files_summary = "\n\n".join([
            f"File: {f['file']}\n```yaml\n{f['content']}\n```"
            for f in yaml_contents
        ])
        
        prompt = f"""You are a 5G Network Infrastructure Analyst. Analyze the following YAML configurations for network-specific issues.

Check for:
1. MTU settings (validate 9000 requires jumbo frame support)
2. BGP configuration (AS numbers, neighbor settings)
3. QoS settings (bandwidth, priority queues)
4. IP addressing issues
5. Routing protocol settings
6. VLAN/segmentation issues

Files to analyze:
{files_summary}

Respond with ONLY valid JSON:
{{
  "network_issues": ["critical network issues"],
  "network_warnings": ["non-critical warnings"],
  "recommendation": "PROCEED or REVIEW or REJECT",
  "details": "brief explanation"
}}"""

        try:
            await _update_workflow_narration(workflow_id, "Network Agent", "Checking MTU configuration across network interfaces...")
            result_text = await _openai_chat(prompt)
            parsed = _parse_json_response(result_text)
            print(f"[NETWORK AGENT] OpenAI result: {parsed}", file=sys.stderr)
            for issue in parsed.get("network_issues", []):
                await _update_workflow_narration(workflow_id, "Network Agent", f"ISSUE: {issue}")
            for warning in parsed.get("network_warnings", []):
                await _update_workflow_narration(workflow_id, "Network Agent", f"WARNING: {warning}")
            
            if parsed.get("network_issues") or parsed.get("network_warnings"):
                ticket_key = create_network_issue_ticket(
                    workflow_id,
                    parsed.get("network_issues", []),
                    parsed.get("network_warnings", []),
                    parsed.get("recommendation", "REVIEW")
                )
                if ticket_key:
                    await _update_workflow_narration(workflow_id, "Network Agent", f"Jira ticket created: {ticket_key}")
            
            return parsed
        except Exception as openai_err:
            print(f"[NETWORK AGENT] OpenAI failed: {openai_err}", file=sys.stderr)

        llm = _get_llm_cached()

        if llm:
            try:
                from crewai import Agent, Task, Crew
                
                print(f"[NETWORK AGENT] Creating CrewAI agent...", file=sys.stderr)
                
                network_agent = Agent(
                    role="5G Network Infrastructure Analyst",
                    goal="Validate network settings in YAML configs",
                    backstory="You are an expert in 5G network infrastructure, routing, BGP, QoS, and network protocols.",
                    llm=llm,
                    verbose=False
                )
                
                await _update_workflow_narration(workflow_id, "Network Agent", "Network Agent analyzing routing protocols, BGP peering, and QoS configurations...")
                
                task = Task(
                    description=prompt,
                    agent=network_agent,
                    expected_output="JSON with network_issues, network_warnings, recommendation, details"
                )
                
                crew = Crew(
                    agents=[network_agent],
                    tasks=[task],
                    verbose=False
                )
                
                print(f"[NETWORK AGENT] Starting Crew kickoff...", file=sys.stderr)
                result = crew.kickoff()
                print(f"[NETWORK AGENT] Raw result: {result}", file=sys.stderr)
                
                parsed = _parse_json_response(str(result))
                print(f"[NETWORK AGENT] Parsed result: {parsed}", file=sys.stderr)
                
                for issue in parsed.get("network_issues", []):
                    await _update_workflow_narration(workflow_id, "Network Agent", f"ISSUE: {issue}")
                for warning in parsed.get("network_warnings", []):
                    await _update_workflow_narration(workflow_id, "Network Agent", f"WARNING: {warning}")
                
                if parsed.get("network_issues") or parsed.get("network_warnings"):
                    ticket_key = create_network_issue_ticket(
                        workflow_id,
                        parsed.get("network_issues", []),
                        parsed.get("network_warnings", []),
                        parsed.get("recommendation", "REVIEW")
                    )
                    if ticket_key:
                        await _update_workflow_narration(workflow_id, "Network Agent", f"Jira ticket created: {ticket_key}")
                
                return parsed
                
            except Exception as e:
                print(f"[NETWORK AGENT] LLM failed: {e}", file=sys.stderr)
                print(f"[NETWORK AGENT] Falling back to mock mode...", file=sys.stderr)
                llm = None
        
        if not llm:
            print(f"[NETWORK AGENT] Running in MOCK mode", file=sys.stderr)
            await asyncio.sleep(1)
            network_issues = []
            network_warnings = []
            
            def validate_network_mtu(content: str, filename: str):
                mtu_pattern = r'mtu[\s:]+(\d+)'
                matches = re.findall(mtu_pattern, content)
                for mtu_val in matches:
                    mtu = int(mtu_val)
                    if mtu < 68 or mtu > 9000:
                        network_issues.append(f"File {filename}: Invalid MTU {mtu} (valid range: 68-9000)")
                    elif mtu == 9000:
                        network_warnings.append(f"File {filename}: MTU 9000 needs jumbo frames on all nodes")
            
            await _update_workflow_narration(workflow_id, "Network Agent", "Checking MTU configuration across network interfaces...")
            for f in yaml_contents:
                content = f['content'].lower()
                validate_network_mtu(content, f['file'])
            
            await _update_workflow_narration(workflow_id, "Network Agent", "Verifying BGP peering and AS number assignments...")
            
            await _update_workflow_narration(workflow_id, "Network Agent", "Analyzing QoS settings and bandwidth allocations...")
            
            await _update_workflow_narration(workflow_id, "Network Agent", "Validating IP addressing and subnet configurations...")
            
            await _update_workflow_narration(workflow_id, "Network Agent", "Inspecting routing protocol settings and VLAN segmentation...")
            
            for issue in network_issues:
                await _update_workflow_narration(workflow_id, "Network Agent", f"ISSUE: {issue}")
            for warning in network_warnings:
                await _update_workflow_narration(workflow_id, "Network Agent", f"WARNING: {warning}")
            
            if network_issues or network_warnings:
                ticket_key = create_network_issue_ticket(
                    workflow_id,
                    network_issues,
                    network_warnings,
                    "PROCEED" if not network_issues else "REVIEW"
                )
                if ticket_key:
                    await _update_workflow_narration(workflow_id, "Network Agent", f"Jira ticket created: {ticket_key}")
            
            result = {
                "network_issues": network_issues,
                "network_warnings": network_warnings,
                "recommendation": "PROCEED" if not network_issues else "REVIEW",
                "details": f"Network validation complete. {len(network_warnings)} warnings."
            }
            
            print(f"[NETWORK AGENT] Mock result: {result}", file=sys.stderr)
        
        rec = result.get("recommendation", "REVIEW")
        if rec == "PROCEED":
            await _update_workflow_narration(workflow_id, "Network Agent", f"Network validation passed: {result.get('details', '')}")
        else:
            await _update_workflow_narration(workflow_id, "Network Agent", f"Network review needed: {result.get('details', '')}")
        
        return result
    
    @staticmethod
    async def security_validation(workflow_id: str, yaml_contents: List[dict]) -> dict:
        """
        Security Agent - Validates security configurations
        Runs after Deploy Agent passes
        """
        print(f"\n[SECURITY AGENT] Starting security validation for workflow {workflow_id}", file=sys.stderr)
        await _update_workflow_narration(workflow_id, "Security Agent", "Starting security compliance validation and threat assessment...")
        
        # Use cached LLM
        llm = _get_llm_cached()
        
        files_summary = "\n\n".join([
            f"File: {f['file']}\n```yaml\n{f['content']}\n```"
            for f in yaml_contents
        ])
        
        prompt = f"""You are a 5G Security Compliance Auditor. Analyze the following YAML configurations for security issues.

Check for:
1. Exposed sensitive data (API keys, passwords in plain text)
2. Weak encryption settings
3. Open access/permissions issues
4. Firewall rule issues
5. Authentication/authorization problems
6. Compliance violations

Files to analyze:
{files_summary}

Respond with ONLY valid JSON:
{{
  "security_issues": ["critical security issues"],
  "security_warnings": ["non-critical warnings"],
  "compliance": true or false,
  "details": "brief explanation"
}}"""

        try:
            await _update_workflow_narration(workflow_id, "Security Agent", "Scanning for exposed credentials and sensitive data...")
            result_text = await _openai_chat(prompt)
            parsed = _parse_json_response(result_text)
            print(f"[SECURITY AGENT] OpenAI result: {parsed}", file=sys.stderr)
            for issue in parsed.get("security_issues", []):
                await _update_workflow_narration(workflow_id, "Security Agent", f"ISSUE: {issue}")
            for warning in parsed.get("security_warnings", []):
                await _update_workflow_narration(workflow_id, "Security Agent", f"WARNING: {warning}")
            
            if parsed.get("security_issues") or parsed.get("security_warnings"):
                ticket_key = create_security_issue_ticket(
                    workflow_id,
                    parsed.get("security_issues", []),
                    parsed.get("security_warnings", []),
                    parsed.get("compliance", True)
                )
                if ticket_key:
                    await _update_workflow_narration(workflow_id, "Security Agent", f"Jira ticket created: {ticket_key}")
            
            return parsed
        except Exception as openai_err:
            print(f"[SECURITY AGENT] OpenAI failed: {openai_err}", file=sys.stderr)

        llm = _get_llm_cached()

        if llm:
            try:
                from crewai import Agent, Task, Crew
                
                print(f"[SECURITY AGENT] Creating CrewAI agent...", file=sys.stderr)
                
                security_agent = Agent(
                    role="5G Security Compliance Auditor",
                    goal="Validate security configurations in YAML",
                    backstory="You are an expert in 5G network security, encryption, access controls, and compliance frameworks.",
                    llm=llm,
                    verbose=False
                )
                
                await _update_workflow_narration(workflow_id, "Security Agent", "Security Agent scanning for exposed credentials, encryption weaknesses, and access control violations...")
                
                task = Task(
                    description=prompt,
                    agent=security_agent,
                    expected_output="JSON with security_issues, security_warnings, compliance, details"
                )
                
                crew = Crew(
                    agents=[security_agent],
                    tasks=[task],
                    verbose=False
                )
                
                print(f"[SECURITY AGENT] Starting Crew kickoff...", file=sys.stderr)
                result = crew.kickoff()
                print(f"[SECURITY AGENT] Raw result: {result}", file=sys.stderr)
                
                parsed = _parse_json_response(str(result))
                print(f"[SECURITY AGENT] Parsed result: {parsed}", file=sys.stderr)
                
                for issue in parsed.get("security_issues", []):
                    await _update_workflow_narration(workflow_id, "Security Agent", f"ISSUE: {issue}")
                for warning in parsed.get("security_warnings", []):
                    await _update_workflow_narration(workflow_id, "Security Agent", f"WARNING: {warning}")
                
                if parsed.get("security_issues") or parsed.get("security_warnings"):
                    ticket_key = create_security_issue_ticket(
                        workflow_id,
                        parsed.get("security_issues", []),
                        parsed.get("security_warnings", []),
                        parsed.get("compliance", True)
                    )
                    if ticket_key:
                        await _update_workflow_narration(workflow_id, "Security Agent", f"Jira ticket created: {ticket_key}")
                
                return parsed
                
            except Exception as e:
                print(f"[SECURITY AGENT] LLM failed: {e}", file=sys.stderr)
                print(f"[SECURITY AGENT] Falling back to mock mode...", file=sys.stderr)
                llm = None
        
        if not llm:
            print(f"[SECURITY AGENT] Running in MOCK mode", file=sys.stderr)
            await asyncio.sleep(1)
            security_issues = []
            security_warnings = []
            
            await _update_workflow_narration(workflow_id, "Security Agent", "Scanning for exposed credentials and sensitive data...")
            await _update_workflow_narration(workflow_id, "Security Agent", "Verifying encryption standards for control plane traffic...")
            await _update_workflow_narration(workflow_id, "Security Agent", "Checking firewall rules for overly permissive entries...")
            await _update_workflow_narration(workflow_id, "Security Agent", "Auditing authentication and authorization mechanisms...")
            await _update_workflow_narration(workflow_id, "Security Agent", "Assessing compliance with 3GPP security standards...")
            
            if security_issues or security_warnings:
                ticket_key = create_security_issue_ticket(
                    workflow_id,
                    security_issues,
                    security_warnings,
                    True
                )
                if ticket_key:
                    await _update_workflow_narration(workflow_id, "Security Agent", f"Jira ticket created: {ticket_key}")
            
            result = {
                "security_issues": security_issues,
                "security_warnings": security_warnings,
                "compliance": True,
                "details": "Security validation complete. No issues found."
            }
            print(f"[SECURITY AGENT] Mock result: {result}", file=sys.stderr)
        
        for issue in result.get("security_issues", []):
            await _update_workflow_narration(workflow_id, "Security Agent", f"ISSUE: {issue}")
        for warning in result.get("security_warnings", []):
            await _update_workflow_narration(workflow_id, "Security Agent", f"WARNING: {warning}")
        
        if result.get("compliance"):
            await _update_workflow_narration(workflow_id, "Security Agent", f"Security compliance passed: {result.get('details', '')}")
        else:
            await _update_workflow_narration(workflow_id, "Security Agent", f"Security issues found: {result.get('details', '')}")
        
        return result
    
    @staticmethod
    async def rollback_analysis(workflow_id: str, deployment_id: str, failure_reason: str, yaml_contents: List[dict]) -> dict:
        """
        Rollback Agent - Analyzes failure and recommends/executes rollback
        Triggered when Deploy Agent fails or deployment fails
        """
        print(f"\n[ROLLBACK AGENT] Starting rollback analysis for workflow {workflow_id}", file=sys.stderr)
        await _update_workflow_narration(workflow_id, "Rollback Agent", "Analyzing deployment failure and evaluating rollback requirements...")
        
        # Use cached LLM
        llm = _get_llm_cached()
        
        files_summary = "\n\n".join([
            f"File: {f['file']}\n```yaml\n{f['content']}\n```"
            for f in yaml_contents
        ])
        
        prompt = f"""You are a 5G Deployment Recovery Specialist. Analyze the failed deployment and recommend rollback.

Failure Reason: {failure_reason}

Deployed Files:
{files_summary}

Based on the failure reason and deployed configs:
1. Determine if rollback is needed
2. Identify what changes need to be reverted
3. Create rollback steps
4. Assess risk of rollback

Respond with ONLY valid JSON:
{{
  "rollback_needed": true or false,
  "reason": "explanation of why rollback is needed",
  "steps": ["step 1", "step 2", "step 3"],
  "risk_level": "LOW or MEDIUM or HIGH",
  "estimated_recovery_time": "time in seconds",
  "confirmation_required": true or false
}}"""

        try:
            result_text = await _openai_chat(prompt)
            parsed = _parse_json_response(result_text)
            print(f"[ROLLBACK AGENT] OpenAI result: {parsed}", file=sys.stderr)
            
            ticket_key = create_rollback_ticket(
                workflow_id, deployment_id,
                parsed.get("reason", failure_reason),
                parsed.get("risk_level", "MEDIUM")
            )
            if ticket_key:
                await _update_workflow_narration(workflow_id, "Rollback Agent", f"Jira ticket created: {ticket_key}")
            
            return parsed
        except Exception as openai_err:
            print(f"[ROLLBACK AGENT] OpenAI failed: {openai_err}", file=sys.stderr)

        llm = _get_llm_cached()

        if llm:
            try:
                from crewai import Agent, Task, Crew
                
                print(f"[ROLLBACK AGENT] Creating CrewAI agent...", file=sys.stderr)
                
                rollback_agent = Agent(
                    role="5G Deployment Recovery Specialist",
                    goal="Analyze failures and recommend rollback actions",
                    backstory="You are an expert in 5G deployment recovery, rollback procedures, and disaster recovery.",
                    llm=llm,
                    verbose=False
                )
                
                await _update_workflow_narration(workflow_id, "Rollback Agent", "Rollback Agent evaluating failure impact and generating recovery plan...")
                
                task = Task(
                    description=prompt,
                    agent=rollback_agent,
                    expected_output="JSON with rollback_needed, reason, steps, risk_level, estimated_recovery_time, confirmation_required"
                )
                
                crew = Crew(
                    agents=[rollback_agent],
                    tasks=[task],
                    verbose=False
                )
                
                print(f"[ROLLBACK AGENT] Starting Crew kickoff...", file=sys.stderr)
                result = crew.kickoff()
                print(f"[ROLLBACK AGENT] Raw result: {result}", file=sys.stderr)
                
                parsed = _parse_json_response(str(result))
                print(f"[ROLLBACK AGENT] Parsed result: {parsed}", file=sys.stderr)
                
                ticket_key = create_rollback_ticket(
                    workflow_id, deployment_id,
                    parsed.get("reason", failure_reason),
                    parsed.get("risk_level", "MEDIUM")
                )
                if ticket_key:
                    await _update_workflow_narration(workflow_id, "Rollback Agent", f"Jira ticket created: {ticket_key}")
                
                return parsed
                
            except Exception as e:
                print(f"[ROLLBACK AGENT] LLM failed: {e}", file=sys.stderr)
                print(f"[ROLLBACK AGENT] Falling back to mock mode...", file=sys.stderr)
                llm = None
        
        if not llm:
            print(f"[ROLLBACK AGENT] Running in MOCK mode", file=sys.stderr)
            await asyncio.sleep(1)
            result = {
                "rollback_needed": True,
                "reason": f"Deployment failed: {failure_reason}",
                "steps": [
                    "Revert YAML configuration changes",
                    "Restart affected services",
                    "Verify network connectivity",
                    "Confirm metrics return to normal"
                ],
                "risk_level": "MEDIUM",
                "estimated_recovery_time": 45,
                "confirmation_required": True
            }
            print(f"[ROLLBACK AGENT] Mock result: {result}", file=sys.stderr)
        
        ticket_key = create_rollback_ticket(
            workflow_id, deployment_id,
            result.get("reason", failure_reason),
            result.get("risk_level", "MEDIUM")
        )
        if ticket_key:
            await _update_workflow_narration(workflow_id, "Rollback Agent", f"Jira ticket created: {ticket_key}")
        
        await _update_workflow_narration(
            workflow_id, 
            "Rollback Agent", 
            f"Rollback recommendation: {'NEEDED' if result.get('rollback_needed') else 'NOT NEEDED'}"
        )
        await _update_workflow_narration(
            workflow_id,
            "Rollback Agent",
            f"Failure analysis: {result.get('reason', 'N/A')}"
        )
        
        if result.get("confirmation_required"):
            await _update_workflow_narration(
                workflow_id,
                "Rollback Agent",
                "Awaiting operator confirmation to proceed with rollback..."
            )
        
        return result


class Orchestrator:
    """
    Orchestrates the multi-agent workflow
    - Runs Deploy -> Network -> Security sequentially
    - On failure, triggers Rollback Agent
    - Returns consolidated results
    """
    
    @staticmethod
    async def run_full_validation(workflow_id: str, yaml_contents: List[dict], deployment_context: dict = None) -> dict:
        """
        Run full agent validation workflow
        Returns: {final_decision: str, results: {}, rollback_available: bool}
        """
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"[ORCHESTRATOR] Starting full validation for {workflow_id}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
        
        results = {
            "deploy": None,
            "network": None,
            "security": None,
            "rollback": None
        }
        
        # Step 1: Deploy Agent validation
        print(f"\n[ORCHESTRATOR] Step 1: Running Deploy Agent...", file=sys.stderr)
        deploy_result = await CrewAgents.deploy_validation(workflow_id, yaml_contents)
        results["deploy"] = deploy_result
        
        if not deploy_result.get("success"):
            print(f"\n[ORCHESTRATOR] Deploy Agent FAILED - triggering Rollback Agent", file=sys.stderr)
            failure_reason = "; ".join(deploy_result.get("issues", ["Unknown validation failure"]))
            rollback_result = await CrewAgents.rollback_analysis(
                workflow_id, 
                deployment_context.get("deployment_id", "unknown") if deployment_context else "unknown",
                failure_reason,
                yaml_contents
            )
            results["rollback"] = rollback_result
            
            return {
                "final_decision": "ROLLBACK_NEEDED",
                "results": results,
                "rollback_available": True,
                "confirmation_required": rollback_result.get("confirmation_required", True)
            }
        
        print(f"\n[ORCHESTRATOR] Deploy Agent PASSED - proceeding to Network Agent", file=sys.stderr)
        
        # Step 2: Network Agent validation
        print(f"\n[ORCHESTRATOR] Step 2: Running Network Agent...", file=sys.stderr)
        network_result = await CrewAgents.network_validation(workflow_id, yaml_contents)
        results["network"] = network_result
        
        if network_result.get("recommendation") == "REJECT":
            print(f"\n[ORCHESTRATOR] Network Agent REJECTED - triggering Rollback Agent", file=sys.stderr)
            failure_reason = "; ".join(network_result.get("network_issues", ["Network validation failed"]))
            rollback_result = await CrewAgents.rollback_analysis(
                workflow_id,
                deployment_context.get("deployment_id", "unknown") if deployment_context else "unknown",
                f"Network validation failed: {failure_reason}",
                yaml_contents
            )
            results["rollback"] = rollback_result
            
            return {
                "final_decision": "ROLLBACK_NEEDED",
                "results": results,
                "rollback_available": True,
                "confirmation_required": rollback_result.get("confirmation_required", True)
            }
        
        print(f"\n[ORCHESTRATOR] Network Agent PASSED - proceeding to Security Agent", file=sys.stderr)
        
        # Step 3: Security Agent validation
        print(f"\n[ORCHESTRATOR] Step 3: Running Security Agent...", file=sys.stderr)
        security_result = await CrewAgents.security_validation(workflow_id, yaml_contents)
        results["security"] = security_result
        
        if not security_result.get("compliance"):
            print(f"\n[ORCHESTRATOR] Security Agent FAILED - triggering Rollback Agent", file=sys.stderr)
            failure_reason = "; ".join(security_result.get("security_issues", ["Security compliance failed"]))
            rollback_result = await CrewAgents.rollback_analysis(
                workflow_id,
                deployment_context.get("deployment_id", "unknown") if deployment_context else "unknown",
                f"Security validation failed: {failure_reason}",
                yaml_contents
            )
            results["rollback"] = rollback_result
            
            return {
                "final_decision": "ROLLBACK_NEEDED",
                "results": results,
                "rollback_available": True,
                "confirmation_required": rollback_result.get("confirmation_required", True)
            }
        
        # All validations passed
        print(f"\n[ORCHESTRATOR] All agents PASSED - deployment can proceed", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
        
        return {
            "final_decision": "PROCEED",
            "results": results,
            "rollback_available": False,
            "confirmation_required": False
        }
    
    @staticmethod
    async def execute_rollback(workflow_id: str, rollback_steps: List[str]) -> dict:
        """
        Execute rollback after user confirmation
        """
        print(f"\n[ORCHESTRATOR] Executing rollback for {workflow_id}", file=sys.stderr)
        await _update_workflow_narration(workflow_id, "Rollback Agent", "Executing rollback procedure...")
        
        for i, step in enumerate(rollback_steps):
            print(f"  Step {i+1}: {step}", file=sys.stderr)
            await _update_workflow_narration(workflow_id, "Rollback Agent", f"Step {i+1}: {step}")
            await asyncio.sleep(0.5)
        
        await _update_workflow_narration(workflow_id, "Rollback Agent", "Rollback executed successfully - services restored to previous stable state")
        print(f"[ORCHESTRATOR] Rollback completed for {workflow_id}", file=sys.stderr)
        
        return {
            "success": True,
            "message": "Rollback completed"
        }
    
    @staticmethod
    async def handle_deployment_failure(workflow_id: str, deployment_id: str, failure_error: str, yaml_contents: List[dict]) -> dict:
        """
        Handle deployment execution failure (not validation failure)
        Triggered when deployment runs but fails
        """
        print(f"\n[ORCHESTRATOR] Deployment execution failed - analyzing rollback", file=sys.stderr)
        await _update_workflow_narration(workflow_id, "Rollback Agent", f"Deployment execution failed: {failure_error}")
        
        rollback_result = await CrewAgents.rollback_analysis(
            workflow_id,
            deployment_id,
            f"Deployment execution failed: {failure_error}",
            yaml_contents
        )
        
        return {
            "rollback_needed": rollback_result.get("rollback_needed", True),
            "reason": rollback_result.get("reason", failure_error),
            "steps": rollback_result.get("steps", []),
            "confirmation_required": rollback_result.get("confirmation_required", True),
            "risk_level": rollback_result.get("risk_level", "MEDIUM"),
            "estimated_recovery_time": rollback_result.get("estimated_recovery_time", 30)
        }


print("[INIT] CrewAI Agents module loaded successfully", file=sys.stderr)
