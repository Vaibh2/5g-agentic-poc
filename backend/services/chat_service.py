import json
import os
import re
import asyncio
from datetime import datetime
from pathlib import Path
import httpx

from services.monitoring_service import MonitoringService
from services.deployment_service import DeploymentService
from services.rag_service import RAGService
from services.rollback_service import RollbackService
from services.zai_client import get_openai_client

MEMORY_FILE = Path(__file__).parent.parent / "data" / "memory.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-5.4-mini-2026-03-17"

SYSTEM_PROMPT = """You are a helpful 5G network operations assistant. You can answer questions about network metrics, incidents, deployments, and help perform actions. 
Provide clear, concise responses. If asked to perform an action, respond with the result."""


def _load_memory():
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text())
    return []


def _save_memory(messages):
    if len(messages) > 50:
        messages = messages[-50:]
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(messages, indent=2))


def _extract_deployment_id(text):
    match = re.search(r'dep[_]?([A-Z0-9]{4,})', text, re.IGNORECASE)
    if match:
        return match.group(0).upper()
    return None


class ChatService:

    @staticmethod
    async def handle_message(user_message: str) -> dict:
        memory = _load_memory()
        
        user_message_lower = user_message.lower()
        
        action_result = await ChatService._try_action(user_message, user_message_lower)
        if action_result:
            response = action_result
        else:
            response = await ChatService._answer_question(user_message, user_message_lower)
        
        memory.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        memory.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        _save_memory(memory)
        
        return {
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    async def _try_action(message: str, message_lower: str) -> str | None:
        if "deploy" in message_lower or "trigger" in message_lower:
            config_name = "routing-config-v24"
            if "v23" in message_lower:
                config_name = "routing-config-v23"
            result = DeploymentService.trigger_deployment(config_name)
            return f"Deployment triggered successfully! Deployment ID: **{result['deployment_id']}**\n\nConfig: {result['config_name']}\nStatus: {result['status']}"
        
        if "inject" in message_lower and ("anomaly" in message_lower or "spike" in message_lower):
            result = MonitoringService.inject_anomaly()
            return f"Anomaly injected! Current metrics:\n- Latency: {result['metrics']['latency_ms']}ms\n- Packet Loss: {result['metrics']['packet_loss_pct']}%\n- Status: CRITICAL"
        
        if "rollback" in message_lower:
            dep_id = _extract_deployment_id(message)
            if not dep_id:
                deployments = DeploymentService.list_deployments()
                if deployments:
                    dep_id = deployments[0].get("deployment_id", "")
            if dep_id:
                result = await RollbackService.execute(dep_id)
                return f"Rollback executed for {dep_id}!\n\n{result['message']}\n\nRecovery actions:\n" + "\n".join(f"- {a}" for a in result.get("recovery_actions", []))
            return "No deployment ID found. Please specify a deployment ID (e.g., dep_123)."
        
        if "restore" in message_lower or "fix" in message_lower or "recover" in message_lower:
            MonitoringService.restore_baseline()
            metrics = MonitoringService.get_current_metrics()
            return f"Network restored to baseline!\n\nCurrent metrics:\n- Latency: {metrics['latency_ms']}ms\n- Packet Loss: {metrics['packet_loss_pct']}%\n- CPU: {metrics['cpu_usage_pct']}%\n- Status: {metrics['status']}"
        
        return None

    @staticmethod
    async def _answer_question(message: str, message_lower: str) -> str:
        metrics = MonitoringService.get_current_metrics()
        alerts = MonitoringService.get_active_alerts()
        deployments = DeploymentService.list_deployments()[:3]
        
        context_parts = [f"CURRENT METRICS:\nLatency: {metrics['latency_ms']}ms\nPacket Loss: {metrics['packet_loss_pct']}%\nCPU: {metrics['cpu_usage_pct']}%\nThroughput: {metrics['throughput_gbps']} Gbps\nError Rate: {metrics['error_rate_pct']}%\nStatus: {metrics['status']}"]
        
        if alerts:
            context_parts.append(f"ACTIVE ALERTS:\n" + "\n".join(f"- {a['severity']}: {a['message']}" for a in alerts))
        
        if deployments:
            dep_str = "\n".join([f"- {d['deployment_id']}: {d['config_name']} ({d['status']})" for d in deployments])
            context_parts.append(f"RECENT DEPLOYMENTS:\n{dep_str}")
        
        if "incident" in message_lower or "root cause" in message_lower or "past" in message_lower or "history" in message_lower:
            query = message
            similar = RAGService.retrieve_similar_incidents(query, top_k=3)
            if similar:
                inc_str = "\n".join([f"## {inc.get('title', inc.get('id'))}\nSymptoms: {inc.get('symptoms')}\nRoot Cause: {inc.get('root_cause')}\nResolution: {inc.get('resolution')}" for inc in similar])
                context_parts.append(f"RELEVANT HISTORICAL INCIDENTS:\n{inc_str}")
        
        context = "\n\n".join(context_parts)
        
        user_prompt = f"""CONTEXT:\n{context}\n\nUSER QUESTION: {message}\n\nProvide a helpful, concise answer based on the context above."""
        
        if not OPENAI_API_KEY:
            return ChatService._mock_response(message_lower, metrics, alerts, deployments)
        
        try:
            client = get_openai_client()
            if not client:
                return ChatService._mock_response(message_lower, metrics, alerts, deployments)
            
            memory = _load_memory()
            conversation_history = [
                {"role": m["role"], "content": m["content"]} 
                for m in memory[-10:]
            ]
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
            ] + conversation_history + [
                {"role": "user", "content": user_prompt},
            ]
            
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.7,
                max_completion_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling OpenAI: {str(e)}. Using fallback response.\n\n{ChatService._mock_response(message_lower, metrics, alerts, deployments)}"

    @staticmethod
    def _mock_response(message_lower: str, metrics: dict, alerts: list, deployments: list) -> str:
        if "metric" in message_lower or "status" in message_lower:
            return f"Current network status: **{metrics['status']}**\n\n- Latency: {metrics['latency_ms']}ms\n- Packet Loss: {metrics['packet_loss_pct']}%\n- CPU: {metrics['cpu_usage_pct']}%\n- Throughput: {metrics['throughput_gbps']} Gbps\n- Error Rate: {metrics['error_rate_pct']}%"
        if "alert" in message_lower:
            if alerts:
                return "Active alerts:\n" + "\n".join([f"- **{a['severity']}**: {a['message']}" for a in alerts])
            return "No active alerts. Network is healthy."
        if "deploy" in message_lower:
            if deployments:
                return "Recent deployments:\n" + "\n".join([f"- {d['deployment_id']}: {d['config_name']} ({d['status']})" for d in deployments])
            return "No recent deployments."
        return f"Current status: {metrics['status']}. Latency: {metrics['latency_ms']}ms, CPU: {metrics['cpu_usage_pct']}%. How can I help further?"

    @staticmethod
    def get_memory():
        return _load_memory()

    @staticmethod
    def clear_memory():
        _save_memory([])
        return {"cleared": True}