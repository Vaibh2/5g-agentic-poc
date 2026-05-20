import React, { useEffect, useState } from "react";
import { apiService } from "../services/api";

interface Workflow {
  workflow_id: string;
  status: string;
  trigger: string;
  files_changed: string[];
  created_at: string;
  agent_narrations?: { agent: string; message: string; timestamp: string }[];
}

const statusConfig: Record<string, { label: string; color: string; bg: string }> = {
  QUEUED: { label: "QUEUED", color: "#f59e0b", bg: "#f59e0b" },
  RUNNING: { label: "RUNNING", color: "#3b82f6", bg: "#3b82f6" },
  SUCCESS: { label: "SUCCESS", color: "#22c55e", bg: "#22c55e" },
  FAILED: { label: "FAILED", color: "#ef4444", bg: "#ef4444" },
  ROLLED_BACK: { label: "ROLLED_BACK", color: "#ef4444", bg: "#ef4444" },
};

const agentColors: Record<string, string> = {
  "Deploy Agent": "#70a1ff",
  "Network Agent": "#2ed573",
  "Security Agent": "#ffa502",
  "Rollback Agent": "#ff4757",
};

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString("en-IN", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
    timeZone: "Asia/Kolkata",
  });
}

function formatTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    timeZone: "Asia/Kolkata",
  });
}

export const Workflows: React.FC = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchWorkflows = async () => {
    try {
      const data = await apiService.workflows();
      const sorted = [...data].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      setWorkflows(sorted);
    } catch (error) {
      console.error("Error fetching workflows:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
    const interval = setInterval(fetchWorkflows, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchWorkflows();
  };

  const handleRollback = async (workflowId: string, confirm: boolean) => {
    try {
      await apiService.confirmRollback(workflowId, confirm);
      fetchWorkflows();
    } catch (error) {
      console.error("Error confirming rollback:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading workflows...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Deployment Workflows</h1>
          <p className="text-gray-400 mt-1">
            Real-time deployment workflows triggered by code pushes from VSCode.
          </p>
        </div>
        <button onClick={handleRefresh} className="btn-secondary">
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {workflows.length === 0 ? (
        <div className="bg-dark-800 border border-dark-700 rounded-xl p-8 text-center">
          <p className="text-gray-400 mb-4">
            No workflows yet. Commit a YAML file in your project to trigger a
            deployment!
          </p>
          <div className="text-left inline-block bg-dark-900 p-4 rounded-lg">
            <p className="text-sm text-gray-400 mb-2">Setup Git Hook</p>
            <p className="text-xs text-gray-500">Run this in your VSCode project folder:</p>
            <code className="text-green-400 text-sm block mt-2">
              cd /path/to/your/5g-config-project
            </code>
            <code className="text-green-400 text-sm block mt-1">
              python3 /path/to/5g-agentic-poc/backend/scripts/setup_git_hook.py
            </code>
            <p className="text-xs text-gray-500 mt-2">
              Then commit a YAML file to trigger a workflow!
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {workflows.map((wf) => {
            const config = statusConfig[wf.status] || { label: "UNKNOWN", color: "text-gray-500", bg: "bg-gray-500" };
            return (
              <div
                key={wf.workflow_id}
                className="bg-gradient-to-br from-dark-800 to-dark-900 border border-dark-700 rounded-xl p-4"
              >
                {/* Header */}
                <div className="flex justify-between items-center mb-3">
                  <span className="text-lg font-bold">
                    {wf.workflow_id}
                  </span>
                  <span
                    className="font-semibold rounded-md px-3 py-1 text-sm border"
                    style={{ 
                      backgroundColor: `${config.color}20`, 
                      color: config.color,
                      borderColor: config.color
                    }}
                  >
                    {wf.status}
                  </span>
                </div>

                {/* Details */}
                <div className="text-sm text-gray-400 mb-2">
                  <strong>Trigger:</strong> {wf.trigger} |{" "}
                  <strong>Files:</strong> {wf.files_changed?.join(", ") || "N/A"}
                </div>
                <div className="text-xs text-gray-500 mb-3">
                  Created: {formatDate(wf.created_at)}
                </div>

                {/* Agent Narrations */}
                {wf.agent_narrations && wf.agent_narrations.length > 0 && (
                  <div className="mt-3 pl-3 border-l-2 border-dark-700">
                    <p className="text-sm font-medium mb-2">Agent Narrations:</p>
                    {wf.agent_narrations.map((nar, idx) => (
                      <div
                        key={idx}
                        className="text-sm font-mono py-1 pl-3 border-l-2 border-dark-700"
                      >
                        <span className="text-gray-500">
                          [{formatTime(nar.timestamp)}]
                        </span>{" "}
                        <span
                          style={{ color: agentColors[nar.agent] || "#70a1ff" }}
                        >
                          {nar.agent}
                        </span>
                        : {nar.message}
                      </div>
                    ))}
                  </div>
                )}

                {/* Rollback Controls for FAILED */}
                {wf.status === "FAILED" && (
                  <div className="mt-4 pt-4 border-t border-dark-700 flex gap-4">
                    <button
                      onClick={() => handleRollback(wf.workflow_id, true)}
                      className="btn-primary text-sm"
                    >
                      Confirm Rollback
                    </button>
                    <button
                      onClick={() => handleRollback(wf.workflow_id, false)}
                      className="btn-secondary text-sm"
                    >
                      Cancel Rollback
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};