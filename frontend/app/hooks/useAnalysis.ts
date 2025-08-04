"use client";
import { useEffect, useRef, useState } from "react";

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

export function useAnalysis() {
    const [riskScore, setRiskScore] = useState<number | null>(null);
    const [metrics, setMetrics] = useState<Metric[]>([]);
    const [loading, setLoading] = useState(false);
    const [latestMsg, setLatestMsg] = useState("");
    const [logs, setLogs] = useState<string[]>([]);

    const esRef = useRef<EventSource | null>(null);

    const appendLog = (line: string) =>
        setLogs((prev) => [...prev, line]);

    function start(address: string) {
        if (!address.trim()) return;
        setLoading(true);
        setRiskScore(null);
        setMetrics([]);
        setLogs([]);
        setLatestMsg("");

        fetch("/api/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ address }),
        })
            .then((r) => r.json())
            .then(({ taskId, error }) => {
                if (error) {
                    appendLog(`Failed to start analysis: ${error}`);
                    setLoading(false);
                    setLatestMsg("Error");
                    return;
                }
                const es = new EventSource(`/api/events/${taskId}`);
                esRef.current = es;
                console.log("[useAnalysis] EventSource opened", taskId);

                es.addEventListener("progress", (e) => {
                    console.log("[useAnalysis] progress", (e as MessageEvent).data);
                    const data = JSON.parse((e as MessageEvent).data) as ProgressPayload;
                    setMetrics(data.metrics);
                    const logLine = `[Turn ${data.turn}] ` +
                        (data.next_tools.length
                            ? `Next tools → ${data.next_tools.join(", ")}`
                            : data.metrics.length
                                ? `Metrics → ${data.metrics.map((m) => m.metric_name).join(", ")}`
                                : "Waiting for next action …");
                    appendLog(logLine);
                    setLatestMsg(logLine);
                });

                es.addEventListener("result", (e) => {
                    console.log("[useAnalysis] result", (e as MessageEvent).data);
                    const data = JSON.parse((e as MessageEvent).data);
                    setRiskScore(data.risk_score);
                    setMetrics(data.metrics || []);
                    setLatestMsg("Analysis complete");
                    appendLog("Received final result.");
                    setLoading(false);
                    es.close();
                });

                es.addEventListener("error", (e) => {
                    console.error("[useAnalysis] error", e);
                    appendLog("Error: " + (e as MessageEvent).data);
                    setLoading(false);
                    setLatestMsg("Error");
                    es.close();
                });

                es.addEventListener("done", () => {
                    console.log("[useAnalysis] done");
                    appendLog("Job finished.");
                    setLoading(false);
                    es.close();
                });
            })
            .catch((err) => {
                appendLog("Request failed: " + err.message);
                setLoading(false);
                setLatestMsg("Error");
            });
    }

    useEffect(() => () => esRef.current?.close(), []);

    return {
        riskScore,
        metrics,
        loading,
        latestMsg,
        logs,
        start,
    };
}

