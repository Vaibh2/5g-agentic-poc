import json
import random
from datetime import datetime
from pathlib import Path

METRICS_FILE = Path(__file__).parent.parent / "data" / "metrics.json"
ALERTS_FILE = Path(__file__).parent.parent / "data" / "alerts.json"

BASELINE = {
    "latency_ms": 120,
    "packet_loss_pct": 0.1,
    "cpu_usage_pct": 28,
    "throughput_gbps": 9.8,
    "error_rate_pct": 0.05,
    "status": "HEALTHY",
}

ANOMALY = {
    "latency_ms": random.randint(800, 1200),
    "packet_loss_pct": round(random.uniform(18, 40), 1),
    "cpu_usage_pct": random.randint(85, 98),
    "throughput_gbps": round(random.uniform(1.2, 3.5), 1),
    "error_rate_pct": round(random.uniform(12, 28), 1),
    "status": "CRITICAL",
}


def _load_metrics():
    if METRICS_FILE.exists():
        return json.loads(METRICS_FILE.read_text())
    return BASELINE.copy()


def _save_metrics(data):
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    METRICS_FILE.write_text(json.dumps(data, indent=2))


def _load_alerts():
    if ALERTS_FILE.exists():
        return json.loads(ALERTS_FILE.read_text())
    return []


def _save_alerts(data):
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ALERTS_FILE.write_text(json.dumps(data, indent=2))


class MonitoringService:

    @staticmethod
    def get_current_metrics() -> dict:
        m = _load_metrics()
        m["timestamp"] = datetime.utcnow().isoformat()
        return m

    @staticmethod
    def inject_anomaly() -> dict:
        anomaly = {
            "latency_ms": random.randint(800, 1200),
            "packet_loss_pct": round(random.uniform(18, 40), 1),
            "cpu_usage_pct": random.randint(85, 98),
            "throughput_gbps": round(random.uniform(1.2, 3.5), 1),
            "error_rate_pct": round(random.uniform(12, 28), 1),
            "status": "CRITICAL",
        }
        _save_metrics(anomaly)

        alerts = _load_alerts()
        alert = {
            "alert_id": f"ALT_{len(alerts)+1:04d}",
            "severity": "CRITICAL",
            "message": f"Latency spike detected: {anomaly['latency_ms']}ms (threshold: 500ms)",
            "metrics_snapshot": anomaly,
            "timestamp": datetime.utcnow().isoformat(),
            "resolved": False,
        }
        alerts.append(alert)
        _save_alerts(alerts)
        return {"injected": True, "metrics": anomaly, "alert": alert}

    @staticmethod
    def restore_baseline():
        _save_metrics(BASELINE.copy())
        alerts = _load_alerts()
        for a in alerts:
            if not a["resolved"]:
                a["resolved"] = True
                a["resolved_at"] = datetime.utcnow().isoformat()
        _save_alerts(alerts)

    @staticmethod
    def get_active_alerts() -> list:
        return [a for a in _load_alerts() if not a.get("resolved")]

    @staticmethod
    def get_alert_history() -> list:
        return list(reversed(_load_alerts()))
