import {useEffect, useRef, useState, type FormEvent} from 'react';
import {Access} from './features/auth/Access';
import {MessageView} from './features/chat/MessageView';
import {api, type Message, type Result, type Session} from './shared/api/client';
import {readEvents} from './shared/api/sse';

type Config = {data_mode:string;inference_mode:string;data_snapshot?:string};
const prompts = ['¿Qué consultas puedes responder?', 'Cuenta registros por estado del 2026-01-01 al 2026-02-01', '¿Qué oficinas hay en La Paz?'];
export function App() {
  const [token, setToken] = useState('');
  const [authBusy, setAuthBusy] = useState(false);
  const [error, setError] = useState('');
  const [config, setConfig] = useState<Config | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');
  const [sidebar, setSidebar] = useState(false);
  const requestId = useRef('');
  const controller = useRef<AbortController | null>(null);
  const bottom = useRef<HTMLDivElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  useEffect(()=>{fetch('/api/config').then(r=>r.ok ? r.json() : null).then(setConfig).catch(()=>setConfig(null));},[]);
  useEffect(()=>{bottom.current?.scrollIntoView({behavior:'instant',block:'end'});},[messages,status]);
  useEffect(()=>()=>controller.current?.abort(),[]);
  async function refreshSessions(accessToken = token) { const result = await api<{sessions:Session[]}>('/api/sessions',accessToken); setSessions(result.sessions); }
  async function login(value:string) {
    setAuthBusy(true);setError('');
    try {await refreshSessions(value);setToken(value);} catch(e) {setError(e instanceof Error ? e.message : 'No se pudo conectar con el servicio.');} finally {setAuthBusy(false);}
  }
  async function openSession(id:string) {
    setError('');
    try {const result = await api<{messages:Message[]}>(`/api/sessions/${encodeURIComponent(id)}`,token);setSessionId(id);setMessages(result.messages);setSidebar(false);composer.current?.focus();}
    catch(e) {setError(e instanceof Error ? e.message : 'No se pudo cargar la conversación.');}
  }
  function newSession() {if (busy) return;setSessionId(null);setMessages([]);setInput('');setError('');setSidebar(false);composer.current?.focus();}
  async function cancel() {
    const id = requestId.current;
    controller.current?.abort();
    if (id) try {await api(`/api/requests/${encodeURIComponent(id)}/cancel`,token,{method:'POST'});} catch {setError('La conexión se detuvo. No se pudo confirmar la cancelación en el servidor.');}
  }
  function logout() {controller.current?.abort();setToken('');setSessions([]);setMessages([]);setInput('');setError('');setSessionId(null);}
  async function send(text = input) {
    text = text.trim(); if (!text || busy) return;
    setBusy(true);setError('');setInput('');setStatus('Conectando con el asistente…');requestId.current='';
    setMessages(previous=>[...previous,{role:'user',content:text},{role:'assistant',content:''}]);
    const abort = new AbortController();controller.current=abort;
    let terminal = false;
    const update = (values:Partial<Message>) => setMessages(previous=>previous.map((m,i)=>i===previous.length-1 ? {...m,...values} : m));
    try {
      const response = await fetch('/api/chat/stream',{method:'POST',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},body:JSON.stringify({message:text,session_id:sessionId}),signal:abort.signal});
      if (!response.ok) throw new Error(response.status===401 ? 'Tu acceso expiró. Cierra la sesión e ingresa de nuevo.' : `El servicio no pudo responder (${response.status}).`);
      if (!response.body || !response.headers.get('content-type')?.includes('text/event-stream')) throw new Error('El servidor no entregó una conversación válida.');
      await readEvents(response.body,({event,data})=>{
        if (typeof data.request_id === 'string') {
          if (requestId.current && data.request_id !== requestId.current) throw new Error('La respuesta pertenece a otra solicitud.');
          requestId.current = data.request_id;
        }
        if (event==='request_started') {update({request_id:requestId.current});if(typeof data.session_id==='string') setSessionId(data.session_id);}
        if (event==='status') setStatus(String(data.message || data.status || 'Consultando información…'));
        if (event==='answer_chunk') setMessages(previous=>previous.map((m,i)=>i===previous.length-1 ? {...m,content:m.content + String(data.text || '')} : m));
        if (event==='completed') {terminal=true;update({...data as Result,content:String(data.answer || '')});}
        if (event==='error') {terminal=true;throw new Error(String(data.message || 'No se pudo completar la consulta.'));}
      });
      if (!terminal) throw new Error('La conexión se interrumpió antes de completar la respuesta. Vuelve a intentarlo.');
      try {await refreshSessions();} catch {setError('Respuesta recibida. No se pudo actualizar el historial.');}
    } catch(e) {
      const message = abort.signal.aborted ? 'Consulta detenida.' : e instanceof Error ? e.message : 'No se pudo conectar. Verifica que el servicio esté disponible.';
      update({status:'error'});
      setMessages(previous=>previous.map((m,i)=>i===previous.length-1 && !m.content ? {...m,content:message} : m));
      if (!abort.signal.aborted) setError(message);
    } finally {setBusy(false);setStatus('');controller.current=null;requestId.current='';composer.current?.focus();}
  }
  function submit(event:FormEvent) {event.preventDefault();void send();}
  if (!token) return <Access onAccess={login} error={error} busy={authBusy}/>;
  const mode = config?.data_mode === 'fixture' ? 'Datos ficticios · PostgreSQL de prueba' : config?.data_mode === 'demo' ? 'Datos ficticios · Demostración' : config?.data_mode === 'postgres' ? (config.data_snapshot ? `Datos reales · respaldo ${config.data_snapshot.slice(0,10)}` : 'Base institucional') : 'Datos sin configurar';
  return <div className="workspace"><a className="skip-link" href="#conversation">Ir a la conversación</a><aside className={`sidebar ${sidebar ? 'is-open' : ''}`} aria-label="Conversaciones"><div className="wordmark"><span className="postal-mark" aria-hidden="true">↗</span><span>CORREOS<br/><strong>BOLIVIA</strong></span></div><button className="new-chat" onClick={newSession} disabled={busy}><span aria-hidden="true">＋</span> Nueva conversación</button><div className="history-heading">CONVERSACIONES <button className="mobile-close" aria-label="Cerrar historial" onClick={()=>setSidebar(false)}>×</button></div><nav aria-label="Historial">{sessions.length ? sessions.map(session=><button className={`session ${session.session_id === sessionId ? 'selected' : ''}`} key={session.session_id} disabled={busy} onClick={()=>void openSession(session.session_id)}><span aria-hidden="true">◷</span><span>{session.title || 'Consulta postal'}</span></button>) : <p className="history-empty">Tus conversaciones aparecerán aquí.</p>}</nav><div className="sidebar-bottom"><div className="local-note"><span aria-hidden="true">▣</span><div><strong>Entorno local</strong><small>Consultas de solo lectura</small></div></div><button className="logout" onClick={logout} disabled={busy}>Cerrar sesión <span aria-hidden="true">↗</span></button></div></aside><main className="chat-main"><header className="chat-header"><div><button className="menu-button" onClick={()=>setSidebar(true)} aria-label="Abrir historial" aria-expanded={sidebar}>☰</button><div><p className="eyebrow">ASISTENTE POSTAL</p><h1>Centro de consultas</h1></div></div><span className={`mode-badge ${['demo','fixture'].includes(config?.data_mode || '') ? 'demo' : ''}`}><span aria-hidden="true">●</span>{mode}</span></header><section id="conversation" className={`conversation ${!messages.length ? 'empty' : ''}`} aria-label="Conversación" aria-busy={busy}>{!messages.length ? <div className="welcome"><span className="welcome-mark" aria-hidden="true">↗</span><p className="eyebrow">TU INFORMACIÓN, A UNA PREGUNTA</p><h2>¿Qué necesitas<br/>consultar hoy?</h2><p>Explora los datos postales disponibles.<br/>Respuestas con fuente, sin modificar tus registros.</p><div className="suggestions">{prompts.map(prompt=><button key={prompt} onClick={()=>void send(prompt)}>{prompt}<span aria-hidden="true">↗</span></button>)}</div></div> : <div className="message-list">{messages.map((message,index)=><MessageView key={index} message={message}/>)}<div ref={bottom}/></div>}</section><div className="composer-area"><div className="request-status" role="status" aria-live="polite">{busy && <><span className="loading-dot" aria-hidden="true"/>{status}</>}</div>{error && <p className="inline-error" role="alert">{error}</p>}<form className="composer" onSubmit={submit}><label className="sr-only" htmlFor="message">Tu consulta</label><textarea id="message" ref={composer} rows={2} maxLength={2000} value={input} onChange={e=>setInput(e.target.value)} placeholder="Escribe tu consulta sobre Correos Bolivia…" disabled={busy} onKeyDown={e=>{if(e.key==='Enter' && !e.shiftKey && !e.nativeEvent.isComposing){e.preventDefault();void send();}}}/><div className="composer-actions"><span>Enter para enviar · Shift + Enter para nueva línea</span>{busy ? <button type="button" className="stop" onClick={()=>void cancel()}>■ Detener</button> : <button className="send" disabled={!input.trim()} aria-label="Enviar consulta">↑</button>}</div></form><p className="composer-note">Verifica la fuente y fecha de cada respuesta. {config?.inference_mode === 'rules' ? 'Modo determinista de demostración.' : 'La disponibilidad depende de los datos autorizados.'}</p></div></main></div>;
}
