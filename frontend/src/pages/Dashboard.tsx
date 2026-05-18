import React, { useEffect, useState } from "react";
import { apiService } from "../services/api";

interface Metrics {
  status: string;
  latency_ms?: number;
  packet_loss_pct?: number;
  cpu_usage_pct?: number;
  throughput_gbps?: number;
  error_rate_pct?: number;
  [key: string]: any;
}

interface Deployment {
  deployment_id: string;
  config_name: string;
  status: string;
  timestamp: string;
}

interface Workflow {
  workflow_id: string;
  status: string;
  trigger: string;
  files_changed: string[];
  created_at: string;
}

const metricDefinitions = [
  { key: "latency_ms", label: "Latency", unit: "ms" },
  { key: "packet_loss_pct", label: "Packet Loss", unit: "%" },
  { key: "cpu_usage_pct", label: "CPU Usage", unit: "%" },
  { key: "throughput_gbps", label: "Throughput", unit: " Gbps" },
  { key: "error_rate_pct", label: "Error Rate", unit: "%" },
];

function getMetricColor(key: string, val: number | string): string {
  if (key === "latency_ms") return (val as number) > 500 ? "status-critical" : "status-healthy";
  if (key === "packet_loss_pct") return (val as number) > 5 ? "status-critical" : "status-healthy";
  if (key === "cpu_usage_pct") return (val as number) > 80 ? "status-critical" : "status-healthy";
  if (key === "status") return val === "CRITICAL" ? "status-critical" : "status-healthy";
  return "status-healthy";
}

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString("en-IN", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
    timeZone: "Asia/Kolkata",
  });
}

const deploymentStatusConfig: Record<string, { color: string }> = {
  deployed: { color: "#22c55e" },
  deploying: { color: "#3b82f6" },
  rolled_back: { color: "#ef4444" },
};

const workflowStatusConfig: Record<string, { emoji: string; color: string }> = {
  QUEUED: { emoji: "⏳", color: "#f59e0b" },
  RUNNING: { emoji: "🔵", color: "#3b82f6" },
  SUCCESS: { emoji: "✅", color: "#22c55e" },
  FAILED: { emoji: "❌", color: "#ef4444" },
  ROLLED_BACK: { emoji: "🔁", color: "#ef4444" },
};

export const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [metricsData, wfData, depsData] = await Promise.all([
          apiService.metrics(),
          apiService.workflows(),
          apiService.deployments(),
        ]);
        setMetrics(metricsData);
        const sortedWf = [...wfData].sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setWorkflows(sortedWf.slice(0, 5));
        const sortedDeps = [...depsData].sort(
          (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        );
        setDeployments(sortedDeps);
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  const status = metrics?.status || "UNKNOWN";

  return (
    <div className="space-y-6">
      {/* Status Banner */}
      <div
        className={`p-4 rounded-lg border ${
          status === "CRITICAL"
            ? "bg-red-500/10 border-red-500 text-red-500"
            : status === "HEALTHY"
            ? "bg-green-500/10 border-green-500 text-green-500"
            : "bg-yellow-500/10 border-yellow-500 text-yellow-500"
        }`}
      >
        <span className="text-lg font-bold">
          {status === "CRITICAL"
            ? "🚨 NETWORK STATUS: CRITICAL — Anomaly detected. AI Agent monitoring."
            : status === "HEALTHY"
            ? "✅ NETWORK STATUS: HEALTHY — All systems nominal."
            : "⚠️ NETWORK STATUS: UNKNOWN"}
        </span>
      </div>

      {/* Metrics Grid */}
      <div>
        <h2 className="text-xl font-bold mb-4">Live Network Metrics</h2>
        <div className="grid grid-cols-5 gap-4">
          {metricDefinitions.map(({ key, label, unit }) => {
            const value = metrics?.[key] ?? "—";
            const colorClass = getMetricColor(
              key,
              typeof value === "number" ? value : 0
            );
            return (
              <div key={key} className="metric-card">
                <div className="metric-label">{label}</div>
                <div className={`metric-val ${colorClass}`}>
                  {value}
                  {unit !== " Gbps" ? unit : ""}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Workflows & Deployments */}
      <div className="grid grid-cols-2 gap-6">
        {/* Triggered Workflows */}
        <div className="bg-dark-800 border border-dark-700 rounded-xl p-4">
          <h3 className="text-lg font-bold mb-4">Triggered Workflows</h3>
          {workflows && workflows.length > 0 ? (
            <div className="space-y-3">
              {workflows.map((wf) => {
                const config = workflowStatusConfig[wf.status] || { emoji: "❓", color: "#6b7280" };
                return (
                  <div
                    key={wf.workflow_id}
                    className="border border-dark-700 rounded-lg p-3"
                  >
                    <div className="flex justify-between items-start">
                      <span className="font-medium">
                        {config.emoji} {wf.workflow_id}
                      </span>
                      <span
                        className="font-semibold rounded-md px-2 py-1 text-xs border"
                        style={{ 
                          backgroundColor: `${config.color}20`, 
                          color: config.color,
                          borderColor: config.color
                        }}
                      >
                        {wf.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 mt-1">
                      <span className="text-gray-500">Trigger:</span> {wf.trigger}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatDate(wf.created_at)}
                    </p>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-gray-500">No workflows triggered yet.</p>
          )}
        </div>

        {/* Recent Deployments */}
        <div className="bg-dark-800 border border-dark-700 rounded-xl p-4">
          <h3 className="text-lg font-bold mb-4">Recent Deployments</h3>
          {deployments && deployments.length > 0 ? (
            <div className="space-y-3">
              {deployments.slice(0, 5).map((dep) => {
                const statusConfig = deploymentStatusConfig[dep.status] || { color: "#6b7280" };
                const statusLabel = dep.status === "rolled_back" ? "ROLLED BACK" : dep.status === "deployed" ? "DEPLOYED" : "DEPLOYING";
                return (
                  <div
                    key={dep.deployment_id}
                    className="border border-dark-700 rounded-lg p-3"
                  >
                    <div className="flex justify-between items-start">
                      <span className="font-medium">{dep.deployment_id}</span>
                      <span
                        className="font-semibold rounded-md px-2 py-1 text-xs border"
                        style={{ 
                          backgroundColor: `${statusConfig.color}20`, 
                          color: statusConfig.color,
                          borderColor: statusConfig.color
                        }}
                      >
                        {statusLabel}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 mt-1">{dep.config_name}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatDate(dep.timestamp)}
                    </p>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-gray-500">No deployments yet.</p>
          )}
        </div>
      </div>
    </div>
  );
};