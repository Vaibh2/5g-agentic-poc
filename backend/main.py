from dotenv import load_dotenv
load_dotenv()

import logging
import sys

# Configure logging to show all output
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

# Redirect all prints to stderr for visibility in uvicorn
print("🚀 Starting 5G Agentic AI Backend...", file=sys.stderr)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import deploy, alerts, incidents, agent, webhook

app = FastAPI(title="5G Agentic AI Operations API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(deploy.router, prefix="/deploy", tags=["Deployment"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
app.include_router(agent.router, prefix="/agent", tags=["AI Agent"])
app.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "5G Agentic AI Ops"}


@app.get("/metrics/current")
def current_metrics():
    from services.monitoring_service import MonitoringService
    return MonitoringService.get_current_metrics()
