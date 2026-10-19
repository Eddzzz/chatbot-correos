import {useEffect, useRef, useState, type FormEvent} from 'react';
import {Ambient, Brand, Icon, PostalMotion, ThemeToggle} from './PostalUI';
import {Access} from './features/auth/Access';
import {MessageView} from './features/chat/MessageView';
import {api, type Message, type Result, type Session} from './shared/api/client';
import {readEvents} from './shared/api/sse';
import {chatIdFromPath,chatPath} from './features/chat/chatUrl';

type Config = {data_mode:string;inference_mode:string;data_snapshot?:string};
const prompts = [
  {icon:'box', title:'Seguimiento de envíos', text:'Consulta estados y movimientos', prompt:'¿Cómo consulto el seguimiento de un envío?'},
  {icon:'chart', title:'Actividad postal', text:'Explora registros por estado', prompt:'Cuenta registros por estado del mes pasado'},
  {icon:'pin', title:'Oficinas y sucursales', text:'Encuentra información de oficinas', prompt:'¿Qué oficinas hay en La Paz?'}
];
export function App() {
  const [theme,setTheme] = useState<'light'|'dark'>(()=>{try {const saved=localStorage.getItem('correos-theme');if(saved==='light' || saved==='dark')return saved;}catch{}return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';});
  useEffect(()=>{document.documentElement.dataset.theme=theme;try{localStorage.setItem('correos-theme',theme);}catch{}},[theme]);
  const toggleTheme=()=>setTheme(value=>value==='dark' ? 'light' : 'dark');
  const [token, setToken] = useState('');
  const [authBusy, setAuthBusy] = useState(false);
  const [error, setError] = useState('');
  const [config, setConfig] = useState<Config | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(()=>chatIdFromPath(window.location.pathname));
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);
  const navigation = useRef(0);
  const [status, setStatus] = useState('');
  const [sidebar, setSidebar] = useState(false);
  const [historySearch,setHistorySearch] = useState('');
  const visibleSessions = sessions.filter(session=>(session.title || 'Consulta postal').toLocaleLowerCase('es').includes(historySearch.trim().toLocaleLowerCase('es')));
  useEffect(()=>{if(sidebar)document.querySelector<HTMLButtonElement>('.mobile-close')?.focus();},[sidebar]);
  const requestId = useRef('');
  const controller = useRef<AbortController | null>(null);
  const bottom = useRef<HTMLDivElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  useEffect(()=>{fetch('/api/config').then(r=>r.ok ? r.json() : null).then(setConfig).catch(()=>setConfig(null));},[]);
  useEffect(()=>{bottom.current?.scrollIntoView({behavior:'instant',block:'end'});},[messages,status]);
  useEffect(()=>()=>controller.current?.abort(),[]);
  function navigate(id:string|null,replace=false) {
    const path=chatPath(id);
    if(window.location.pathname!==path) window.history[replace?'replaceState':'pushState']({},'',path);
  }
  useEffect(()=>{
    function backOrForward() {
      if(busy || loadingChat){navigate(sessionId,true);return;}
      const id=chatIdFromPath(window.location.pathname);
      if(id && token) void openSession(id,token,false);
      else if(!id) {setSessionId(null);setMessages([]);setInput('');setError('');}
    }
    window.addEventListener('popstate',backOrForward);
    return ()=>window.removeEventListener('popstate',backOrForward);
  },[token,busy,loadingChat,sessionId]);
  async function refreshSessions(accessToken = token) { const result = await api<{sessions:Session[]}>('/api/sessions',accessToken); setSessions(result.sessions); }
  async function login(value:string) {
    setAuthBusy(true);setError('');
    try {await refreshSessions(value);setToken(value);const id=chatIdFromPath(window.location.pathname);if(id) await openSession(id,value,false);} catch(e) {setError(e instanceof Error ? e.message : 'No se pudo conectar con el servicio.');} finally {setAuthBusy(false);}
  }
  async function openSession(id:string,accessToken=token,updateUrl=true) {
    const current=++navigation.current;
    setError('');setLoadingChat(true);setMessages([]);
    try {const result = await api<{messages:Message[]}>(`/api/sessions/${encodeURIComponent(id)}`,accessToken);if(current!==navigation.current)return;setSessionId(id);setMessages(result.messages);setInput('');if(updateUrl)navigate(id);setSidebar(false);composer.current?.focus();}
    catch(e) {if(current===navigation.current){setSessionId(null);setError(e instanceof Error ? e.message : 'No se pudo cargar la conversación.');}}
    finally {if(current===navigation.current)setLoadingChat(false);}
  }
  function newSession() {if (busy || loadingChat) return;navigation.current++;navigate(null);setSessionId(null);setMessages([]);setInput('');setError('');setSidebar(false);composer.current?.focus();}
  async function cancel() {
    const id = requestId.current;
    controller.current?.abort();
    if (id) try {await api(`/api/requests/${encodeURIComponent(id)}/cancel`,token,{method:'POST'});} catch {setError('La conexión se detuvo. No se pudo confirmar la cancelación en el servidor.');}
  }
  function logout() {navigation.current++;controller.current?.abort();setToken('');setSessions([]);setMessages([]);setInput('');setError('');setSessionId(null);setLoadingChat(false);}
  async function send(text = input) {
    text = text.trim(); if (!text || busy || loadingChat) return;
    const startedAt = performance.now();
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
        if (event==='request_started') {update({request_id:requestId.current});if(typeof data.session_id==='string'){setSessionId(data.session_id);navigate(data.session_id);}}
        if (event==='status') setStatus(String(data.message || data.status || 'Consultando información…'));
        if (event==='answer_chunk') setMessages(previous=>previous.map((m,i)=>i===previous.length-1 ? {...m,content:m.content + String(data.text || '')} : m));
        if (event==='completed') {terminal=true;update({...data as Result,content:String(data.answer || ''),response_seconds:(performance.now()-startedAt)/1000});}
        if (event==='error') {terminal=true;throw new Error(String(data.message || 'No se pudo completar la consulta.'));}
      });
      if (!terminal) throw new Error('La conexión se interrumpió antes de completar la respuesta. Vuelve a intentarlo.');
    } catch(e) {
      const message = abort.signal.aborted ? 'Consulta detenida.' : e instanceof Error ? e.message : 'No se pudo conectar. Verifica que el servicio esté disponible.';
      update({status:'error',response_seconds:(performance.now()-startedAt)/1000});
      setMessages(previous=>previous.map((m,i)=>i===previous.length-1 && !m.content ? {...m,content:message} : m));
      if (!abort.signal.aborted) setError(message);
    } finally {try{await refreshSessions();}catch{/* Keep the saved chat URL available when history refresh fails. */}setBusy(false);setStatus('');controller.current=null;requestId.current='';composer.current?.focus();}
  }
  function submit(event:FormEvent) {event.preventDefault();void send();}
  if (!token) return <Access onAccess={login} error={error} busy={authBusy} theme={theme} onToggleTheme={toggleTheme}/>;
  const mode = config?.data_mode === 'fixture' ? 'Datos ficticios · PostgreSQL de prueba' : config?.data_mode === 'demo' ? 'Datos ficticios · Demostración' : config?.data_mode === 'postgres' ? (config.data_snapshot ? `Datos reales · respaldo ${config.data_snapshot.slice(0,10)}` : 'Base institucional') : 'Datos sin configurar';
  return <div className="workspace">
    <Ambient/>
    <a className="skip-link" href="#conversation">Ir a la conversación</a>
    {sidebar && <button className="sidebar-backdrop" aria-label="Cerrar historial" onClick={()=>setSidebar(false)}/>}
    <aside className={`sidebar ${sidebar ? 'is-open' : ''}`} aria-label="Conversaciones" onKeyDown={event=>{if(event.key==='Escape'){setSidebar(false);document.querySelector<HTMLButtonElement>('.menu-button')?.focus();}}}>
      <div className="sidebar-brand"><Brand/><button className="mobile-close" aria-label="Cerrar historial" onClick={()=>setSidebar(false)}><Icon name="close"/></button></div>
      <button className="new-chat" onClick={newSession} disabled={busy || loadingChat}><Icon name="plus"/> Nueva conversación </button>
      <div className="history-heading">Conversaciones <span>{sessions.length}</span></div>
      <label className="history-search"><Icon name="search" size={16}/><span className="sr-only">Buscar conversaciones</span><input type="search" value={historySearch} onChange={event=>setHistorySearch(event.target.value)} placeholder="Buscar en el historial…" autoComplete="off"/>{historySearch && <button type="button" aria-label="Limpiar búsqueda" onClick={()=>setHistorySearch('')}><Icon name="close" size={14}/></button>}</label>
      <nav aria-label="Historial">{visibleSessions.length ? visibleSessions.map(session=><a className={`session ${session.session_id === sessionId ? 'selected' : ''}`} key={session.session_id} title={session.title || 'Consulta postal'} href={chatPath(session.session_id)} aria-current={session.session_id===sessionId ? 'page' : undefined} aria-disabled={busy || loadingChat} onClick={event=>{if(event.ctrlKey || event.metaKey || event.shiftKey || event.altKey)return;event.preventDefault();if(!busy && !loadingChat)void openSession(session.session_id);}}><Icon name="chat" size={17}/><span>{session.title || 'Consulta postal'}</span></a>) : <div className="history-empty"><Icon name="chat" size={24}/><p>{historySearch ? 'No encontramos conversaciones.' : 'Un espacio para tus consultas.'}</p><small>{historySearch ? 'Prueba con otras palabras.' : 'Tu historial aparecerá aquí.'}</small></div>}</nav>
      <div className="sidebar-bottom"><a className="institution-link" href="https://correos.gob.bo/" target="_blank" rel="noreferrer">Sitio de Correos Bolivia <Icon name="arrow" size={16}/></a><div className="local-note"><span className="secure-icon"><Icon name="shield"/></span><div><strong>Espacio interno</strong><small>Consultas de solo lectura</small></div><span className="online-dot"/></div><button className="logout" onClick={logout} disabled={busy || loadingChat}>Cerrar sesión <Icon name="exit" size={16}/></button></div>
    </aside>
    <main className="chat-main">
      <header className="chat-header"><div><button className="menu-button" onClick={()=>setSidebar(true)} aria-label="Abrir historial" aria-expanded={sidebar}><Icon name="menu"/></button><div><p className="eyebrow">CORREOS DE BOLIVIA</p><h1>Asistente postal <span className="internal-tag">INTERNO</span></h1>{sessionId && <p className="chat-code" title="Código de la conversación">Chat: <code>{sessionId}</code></p>}</div></div><div className="header-tools"><span className={`mode-badge ${['demo','fixture'].includes(config?.data_mode || '') ? 'demo' : ''}`}><span className="online-dot"/>{mode}</span><ThemeToggle theme={theme} onToggle={toggleTheme}/></div></header>
      <section id="conversation" className={`conversation ${!messages.length ? 'empty' : ''}`} aria-label="Conversación" aria-busy={busy || loadingChat}>
        {loadingChat ? <p role="status">Cargando conversación guardada…</p> : !messages.length ? <div className="welcome"><PostalMotion/><div className="welcome-label"><span/> CONECTAMOS CONTIGO</div><h2>Tu próxima respuesta <br/>empieza con <em>una pregunta.</em></h2><p>Envíos, oficinas y actividad postal. <br/>La información que necesitas, en una conversación.</p><div className="suggestions">{prompts.map((item,index)=><button key={item.title} style={{animationDelay:`${index*50}ms`}} onClick={()=>void send(item.prompt)}><span className="suggestion-icon"><Icon name={item.icon}/></span><strong>{item.title}</strong><small>{item.text}</small><span className="suggestion-arrow"><Icon name="arrow" size={16}/></span></button>)}</div><button className="capabilities" onClick={()=>void send('¿Qué consultas puedes responder?')}>¿En qué puede ayudarte el asistente? <Icon name="arrow" size={14}/></button></div> : <div className="message-list">{messages.map((message,index)=><MessageView key={index} message={message} token={token} pending={busy && index===messages.length-1 && !message.status}/>)}<div ref={bottom}/></div>}
      </section>
      <div className="composer-area"><div className="request-status" role="status" aria-live="polite">{busy && <><span className="loading-dot" aria-hidden="true"/>{status}</>}</div>{error && <p className="inline-error" role="alert">{error}</p>}<form className="composer" onSubmit={submit}><label className="sr-only" htmlFor="message">Tu consulta</label><textarea id="message" ref={composer} rows={2} maxLength={2000} value={input} onChange={e=>setInput(e.target.value)} placeholder="Pregunta lo que necesitas saber…" disabled={busy || loadingChat} onKeyDown={e=>{if(e.key==='Enter' && !e.shiftKey && !e.nativeEvent.isComposing){e.preventDefault();void send();}}}/><div className="composer-actions"><span><Icon name="shield" size={13}/> Consulta segura · Solo lectura</span><div><span className="keyboard-hint">Enter para enviar</span>{busy ? <button type="button" className="stop" onClick={()=>void cancel()}>■ Detener</button> : <button className="send" disabled={!input.trim() || loadingChat} aria-label="Enviar consulta"><Icon name="send"/></button>}</div></div></form><p className="composer-note">Verifica la fuente y fecha de cada respuesta. {config?.inference_mode === 'rules' ? 'Modo determinista de demostración.' : 'Las conversaciones se guardan en este equipo.'}</p></div>
    </main>
  </div>;
}
