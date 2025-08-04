// /app/api/events/[taskId]/route.ts
// Proxy SSE stream from backend to client
// Correct signature for App Router route handler
export const runtime = 'nodejs';          // makes “process.env” legal

export async function GET(_req: Request, { params }: { params: { taskId: string } }) {
  const { taskId } = params;
  const backendBase = process.env.BACKEND_URL ?? "http://backend:8000";
  const backendUrl = `${backendBase}/events/${taskId}`;
  console.log(`[api/events] Proxying SSE for task ${taskId} to ${backendUrl}`);

  const response = await fetch(backendUrl);

  if (!response.body) {
    return new Response('No response body from backend', { status: 500 });
  }

  const stream = new ReadableStream({
    async start(controller) {
      const reader = response.body!.getReader();
      const decoder = new TextDecoder();

      function push() {
        reader.read().then(({ done, value }) => {
          if (done) {
            console.log(`[api/events] Stream for task ${taskId} finished.`);
            controller.close();
            return;
          }
          const chunk = decoder.decode(value, { stream: true });
          console.log(`[api/events] Received chunk for task ${taskId}:`, chunk.trim());
          controller.enqueue(value);
          push();
        }).catch(err => {
          console.error(`[api/events] Error reading stream for task ${taskId}:`, err);
          controller.error(err);
        })
      }
      push();
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive',
    },
  });
}
