export type ServerEvent = {event: string; data: Record<string, unknown>};

/** Decode SSE across UTF-8, CRLF and network chunk boundaries. */
export async function readEvents(body: ReadableStream<Uint8Array>, onEvent: (event: ServerEvent) => void) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let pending = '';
  let event = 'message';
  let data: string[] = [];
  const line = (value: string) => {
    if (!value) {
      if (data.length) onEvent({event, data: JSON.parse(data.join('\n')) as Record<string, unknown>});
      event = 'message'; data = [];
    } else if (!value.startsWith(':')) {
      const colon = value.indexOf(':');
      const field = colon < 0 ? value : value.slice(0, colon);
      let content = colon < 0 ? '' : value.slice(colon + 1);
      if (content.startsWith(' ')) content = content.slice(1);
      if (field === 'event') event = content;
      if (field === 'data') data.push(content);
    }
  };
  try {
    for (;;) {
      const {done, value} = await reader.read();
      pending += done ? decoder.decode() : decoder.decode(value, {stream: true});
      let index = 0;
      for (let i = 0; i < pending.length; i++) {
        if (pending[i] !== '\n' && pending[i] !== '\r') continue;
        if (pending[i] === '\r' && i === pending.length - 1 && !done) break;
        line(pending.slice(index, i));
        if (pending[i] === '\r' && pending[i + 1] === '\n') i++;
        index = i + 1;
      }
      pending = pending.slice(index);
      if (done) {
        // An incomplete event is not a completed response; caller checks the terminal event.
        break;
      }
    }
  } finally { reader.releaseLock(); }
}
