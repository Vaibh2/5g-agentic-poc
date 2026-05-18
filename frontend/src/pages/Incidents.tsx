import React, { useEffect, useState } from "react";
import { apiService } from "../services/api";

interface Incident {
  id: string;
  title: string;
  description: string;
  symptoms: string;
  root_cause: string;
  resolution: string;
  config_change: string;
  impact_duration_minutes: number;
}

export const Incidents: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const data = await apiService.incidents();
        setIncidents(data);
      } catch (error) {
        console.error("Error fetching incidents:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchIncidents();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading incidents...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">📋 Historical Incidents & RCA</h1>
        <p className="text-gray-400 mt-1">
          View past incidents and their root cause analysis.
        </p>
      </div>

      {incidents.length === 0 ? (
        <div className="bg-dark-800 border border-dark-700 rounded-xl p-8 text-center">
          <p className="text-gray-400">No incidents found.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {incidents.map((inc) => (
            <div
              key={inc.id}
              className="bg-dark-800 border border-dark-700 rounded-xl overflow-hidden"
            >
              {/* Header - Always visible */}
              <button
                onClick={() => setExpandedId(expandedId === inc.id ? null : inc.id)}
                className="w-full text-left p-4 flex items-center justify-between hover:bg-dark-700 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="text-red-500 text-lg">🔴</span>
                  <span className="font-medium">{inc.id}</span>
                  <span className="text-gray-400">— {inc.title}</span>
                </div>
                <span className="text-gray-500 text-2xl">
                  {expandedId === inc.id ? "▲" : "▼"}
                </span>
              </button>

              {/* Expanded Content */}
              {expandedId === inc.id && (
                <div className="px-4 pb-4 border-t border-dark-700">
                  <div className="grid grid-cols-2 gap-6 mt-4">
                    <div>
                      <h4 className="text-sm font-bold text-gray-400 mb-2">Description</h4>
                      <p className="text-sm">{inc.description || "—"}</p>

                      <h4 className="text-sm font-bold text-gray-400 mt-4 mb-2">Symptoms</h4>
                      <p className="text-sm">{inc.symptoms || "—"}</p>

                      <h4 className="text-sm font-bold text-gray-400 mt-4 mb-2">Root Cause</h4>
                      <p className="text-sm">{inc.root_cause || "—"}</p>
                    </div>

                    <div>
                      <h4 className="text-sm font-bold text-gray-400 mb-2">Resolution</h4>
                      <p className="text-sm">{inc.resolution || "—"}</p>

                      <h4 className="text-sm font-bold text-gray-400 mt-4 mb-2">Config Changed</h4>
                      <code className="text-sm text-green-400 bg-dark-900 px-2 py-1 rounded">
                        {inc.config_change || "—"}
                      </code>

                      <h4 className="text-sm font-bold text-gray-400 mt-4 mb-2">Impact Duration</h4>
                      <p className="text-sm">
                        {inc.impact_duration_minutes ? `${inc.impact_duration_minutes} min` : "—"}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};