import React, { useState, useEffect } from "react";
import { apiService } from "../services/api";

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const tabs = [
  { id: "dashboard", label: "Operations Dashboard", icon: "dashboard" },
  { id: "deploy", label: "Deploy", icon: "deploy" },
  { id: "workflows", label: "Workflows", icon: "workflows" },
  { id: "incidents", label: "Incidents & RCA", icon: "incidents" },
  { id: "chat", label: "Chat", icon: "chat" },
];

export const Layout: React.FC<LayoutProps> = ({
  children,
  activeTab,
  onTabChange,
}) => {
  const [apiStatus, setApiStatus] = useState<"online" | "offline">("offline");
  const [lastRefresh, setLastRefresh] = useState(new Date());

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await apiService.health();
        setApiStatus(health.status === "ok" ? "online" : "offline");
      } catch {
        setApiStatus("offline");
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setLastRefresh(new Date());
    window.location.reload();
  };

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-dark-900 border-r border-dark-700 p-4 flex flex-col">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-white">5G Agentic AI Ops</h1>
          <p className="text-sm text-gray-400 mt-1">Autonomous Self-Healing Infrastructure</p>
        </div>

        <nav className="flex-1 space-y-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`w-full text-left px-4 py-3 rounded-lg transition-all ${
                activeTab === tab.id
                  ? "bg-blue-600 text-white"
                  : "text-gray-300 hover:bg-dark-800"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        <div className="border-t border-dark-700 pt-4 mt-4">
          <div className="text-xs text-gray-400 mb-2">System</div>
          <div className="flex items-center gap-2 mb-2">
            <span
              className={`w-2 h-2 rounded-full ${
                apiStatus === "online" ? "bg-green-500" : "bg-red-500"
              }`}
            />
            <span className={apiStatus === "online" ? "text-green-500" : "text-red-500"}>
              API: {apiStatus === "online" ? "Online" : "Offline"}
            </span>
          </div>
          <div className="text-xs text-gray-500">
            Last refresh: {lastRefresh.toLocaleTimeString()}
          </div>
          <button
            onClick={handleRefresh}
            className="mt-3 w-full bg-dark-700 hover:bg-dark-600 text-gray-300 px-3 py-2 rounded-lg text-sm transition-colors"
          >
            Refresh
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 overflow-auto">{children}</main>
    </div>
  );
};