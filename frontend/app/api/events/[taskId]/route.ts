export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

import type { NextRequest } from 'next/server';

export async function GET(_req: NextRequest, { params }: { params: Promise<any> }) {
  const record: any = await params;
  const taskId: string | undefined = record?.taskId;
  if (!taskId) {
    return new Response('Missing taskId', { status: 400 });
  }
  if (!taskId) {
    return new Response('Missing taskId', { status: 400 });
  }

  const backendBase = process.env.BACKEND_URL ?? 'http://backend:8000';
  const backendUrl = `${backendBase}/events/${taskId}`;

  const response = await fetch(backendUrl, {
    headers: { Accept: 'text/event-stream' },
    cache: 'no-store',
  });
  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => '');
    return new Response(text || 'Upstream error', { status: response.status || 502 });
  }

  const stream = new ReadableStream({
    async start(controller) {
      const reader = response.body!.getReader();
      try {
        for (; ;) {
          const { done, value } = await reader.read();
          if (done) break;
          controller.enqueue(value);
        }
      } catch (err) {
        controller.error(err);
      } finally {
        controller.close();
      }
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
