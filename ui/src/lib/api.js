export const API = "";
// API key sent with every request — set via VITE_API_KEY env var at build time
export const API_KEY = import.meta.env.VITE_API_KEY || "";

export function apiFetch(path, opts = {}) {
  return fetch(`${API}${path}`, {
    ...opts,
    headers: {
      "X-API-Key": API_KEY,
      ...(opts.headers || {}),
    },
  });
}

/**
 * Read the server's SSE job stream over fetch.
 *
 * EventSource cannot send auth headers, which forced the API key into the URL
 * (where it leaks into server logs / browser history) — and the server ignores
 * query-param auth anyway. fetch() sends the X-API-Key header properly and
 * exposes the same text/event-stream body for incremental reading.
 */
export async function streamJobStatus(jobId, onEvent, onEnd) {
  try {
    const res = await apiFetch(`/api/status/${jobId}`);
    if (!res.ok || !res.body) {
      onEnd?.("error");
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let sep;
      while ((sep = buf.indexOf("\n\n")) >= 0) {
        const chunk = buf.slice(0, sep);
        buf = buf.slice(sep + 2);
        const dataLine = chunk.split("\n").find((l) => l.startsWith("data: "));
        if (dataLine) {
          try {
            onEvent(JSON.parse(dataLine.slice(6)));
          } catch (_) {}
        }
      }
    }
    onEnd?.("closed");
  } catch (_) {
    onEnd?.("error");
  }
}
