"use client";

import React, { useState, useRef, useEffect } from "react";
import { PieChart } from "react-minimal-pie-chart";
import { useAnalysis } from "./hooks/useAnalysis";

 // ---------- Types ----------
interface Metric {
  metric_name: string;
  metric_description: string;
  value: number;
  value_explanation: string;
  [key: string]: unknown; // allow extra unseen fields
}

// ---------- Visual Components ----------

const Gauge = ({ value }: { value: number }) => {
  const roundedValue = Math.round(value);
  const getColor = (val: number) => {
    if (val < 20) return "#22c55e"; // green-500
    if (val < 50) return "#f59e0b"; // amber-500
    if (val < 85) return "#ef4444"; // red-500
    return "#dc2626"; // red-600
  };
  const color = getColor(roundedValue);

  return (
    <div className="relative w-48 h-24 overflow-hidden">
      <div className="absolute w-full h-full">
        <PieChart
          data={[{ value: 1, color }]}
          lineWidth={20}
          startAngle={180}
          lengthAngle={roundedValue * 1.8}
          background="#e5e7eb"
          animate
        />
      </div>
      <div className="absolute w-full h-full flex flex-col items-center justify-end">
        <span className="text-4xl font-bold" style={{ color }}>
          {roundedValue}
        </span>
        <span className="text-sm text-gray-500 -mt-1">Risk Score</span>
      </div>
    </div>
  );
};

const BarChart = ({ metrics }: { metrics: Metric[] }) => {
  const visible = metrics.filter((m) => m.value > 0);

  if (visible.length === 0) return null;

  return (
    <div className="w-full space-y-3 mt-4 self-stretch">
      {visible.map((m) => (
        <div key={m.metric_name} className="flex gap-2">
          <div className="w-1/3 text-xs text-gray-600 truncate" title={m.metric_name}>
            {m.metric_name}
          </div>
          <div className="w-2/3">
            <div className="bg-gray-200 rounded-full h-4">
              <div
                className="bg-blue-500 h-4 rounded-full text-white text-xs flex items-center justify-end pr-2"
                style={{ width: `${Math.min(m.value, 100)}%` }}
              >
                {m.value.toFixed(0)}%
              </div>
            </div>
            {m.value_explanation && (
              <div className="text-[11px] text-gray-700 mt-1">
                {m.value_explanation}
              </div>
            )}
            {m.metric_description && (
              <div className="text-[11px] text-gray-500">
                {m.metric_description}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

// ---------- Component ----------
export default function HomePage() {
  /* ---------------- Local state ---------------- */
  const [address, setAddress] = useState("");
  const [showLogs, setShowLogs] = useState(false);

  /* ---------------- Analysis hook ---------------- */
  const { riskScore, metrics, loading, latestMsg, logs, justification, reasoning, start } = useAnalysis();

  /* ---------------- Refs ---------------- */
  const logRef = useRef<HTMLPreElement>(null);

  /* ---------------- Effects ---------------- */
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  /* ---------------- Handlers ---------------- */
  const handleAnalyze = () => {
    start(address);
  };

  /* ---------------- Render ---------------- */
  return (
    <section className="space-y-8 max-w-3xl mx-auto p-4">
      <div className="flex items-end gap-2">
        <h1 className="text-4xl font-bold text-gray-800">Defi Risk Analyzer</h1>
      </div>
      {/* Address input */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleAnalyze();
        }}
        className="flex items-end gap-2"
      >
        <input
          className="flex-1 rounded border px-3 py-2"
          placeholder="0x… address"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </form>

      {/* Status / result card */}
      {(loading || riskScore !== null) && (
        <div className="rounded border p-6 shadow bg-white flex flex-col items-center justify-center space-y-4 min-h-[15rem]">
          {loading && (
            <>
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-gray-900" />
              <p className="text-center text-sm text-gray-700 min-h-[1.5rem]">
                {latestMsg || "Thinking…"}
              </p>
              {reasoning && (
                <div className="w-full">
                  <div className="text-xs font-medium text-gray-500 mb-1">Reasoning</div>
                  <pre className="text-xs text-gray-800 bg-gray-100 rounded p-2 whitespace-pre-wrap max-h-40 overflow-y-auto">
                    {reasoning}
                  </pre>
                </div>
              )}
            </>
          )}

          {!loading && riskScore !== null && (
            <>
              <Gauge value={riskScore} />
              {justification && (
                <p className="text-center text-gray-700 text-sm max-w-prose whitespace-pre-wrap">
                  {justification}
                </p>
              )}
              {reasoning && (
                <div className="w-full">
                  <div className="text-xs font-medium text-gray-500 mb-1">Reasoning</div>
                  <pre className="text-xs text-gray-800 bg-gray-100 rounded p-2 whitespace-pre-wrap max-h-40 overflow-y-auto">
                    {reasoning}
                  </pre>
                </div>
              )}
              <BarChart metrics={metrics.filter((m: Metric) => m.metric_name !== "Risk Score")} />
            </>
          )}
        </div>
      )}

      {/* Full logs */}
      {logs.length > 0 && (
        <div className="rounded border shadow bg-white p-4">
          <button
            onClick={() => setShowLogs((s: boolean) => !s)}
            className="text-sm font-medium text-blue-600 hover:underline mb-2"
          >
            {showLogs ? "Hide" : "Show"} agent thought process ({logs.length} lines)
          </button>
          {showLogs && (
            <div className="space-y-2">
              {reasoning && (
                <>
                  <div className="text-xs font-medium text-gray-500">Reasoning</div>
                  <pre className="text-xs text-gray-800 bg-gray-100 rounded p-2 whitespace-pre-wrap max-h-40 overflow-y-auto">
                    {reasoning}
                  </pre>
                </>
              )}
              <pre
                ref={logRef}
                className="h-60 overflow-y-auto whitespace-pre-wrap rounded border bg-gray-100 text-gray-800 p-2 text-xs"
              >
                {logs.join("\n")}
              </pre>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
