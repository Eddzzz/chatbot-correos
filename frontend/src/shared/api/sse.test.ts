import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readEvents} from './sse.ts';

test('SSE conserva UTF-8, CRLF, comentarios y JSON multilínea con fragmentos de un byte', async () => {
  const text = ': keepalive\r\nevent: answer_chunk\r\ndata: {"text":\r\ndata: "Envío en tránsito"}\r\n\r\nevent: completed\ndata: {"request_id":"r"}\n\n';
  const bytes = new TextEncoder().encode(text);
  const stream = new ReadableStream<Uint8Array>({start(controller) { for (const byte of bytes) controller.enqueue(new Uint8Array([byte])); controller.close(); }});
  const result: unknown[] = [];
  await readEvents(stream, event => result.push(event));
  assert.deepEqual(result, [{event:'answer_chunk',data:{text:'Envío en tránsito'}},{event:'completed',data:{request_id:'r'}}]);
});
test('SSE no convierte un evento incompleto en una respuesta terminada y rechaza JSON inválido', async () => {
  const stream = (text: string) => new ReadableStream<Uint8Array>({start(c) { c.enqueue(new TextEncoder().encode(text)); c.close(); }});
  const result: unknown[] = [];
  await readEvents(stream('event: completed\ndata: {}'), e => result.push(e));
  assert.deepEqual(result, []);
  await assert.rejects(readEvents(stream('data: invalid\n\n'), () => {}), SyntaxError);
});
