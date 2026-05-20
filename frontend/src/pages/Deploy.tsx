import React, { useState } from "react";
import { apiService } from "../services/api";

export const Deploy: React.FC = () => {
  const [configChoice, setConfigChoice] = useState("routing-config-v24");
  const [deploying, setDeploying] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [anomalyInjected, setAnomalyInjected] = useState(false);
  const [anomalyResult, setAnomalyResult] = useState<any>(null);

  const handleDeploy = async () => {
    setDeploying(true);
    setResult(null);
    setError(null);
    try {
      const res = await apiService.triggerDeployment(configChoice);
      setResult(res);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setDeploying(false);
    }
  };

  const handleInjectAnomaly = async () => {
    try {
      const res = await apiService.simulateSpike();
      setAnomalyInjected(true);
      setAnomalyResult(res.metrics);
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Deployment Control</h1>
        <p className="text-gray-400 mt-1">
          Simulate a network configuration deployment and observe AI-driven
          anomaly response.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Left Column - Controls */}
        <div className="space-y-6">
          {/* Trigger Deployment */}
          <div className="bg-dark-800 border border-dark-700 rounded-xl p-4">
            <h3 className="text-lg font-bold mb-4">Trigger Deployment</h3>
            <select
              value={configChoice}
              onChange={(e) => setConfigChoice(e.target.value)}
              className="input-field w-full mb-4"
            >
              <option value="routing-config-v24">
                routing-config-v24 (HIGH RISK)
              </option>
              <option value="routing-config-v23">
                routing-config-v23 (MEDIUM RISK)
              </option>
            </select>
            <button
              onClick={handleDeploy}
              disabled={deploying}
              className="btn-primary w-full disabled:opacity-50"
            >
              {deploying ? "Deploying..." : "Deploy Configuration"}
            </button>
            {result && (
              <div className="mt-4 p-3 bg-green-500/10 border border-green-500 rounded-lg">
                <p className="text-green-500 font-medium">
                  Deployment triggered: {result.deployment_id}
                </p>
                <pre className="mt-2 text-xs text-gray-400 overflow-x-auto">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </div>
            )}
            {error && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500 rounded-lg text-red-500">
                Error: {error}
              </div>
            )}
          </div>

          {/* Inject Anomaly */}
          <div className="bg-dark-800 border border-dark-700 rounded-xl p-4">
            <h3 className="text-lg font-bold mb-2">Inject Network Anomaly</h3>
            <p className="text-sm text-gray-400 mb-4">
              Simulates a latency spike and packet loss after deployment.
            </p>
            <button
              onClick={handleInjectAnomaly}
              className="btn-secondary w-full"
            >
              Inject Anomaly Spike
            </button>
            {anomalyInjected && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500 rounded-lg">
                <p className="text-red-500 font-medium">
                  Anomaly injected! Metrics are now CRITICAL.
                </p>
                {anomalyResult && (
                  <pre className="mt-2 text-xs text-gray-400 overflow-x-auto">
                    {JSON.stringify(anomalyResult, null, 2)}
                  </pre>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column - Diff View */}
        <div className="bg-dark-800 border border-dark-700 rounded-xl p-4">
          <h3 className="text-lg font-bold mb-4">Current Deployment Diff</h3>
          <pre className="text-sm text-gray-300 bg-dark-900 p-4 rounded-lg overflow-x-auto font-mono">
{`--- network/routing.tf (v23)
+++ network/routing.tf (v24)
@@ -12,7 +12,10 @@

   resource "tower_routing" "sector_7" {
-   mtu_size             = 1500
+   mtu_size             = 9000
+   enable_jumbo_frames  = true
+   fragmentation_policy = "none"
     bgp_route_preference = "auto"
   }`}
          </pre>
          <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500 rounded-lg">
            <p className="text-yellow-500 text-sm">
              MTU change to 9000 requires jumbo frame support on ALL edge
              nodes.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};