"""
Jira Service for 5G Agentic AI Ops
- Creates tickets when agents find issues
- Follows same pattern as slack_notification.py
"""
import os
import json
import base64
from typing import Optional, List
from datetime import datetime

import requests

JIRA_URL = os.getenv("JIRA_URL", "")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "")


def _auth_header() -> dict:
    if not JIRA_EMAIL or not JIRA_API_TOKEN:
        return {}
    token = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _headers() -> dict:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        **_auth_header()
    }


def create_ticket(
    summary: str,
    description: str,
    issue_type: str = "Task",
    priority: str = "Medium",
    labels: Optional[List[str]] = None,
) -> Optional[str]:
    """Create a Jira ticket and return the ticket key (e.g. PROJ-42)"""
    if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY]):
        print("[JIRA] Not fully configured - skipping ticket creation")
        return None

    url = f"{JIRA_URL.rstrip('/')}/rest/api/3/issue"

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": summary,
            "description": {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }
                ]
            },
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
            "labels": labels or [],
        }
    }

    try:
        response = requests.post(url, json=payload, headers=_headers(), timeout=10)
        if response.status_code == 201:
            ticket_key = response.json().get("key")
            print(f"[JIRA] Created ticket: {ticket_key}")
            return ticket_key
        else:
            print(f"[JIRA] Failed to create ticket: {response.status_code} {response.text[:500]}")
            return None
    except Exception as e:
        print(f"[JIRA] Error creating ticket: {e}")
        return None


def create_network_issue_ticket(workflow_id: str, issues: List[str], warnings: List[str], recommendation: str) -> Optional[str]:
    """Create a Jira ticket for network validation issues"""
    timestamp = datetime.utcnow().isoformat()
    summary = f"[Network Agent] Issues found in workflow {workflow_id[:8]}"
    
    desc_parts = [f"Workflow: {workflow_id}", f"Timestamp: {timestamp}", f"Recommendation: {recommendation}", ""]
    if issues:
        desc_parts.append("=== ISSUES ===")
        desc_parts.extend(f"- {i}" for i in issues)
        desc_parts.append("")
    if warnings:
        desc_parts.append("=== WARNINGS ===")
        desc_parts.extend(f"- {w}" for w in warnings)
    
    description = "\n".join(desc_parts)
    priority = "High" if recommendation == "REJECT" else "Medium"
    
    return create_ticket(
        summary=summary,
        description=description,
        issue_type="Task",
        priority=priority,
        labels=["network", "5g", "automated"]
    )


def create_security_issue_ticket(workflow_id: str, issues: List[str], warnings: List[str], compliant: bool) -> Optional[str]:
    """Create a Jira ticket for security validation issues"""
    timestamp = datetime.utcnow().isoformat()
    summary = f"[Security Agent] {'Compliance' if not compliant else 'Advisory'} in workflow {workflow_id[:8]}"
    
    desc_parts = [f"Workflow: {workflow_id}", f"Timestamp: {timestamp}", f"Compliant: {compliant}", ""]
    if issues:
        desc_parts.append("=== ISSUES ===")
        desc_parts.extend(f"- {i}" for i in issues)
        desc_parts.append("")
    if warnings:
        desc_parts.append("=== WARNINGS ===")
        desc_parts.extend(f"- {w}" for w in warnings)
    
    description = "\n".join(desc_parts)
    priority = "High" if not compliant else "Medium"
    
    return create_ticket(
        summary=summary,
        description=description,
        issue_type="Task",
        priority=priority,
        labels=["security", "5g", "automated"]
    )


def create_rollback_ticket(workflow_id: str, deployment_id: str, reason: str, risk_level: str) -> Optional[str]:
    """Create a Jira ticket for rollback events"""
    timestamp = datetime.utcnow().isoformat()
    summary = f"[Rollback] Rollback triggered for deployment {deployment_id[:8]}"
    
    description = f"""Workflow: {workflow_id}
Deployment: {deployment_id}
Timestamp: {timestamp}
Risk Level: {risk_level}
Reason: {reason}"""
    
    return create_ticket(
        summary=summary,
        description=description,
        issue_type="Task",
        priority="High",
        labels=["rollback", "5g", "automated", "incident"]
    )


def create_deployment_failure_ticket(workflow_id: str, deployment_id: str, error: str) -> Optional[str]:
    """Create a Jira ticket for deployment failures"""
    timestamp = datetime.utcnow().isoformat()
    summary = f"[Deploy] Deployment failed for workflow {workflow_id[:8]}"
    
    description = f"""Workflow: {workflow_id}
Deployment: {deployment_id}
Timestamp: {timestamp}
Error: {error}"""
    
    return create_ticket(
        summary=summary,
        description=description,
        issue_type="Task",
        priority="High",
        labels=["deployment", "5g", "automated", "failure"]
    )
