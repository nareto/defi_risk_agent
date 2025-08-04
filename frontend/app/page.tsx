"use client";

import React, { useState, useRef, useEffect } from "react";
import { PieChart } from "react-minimal-pie-chart";

// ---------- Types ----------
interface Metric {
  metric_name: string;
  percentage_exposure?: number;
  description?: string;
  hhi_score?: number;
}

interface ProgressPayload {
  turn: number;
  metrics: Metric[];
  next_tools: string[];
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
          lengthAngle={roundedValue * 1.8} // 100% = 180 degrees
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
  const chartData = metrics
    .map((m) => ({
      name: m.metric_name,
      value:
        m.percentage_exposure !== undefined
          ? m.percentage_exposure
          : (m.hhi_score || 0) * 100, // Normalize HHI to 0-100 scale
    }))
    .filter((d) => d.value > 0);

  if (chartData.length === 0) return null;

  return (
    <div className="w-full space-y-2 mt-4 self-stretch">
      {chartData.map((d) => (
        <div key={d.name} className="flex items-center gap-2">
          <div className="w-1/3 text-xs text-gray-600 truncate" title={d.name}>
            {d.name}
          </div>
          <div className="w-2/3 bg-gray-200 rounded-full h-4">
            <div
              className="bg-blue-500 h-4 rounded-full text-white text-xs flex items-center justify-end pr-2"
              style={{ width: `${Math.min(d.value, 100)}%` }}
            >
              {d.value.toFixed(0)}%
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};


// ---------- Component ----------
export default function HomePage() {
  /* ---------------- State ---------------- */
  const [address, setAddress] = useState("");
  const [riskScore, setRiskScore] = useState<number | null>(null);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [loading, setLoading] = useState(false);
  const [latestMsg, setLatestMsg] = useState<string>("");
  const [logs, setLogs] = useState<string[]>([]);
  const [showLogs, setShowLogs] = useState<boolean>(false);

  /* ---------------- Refs ---------------- */
  const logRef = useRef<HTMLPreElement>(null);

  /* ------------- Helpers --------------- */
  const appendLog = (text: string) => setLogs((prev) => [...prev, text]);

  /* Auto-scroll logs */
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  /* ---------------- Actions ---------------- */
  async function handleAnalyze() {
    if (!address.trim()) return;

    // Reset
    setLoading(true);
    setRiskScore(null);
    setMetrics([]);
    setLogs([]);
    setLatestMsg("");

    try {
      const res = await fetch("/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address }),
      });
      const { task_id } = await res.json();

      const es = new EventSource(`/events/${task_id}`);

      // --- progress ---
      es.addEventListener("progress", (e) => {
        const data = JSON.parse((e as MessageEvent).data) as ProgressPayload;

        // Update metrics so final view has everything
        setMetrics(data.metrics);

        // Build human-readable message & append to logs
        const logLine = `[Turn ${data.turn}] ` +
          (data.next_tools.length
            ? `Next tools → ${data.next_tools.join(", ")}`
            : data.metrics.length
            ? `Metrics → ${data.metrics.map((m) => m.metric_name).join(", ")}`
            : "Waiting for next action …");

        appendLog(logLine);
        setLatestMsg(logLine);
      });

      // --- result (final) ---
      es.addEventListener("result", (e) => {
        const data = JSON.parse((e as MessageEvent).data);
        setRiskScore(data.risk_score);
        setMetrics(data.metrics || []);
        setLatestMsg("Analysis complete");
        appendLog("Received final result.");

        // In case the server (or any proxy in front of it) closes the SSE
        // connection immediately after sending the result event, the browser
        // may never deliver the subsequent "done" event to the client.  This
        // would leave the UI stuck in the loading state.  To guard against
        // that, we consider the analysis finished as soon as we receive the
        // "result" event.
        setLoading(false);
        es.close();
      });

      // --- errors ---
      es.addEventListener("error", (e) => {
        appendLog("Error: " + (e as MessageEvent).data);
        es.close();
        setLoading(false);
        setLatestMsg("Error");
      });

      // --- done / close ---
      es.addEventListener("done", () => {
        appendLog("Job finished.");
        es.close();
        setLoading(false);
      });
    } catch (err: any) {
      appendLog("Request failed: " + err.message);
      setLoading(false);
      setLatestMsg("Error");
    }
  }

  /* ---------------- Render ---------------- */
  return (
    <section className="space-y-8 max-w-3xl mx-auto p-4">
      {/* Address input */}
      <div className="flex items-end gap-2">
        <input
          className="flex-1 rounded border px-3 py-2"
          placeholder="0x… address"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          disabled={loading}
        />
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </div>

      {/* Status / result card */}
      {(loading || riskScore !== null) && (
        <div className="rounded border p-6 shadow bg-white flex flex-col items-center justify-center space-y-4 min-h-60">
          {loading && (
            <>
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-gray-900" />
              <p className="text-center text-sm text-gray-700 min-h-6">
                {latestMsg || "Thinking…"}
              </p>
            </>
          )}

          {!loading && riskScore !== null && (
            <>
              <Gauge value={riskScore} />
              <BarChart metrics={metrics.filter(m => m.metric_name !== 'Risk Score')} />
            </>
          )}
        </div>
      )}

      {/* Full logs */}
      {logs.length > 0 && (
        <div className="rounded border shadow bg-white p-4">
          <button
            onClick={() => setShowLogs((s) => !s)}
            className="text-sm font-medium text-blue-600 hover:underline mb-2"
          >
            {showLogs ? "Hide" : "Show"} agent thought process ({logs.length} lines)
          </button>
          {showLogs && (
            <pre
              ref={logRef}
              className="h-60 overflow-y-auto whitespace-pre-wrap rounded border bg-gray-100 text-gray-800 p-2 text-xs"
            >
              {logs.join("\n")}
            </pre>
          )}
        </div>
      )}
    </section>
  );
}
