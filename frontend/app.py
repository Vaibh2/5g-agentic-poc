"""
5G Autonomous AI Operations — Streamlit Dashboard
"""

import time
import json
import streamlit as st
import requests
from datetime import datetime

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="5G Agentic AI Ops",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
code, pre, .mono { font-family: 'JetBrains Mono', monospace; }

.metric-card {
    background: linear-gradient(135deg, #0f1117 0%, #1a1d2e 100%);
    border: 1px solid #2d3154;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 8px;
}
.metric-val { font-size: 2rem; font-weight: 800; }
.metric-label { font-size: 0.75rem; color: #8892b0; text-transform: uppercase; letter-spacing: 1px; }
.critical { color: #ff4757 !important; }
.healthy { color: #2ed573 !important; }
.warning { color: #ffa502 !important; }

.timeline-entry {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    padding: 4px 0;
    border-left: 2px solid #2d3154;
    padding-left: 12px;
    margin: 4px 0;
}
.badge-critical { background:#ff475722; color:#ff4757; border:1px solid #ff4757; border-radius:6px; padding:2px 10px; font-size:0.75rem; }
.badge-healthy { background:#2ed57322; color:#2ed573; border:1px solid #2ed573; border-radius:6px; padding:2px 10px; font-size:0.75rem; }
.badge-rolling { background:#ffa50222; color:#ffa502; border:1px solid #ffa502; border-radius:6px; padding:2px 10px; font-size:0.75rem; }
</style>
""",
    unsafe_allow_html=True,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def api(path, method="GET", **kwargs):
    try:
        fn = getattr(requests, method.lower())
        r = fn(f"{API_BASE}{path}", timeout=30, **kwargs)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def metric_color(key, val):
    if key == "latency_ms":
        return "critical" if val > 500 else "healthy"
    if key == "packet_loss_pct":
        return "critical" if val > 5 else "healthy"
    if key == "cpu_usage_pct":
        return "critical" if val > 80 else "healthy"
    if key == "status":
        return "critical" if val == "CRITICAL" else "healthy"
    return "healthy"


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📡 5G Agentic AI Ops")
    st.markdown("*Autonomous Self-Healing Infrastructure*")
    st.divider()

    page = st.radio(
        "Navigation",
        ["🏠 Operations Dashboard", "🚀 Deploy", "📦 Workflows", "💬 Chat", "📋 Incidents & RCA"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("#### System")
    health = api("/health")
    if "error" not in health:
        st.success("API: Online")
    else:
        st.error(f"API: Offline\n`{health['error']}`")

    st.markdown(
        f"<small style='color:#8892b0'>Last refresh: {datetime.now().strftime('%H:%M:%S')}</small>",
        unsafe_allow_html=True,
    )
    if st.button("🔄 Refresh", key="refresh_home"):
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Operations Dashboard
# ══════════════════════════════════════════════════════════════════════════════

if page == "🏠 Operations Dashboard":
    st.title("Operations Dashboard")

    metrics = api("/metrics/current")
    alerts = api("/alerts/current")

    # Status banner
    status = metrics.get("status", "UNKNOWN")
    if status == "CRITICAL":
        st.error("🚨 **NETWORK STATUS: CRITICAL** — Anomaly detected. AI Agent monitoring.")
    elif status == "HEALTHY":
        st.success("✅ **NETWORK STATUS: HEALTHY** — All systems nominal.")
    else:
        st.warning("⚠️ **NETWORK STATUS: UNKNOWN**")

    st.divider()
    st.subheader("Live Network Metrics")

    cols = st.columns(5)
    metric_defs = [
        ("latency_ms", "Latency", "ms"),
        ("packet_loss_pct", "Packet Loss", "%"),
        ("cpu_usage_pct", "CPU Usage", "%"),
        ("throughput_gbps", "Throughput", " Gbps"),
        ("error_rate_pct", "Error Rate", "%"),
    ]

    for col, (key, label, unit) in zip(cols, metric_defs):
        val = metrics.get(key, "—")
        cls = metric_color(key, val if isinstance(val, (int, float)) else 0)
        col.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-val {cls}">{val}{unit}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Active Alerts")
        if isinstance(alerts, list) and alerts:
            for a in alerts:
                st.markdown(
                    f"""
                    <div style="background:#ff475710;border:1px solid #ff4757;border-radius:8px;padding:12px;margin:6px 0">
                    <b>🚨 {a.get('severity','?')}</b> — {a.get('message','')}<br>
                    <small style='color:#8892b0'>{a.get('timestamp','')}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No active alerts.")

    with col_b:
        st.subheader("Recent Deployments")
        deps = api("/deploy/list")
        if isinstance(deps, list):
            for d in deps[:5]:
                status_d = d.get("status", "unknown")
                badge = (
                    '<span class="badge-critical">ROLLED BACK</span>'
                    if status_d == "rolled_back"
                    else '<span class="badge-healthy">DEPLOYED</span>'
                    if status_d == "deployed"
                    else '<span class="badge-rolling">DEPLOYING</span>'
                )
                st.markdown(
                    f"""
                    <div style="border:1px solid #2d3154;border-radius:8px;padding:10px;margin:4px 0">
                    <b>{d.get('deployment_id')}</b> — {d.get('config_name','')} {badge}<br>
                    <small style='color:#8892b0'>{d.get('timestamp','')[:19]}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No deployments yet.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Deploy
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🚀 Deploy":
    st.title("Deployment Control")
    st.markdown("Simulate a network configuration deployment and observe AI-driven anomaly response.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Trigger Deployment")
        config_choice = st.selectbox(
            "Config Package",
            ["routing-config-v24 (HIGH RISK)", "routing-config-v23 (MEDIUM RISK)"],
        )
        config_name = config_choice.split(" ")[0]

        if st.button("🚀 Deploy Configuration", type="primary", use_container_width=True):
            with st.spinner("Deploying configuration..."):
                result = api(f"/deploy/trigger?config_name={config_name}", method="POST")
            if "error" not in result:
                st.success(f"Deployment triggered: **{result['deployment_id']}**")
                st.session_state["last_dep_id"] = result["deployment_id"]
                st.json(result)
            else:
                st.error(f"Error: {result['error']}")

        st.divider()
        st.subheader("Inject Network Anomaly")
        st.caption("Simulates a latency spike and packet loss after deployment.")
        if st.button("⚡ Inject Anomaly Spike", use_container_width=True):
            result = api("/alerts/simulate-spike", method="POST")
            if "error" not in result:
                st.error("🚨 Anomaly injected! Metrics are now CRITICAL.")
                st.json(result.get("metrics", {}))
            else:
                st.error(result["error"])

    with col2:
        st.subheader("Current Deployment Diff")
        st.code(
            """--- network/routing.tf (v23)
+++ network/routing.tf (v24)
@@ -12,7 +12,10 @@

  resource "tower_routing" "sector_7" {
-   mtu_size             = 1500
+   mtu_size             = 9000
+   enable_jumbo_frames  = true
+   fragmentation_policy = "none"
    bgp_route_preference = "auto"
  }""",
            language="diff",
        )
        st.warning("⚠️ MTU change to 9000 requires jumbo frame support on ALL edge nodes.")


elif page == "📦 Workflows":
    st.title("📦 Deployment Workflows")
    st.markdown("Real-time deployment workflows triggered by code pushes from VSCode.")

    if st.button("🔄 Refresh", key="refresh_workflows"):
        st.rerun()

    workflows = api("/webhook/list")
    
    if not isinstance(workflows, list) or len(workflows) == 0:
        st.info("No workflows yet. Commit a YAML file in your project to trigger a deployment!")
        st.markdown("""
        ### Setup Git Hook
        Run this in your VSCode project folder:
        ```bash
        cd /path/to/your/5g-config-project
        python3 /path/to/5g-agentic-poc/backend/scripts/setup_git_hook.py
        ```
        Then commit a YAML file to trigger a workflow!
        """)
    else:
        for wf in workflows:
            status_emoji = {
                "QUEUED": "⏳",
                "RUNNING": "🔵",
                "SUCCESS": "✅",
                "FAILED": "❌"
            }.get(wf.get("status", "UNKNOWN"), "❓")
            
            status_color = {
                "QUEUED": "#ffa502",
                "RUNNING": "#3742fa",
                "SUCCESS": "#2ed573",
                "FAILED": "#ff4757"
            }.get(wf.get("status", "UNKNOWN"), "#888")
            
            with st.container():
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#1a1d2e,#0f1117);border:1px solid #2d3154;border-radius:12px;padding:16px;margin:12px 0">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <span style="font-size:1.2rem;font-weight:bold">{status_emoji} {wf.get('workflow_id','')}</span>
                        <span style="background:{status_color}22;color:{status_color};border:1px solid {status_color};border-radius:6px;padding:4px 12px;font-size:0.8rem">{wf.get('status','')}</span>
                    </div>
                    <div style="margin-top:8px;color:#8892b0;font-size:0.9rem">
                        <strong>Trigger:</strong> {wf.get('trigger','')} | 
                        <strong>Files:</strong> {', '.join(wf.get('files_changed', [])) or 'N/A'}
                    </div>
                    <div style="color:#8892b0;font-size:0.8rem;margin-top:4px">
                        Created: {wf.get('created_at','')[:19]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show agent narrations
                narrations = wf.get("agent_narrations", [])
                if narrations:
                    st.markdown("**Agent Narrations:**")
                    for nar in narrations:
                        ts = nar.get("timestamp", "")[11:19]
                        agent_color = {
                            "Deploy Agent": "#70a1ff",
                            "Network Agent": "#2ed573",
                            "Security Agent": "#ffa502",
                            "Rollback Agent": "#ff4757"
                        }.get(nar.get("agent", ""), "#70a1ff")
                        st.markdown(f"""
                        <div style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;padding:4px 0;border-left:2px solid #2d3154;padding-left:12px;margin:4px 0">
                            <span style="color:#8892b0">[{ts}]</span> <span style="color:{agent_color}">{nar.get('agent','')}</span>: {nar.get('message','')}
                        </div>
                        """, unsafe_allow_html=True)
                
                # Show rollback confirmation for failed workflows
                if wf.get("status") == "FAILED":
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Confirm Rollback", key=f"confirm_{wf.get('workflow_id')}"):
                            try:
                                resp = requests.post(
                                    "http://localhost:8000/webhook/rollback/confirm",
                                    json={"workflow_id": wf.get("workflow_id"), "confirm": True},
                                    timeout=10
                                )
                                if resp.status_code == 200:
                                    st.success("Rollback executed!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    with col2:
                        if st.button(f"❌ Cancel Rollback", key=f"cancel_{wf.get('workflow_id')}"):
                            try:
                                resp = requests.post(
                                    "http://localhost:8000/webhook/rollback/confirm",
                                    json={"workflow_id": wf.get("workflow_id"), "confirm": False},
                                    timeout=10
                                )
                                if resp.status_code == 200:
                                    st.info("Rollback cancelled")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                
                st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Incidents & RCA
# ══════════════════════════════════════════════════════════════════════════════

elif page == "📋 Incidents & RCA":
    st.title("Historical Incidents & RCA")

    incidents = api("/incidents/list")
    if isinstance(incidents, list):
        for inc in incidents:
            with st.expander(f"🔴 {inc.get('id')} — {inc.get('title', 'Unknown')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Description:** {inc.get('description', '—')}")
                    st.markdown(f"**Symptoms:** {inc.get('symptoms', '—')}")
                    st.markdown(f"**Root Cause:** {inc.get('root_cause', '—')}")
                with col2:
                    st.markdown(f"**Resolution:** {inc.get('resolution', '—')}")
                    st.markdown(f"**Config Changed:** `{inc.get('config_change', '—')}`")
                    st.markdown(f"**Impact Duration:** {inc.get('impact_duration_minutes', '—')} min")
    else:
        st.info("No incidents found.")


elif page == "💬 Chat":
    st.title("💬 Network Assistant")
    st.markdown("Ask questions or trigger actions like deployments, rollbacks, etc.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Assistant:** {msg['content']}")
        st.divider()

    user_input = st.text_input("Type your message...", key="chat_input")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        send_btn = st.button("Send", type="primary")
    with col2:
        clear_btn = st.button("Clear Chat")

    if send_btn and user_input:
        with st.spinner("Thinking..."):
            result = api("/agent/chat", method="POST", json={"message": user_input})
        
        if "error" not in result:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.chat_history.append({"role": "assistant", "content": result.get("response", "")})
            st.rerun()
        else:
            st.error(f"Error: {result.get('error', 'Unknown error')}")

    if clear_btn:
        api("/agent/chat/clear", method="POST")
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.markdown("**Example commands:**")
    st.markdown("- `deploy config v24` - Trigger a deployment")
    st.markdown("- `inject anomaly` - Inject a network anomaly")
    st.markdown("- `rollback dep_123` - Rollback a deployment")
    st.markdown("- `show metrics` - Display current network metrics")
    st.markdown("- `what caused the last incident?` - Query historical incidents")
