"use server";

export async function startAnalysis(address: string) {
  console.log(`[server.ts] Starting analysis for address: ${address}`);
  try {
    const res = await fetch(`${process.env.BACKEND_URL}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address }),
    });
    if (!res.ok) {
      const errorText = await res.text();
      console.error(`[server.ts] Error from backend: ${res.status} ${errorText}`);
      throw new Error(`Failed to start analysis: ${res.status} ${errorText}`);
    }
    const { task_id } = await res.json();
    console.log(`[server.ts] Task ID received: ${task_id}`);
    return { taskId: task_id };
  } catch (error) {
    console.error("[server.ts] Error in startAnalysis:", error);
    if (error instanceof Error) {
      return { error: error.message };
    }
    return { error: "An unknown error occurred" };
  }
}
