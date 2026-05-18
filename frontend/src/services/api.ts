const API_BASE = "http://localhost:8000";

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  } catch (error) {
    console.error(`API Error for ${path}:`, error);
    throw error;
  }
}

export const apiService = {
  health: () => api<{ status: string; service: string }>("/health"),
  metrics: () => api<any>("/metrics/current"),
  alerts: () => api<any[]>("/alerts/current"),
  deployments: () => api<any[]>("/deploy/list"),
  triggerDeployment: (configName: string) =>
    api<any>(`/deploy/trigger?config_name=${configName}`, { method: "POST" }),
  simulateSpike: () => api<any>("/alerts/simulate-spike", { method: "POST" }),
  workflows: () => api<any[]>("/webhook/list"),
  confirmRollback: (workflowId: string, confirm: boolean) =>
    api<any>("/webhook/rollback/confirm", {
      method: "POST",
      body: JSON.stringify({ workflow_id: workflowId, confirm }),
    }),
  incidents: () => api<any[]>("/incidents/list"),
  chat: (message: string) =>
    api<{ response: string }>("/agent/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
  clearChat: () => api<any>("/agent/chat/clear", { method: "POST" }),
};