import os
import requests
from datetime import datetime
from typing import Optional

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_deployment_alert(
    deployment_id: str,
    config_name: str,
    status: str,
    error_message: Optional[str] = None,
    deployed_by: str = "ci-pipeline"
):
    if status == "success":
        color = "#36a64f"
        status_emoji = ":white_check_mark:"
        title = f"Deployment Succeeded"
    else:
        color = "#ff0000"
        status_emoji = ":x:"
        title = f"Deployment Failed"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{status_emoji} {title}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Deployment ID:*\n{deployment_id}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Config:*\n{config_name}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Status:*\n{status.upper()}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Triggered By:*\n{deployed_by}"
                }
            ]
        }
    ]

    if error_message:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Error:*\n```{error_message}```"
            }
        })

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Timestamp: {datetime.utcnow().isoformat()}"
            }
        ]
    })

    payload = {
        "blocks": blocks,
        "attachments": [
            {
                "color": color,
                "blocks": blocks
            }
        ]
    }

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send Slack notification: {e}")
        return False


def send_rollback_alert(
    deployment_id: str,
    config_name: str,
    reason: str = "Automatic rollback",
    workflow_id: Optional[str] = None
):
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":warning: Rollback Initiated",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": []
        }
    ]

    if workflow_id:
        blocks[1]["fields"].append({
            "type": "mrkdwn",
            "text": f"*Workflow ID:*\n{workflow_id}"
        })

    blocks[1]["fields"].extend([
        {
            "type": "mrkdwn",
            "text": f"*Deployment ID:*\n{deployment_id}"
        },
        {
            "type": "mrkdwn",
            "text": f"*Config:*\n{config_name}"
        },
        {
            "type": "mrkdwn",
            "text": f"*Reason:*\n{reason}"
        }
    ])

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Timestamp: {datetime.utcnow().isoformat()}"
            }
        ]
    })

    payload = {"blocks": blocks}

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send Slack notification: {e}")
        return False


def send_workflow_alert(
    workflow_id: str,
    status: str,
    files: list,
    error_message: Optional[str] = None,
    rollback_reason: Optional[str] = None
):
    if status == "SUCCESS":
        color = "#36a64f"
        status_emoji = ":white_check_mark:"
        title = f"Deployment {status}"
    else:
        color = "#ff0000"
        status_emoji = ":x:"
        title = f"Workflow {status}"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{status_emoji} {title}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Workflow ID:*\n{workflow_id}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Status:*\n{status}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Files:*\n{', '.join(files)}"
            }
        }
    ]

    if error_message:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Error:*\n```{error_message}```"
            }
        })

    if rollback_reason:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Rollback:*\n{rollback_reason}"
            }
        })

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Timestamp: {datetime.utcnow().isoformat()}"
            }
        ]
    })

    payload = {
        "blocks": blocks,
        "attachments": [
            {
                "color": color,
                "blocks": blocks
            }
        ]
    }

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send Slack notification: {e}")
        return False