// /app/api/run/route.ts
// POST /api/run — proxy request to backend /run endpoint and return the taskId.
// This makes it possible for the client-side hook to call /api/run without knowing backend URL.
// The backend URL is provided via the BACKEND_URL env variable at build/runtime.

export const runtime = 'nodejs'; // allow access to process.env

interface BackendRunResponse {
    task_id?: string; // backend (python FastAPI) likely returns snake_case
    taskId?: string; // but we'll be forgiving
    error?: string;
}

export async function POST(req: Request): Promise<Response> {
    try {
        const { address } = await req.json();
        if (!address || typeof address !== 'string') {
            return new Response(
                JSON.stringify({ error: 'Missing or invalid "address"' }),
                { status: 400, headers: { 'Content-Type': 'application/json' } },
            );
        }

    const backendBase = process.env.BACKEND_URL ?? "http://backend:8000";
    const backendUrl = `${backendBase}/run`;
        console.log(`[api/run] Forwarding request to ${backendUrl} with address ${address}`);

        const backendRes = await fetch(backendUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address }),
        });

        if (!backendRes.ok) {
            const text = await backendRes.text();
            console.error(`[api/run] Backend error ${backendRes.status}: ${text}`);
            return new Response(
                JSON.stringify({ error: `Backend returned ${backendRes.status}: ${text}` }),
                { status: backendRes.status, headers: { 'Content-Type': 'application/json' } },
            );
        }

        const backendJson: BackendRunResponse = await backendRes.json();
        const taskId = backendJson.task_id ?? backendJson.taskId;

        if (!taskId) {
            console.error('[api/run] No task_id returned from backend', backendJson);
            return new Response(
                JSON.stringify({ error: 'No task_id returned from backend' }),
                { status: 502, headers: { 'Content-Type': 'application/json' } },
            );
        }

        return new Response(
            JSON.stringify({ taskId }),
            { status: 200, headers: { 'Content-Type': 'application/json' } },
        );
    } catch (err: unknown) {
        console.error('[api/run] Unexpected error', err);
        const message = err instanceof Error ? err.message : 'Unknown error';
        return new Response(
            JSON.stringify({ error: message }),
            { status: 500, headers: { 'Content-Type': 'application/json' } },
        );
    }
}
