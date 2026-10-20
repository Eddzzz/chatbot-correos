import {useEffect, useRef, useState, type FormEvent} from 'react';
import {Ambient, Brand, Icon, PostalMotion, ThemeToggle} from './PostalUI';
import {Access} from './features/auth/Access';
import {MessageView} from './features/chat/MessageView';
import {DeleteChatDialog} from './features/chat/DeleteChatDialog';
import {api, notifyUnauthorized, resetApiSession, type User, type Message, type Result, type Session} from './shared/api/client';
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
  const [user,setUser] = useState<User|null>(null);
  const [authBusy,setAuthBusy] = useState(false);
  const [restoring,setRestoring] = useState(true);
  const [error,setError] = useState('');
  const currentUser=useRef<User|null>(null);
  const restoreController=useRef<AbortController|null>(null);
  const authAction=useRef(false);
  function replaceUser(value:User|null) {currentUser.current=value;setUser(value);}
  function announceAuthChange() {
    try {localStorage.setItem('correos-auth-change',`${Date.now()}:${Math.random()}`);} catch {}
  }
  function clearSession(message='') {
    restoreController.current?.abort();
    resetApiSession();replaceUser(null);setError(message);
    window.history.replaceState({},'',chatPath(null));
  }
  async function restoreSession(remoteChange=false) {
    if(authAction.current)return;
    restoreController.current?.abort();
    if(remoteChange){clearSession();setRestoring(true);}
    const abort=new AbortController();restoreController.current=abort;
    try {
      const result=await api<{user:User}>('/api/auth/me','',{signal:abort.signal});
      if(abort.signal.aborted)return;
      if(currentUser.current && currentUser.current.user_id!==result.user.user_id){
        resetApiSession();window.history.replaceState({},'',chatPath(null));
      }
      replaceUser(result.user);setError('');
    } catch(e) {
      if(abort.signal.aborted || (e instanceof DOMException && e.name==='AbortError'))return;
      const message=(e as {status?:number}).status===401 ? '' : 'No se pudo restaurar la sesión. Intenta iniciar sesión.';
      if(currentUser.current || remoteChange)clearSession(message);else setError(message);
    } finally {if(restoreController.current===abort)setRestoring(false);}
  }
  useEffect(()=>{
    void restoreSession();
    const changed=(event:StorageEvent)=>{if(event.key==='correos-auth-change')void restoreSession(true);};
    const focused=()=>void restoreSession();
    const resumed=(event:PageTransitionEvent)=>{if(event.persisted)void restoreSession(true);};
    const expired=()=>{clearSession('Tu sesión expiró. Inicia sesión de nuevo.');setRestoring(false);};
    window.addEventListener('storage',changed);
    window.addEventListener('focus',focused);
    window.addEventListener('pageshow',resumed);
    window.addEventListener('session-expired',expired);
    return ()=>{
      restoreController.current?.abort();
      window.removeEventListener('storage',changed);
      window.removeEventListener('focus',focused);
      window.removeEventListener('pageshow',resumed);
      window.removeEventListener('session-expired',expired);
    };
  },[]);
  async function login(username:string,password:string) {
    if(authBusy || restoring)return;
    authAction.current=true;restoreController.current?.abort();setAuthBusy(true);setError('');
    try {
      const result=await api<{user:User}>('/api/auth/login','',{method:'POST',body:JSON.stringify({username,password})});
      resetApiSession();replaceUser(result.user);announceAuthChange();
    } catch(e) {setError(e instanceof Error ? e.message : 'No se pudo iniciar sesión.');}
    finally {authAction.current=false;setAuthBusy(false);}
  }
  async function logout() {
    if(authBusy)return;
    authAction.current=true;setAuthBusy(true);clearSession();
    try {await api('/api/auth/logout','',{method:'POST'});announceAuthChange();}
    catch {setError('No se pudo confirmar el cierre de sesión. Inicia sesión o vuelve a intentarlo al recargar.');}
    finally {authAction.current=false;setAuthBusy(false);}
  }
  if(!user)return <Access onAccess={login} error={error} busy={authBusy || restoring} theme={theme} onToggleTheme={toggleTheme}/>;
  return <Workspace key={user.user_id} user={user} theme={theme} onToggleTheme={toggleTheme} onLogout={()=>void logout()}/>;
}
function Workspace({user,theme,onToggleTheme,onLogout}:{user:User;theme:'light'|'dark';onToggleTheme:()=>void;onLogout:()=>void}) {
  const token='';
  const toggleTheme=onToggleTheme;
  const logout=onLogout;
  const [error,setError]=useState('');
  const [config, setConfig] = useState<Config | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(()=>chatIdFromPath(window.location.pathname));
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);
  const [deletingId,setDeletingId] = useState<string|null>(null);
  const [deleteTarget,setDeleteTarget] = useState<Session|null>(null);
  const [deleteError,setDeleteError] = useState('');
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
      if(busy || loadingChat || deletingId!==null){navigate(sessionId,true);return;}
      const id=chatIdFromPath(window.location.pathname);
      if(id) void openSession(id,token,false);
      else if(!id) {setSessionId(null);setMessages([]);setInput('');setError('');}
    }
    window.addEventListener('popstate',backOrForward);
    return ()=>window.removeEventListener('popstate',backOrForward);
  },[busy,loadingChat,deletingId,sessionId]);
  async function refreshSessions(accessToken = token) { const result = await api<{sessions:Session[]}>('/api/sessions',accessToken); setSessions(result.sessions); }
  useEffect(()=>{
    void refreshSessions().catch(e=>{if(!(e instanceof DOMException && e.name==='AbortError'))setError(e instanceof Error ? e.message : 'No se pudo cargar tu historial.');});
    const id=chatIdFromPath(window.location.pathname);
    if(id)void openSession(id,token,false);
    return ()=>{navigation.current++;};
  },[]);
  async function openSession(id:string,accessToken=token,updateUrl=true) {
    const current=++navigation.current;
    setError('');setLoadingChat(true);setMessages([]);
    try {const result = await api<{messages:Message[]}>(`/api/sessions/${encodeURIComponent(id)}`,accessToken);if(current!==navigation.current)return;setSessionId(id);setMessages(result.messages);setInput('');if(updateUrl)navigate(id);setSidebar(false);composer.current?.focus();}
    catch(e) {if(current===navigation.current){setSessionId(null);setError(e instanceof Error ? e.message : 'No se pudo cargar la conversación.');}}
    finally {if(current===navigation.current)setLoadingChat(false);}
  }
  function newSession() {if (busy || loadingChat || deletingId!==null) return;navigation.current++;navigate(null);setSessionId(null);setMessages([]);setInput('');setError('');setSidebar(false);composer.current?.focus();}
  async function deleteSession(session:Session) {
    if (busy || loadingChat || deletingId!==null) return;
    setDeletingId(session.session_id);setDeleteError('');setError('');
    try {
      await api(`/api/sessions/${encodeURIComponent(session.session_id)}`,token,{method:'DELETE'});
      setSessions(previous=>previous.filter(item=>item.session_id!==session.session_id));
      if (session.session_id===sessionId) {
        navigation.current++;navigate(null,true);setSessionId(null);setMessages([]);setInput('');setSidebar(false);
      }
      setDeleteTarget(null);
    } catch(e) {setDeleteError(e instanceof Error ? e.message : 'No se pudo eliminar la conversación.');}
    finally {setDeletingId(null);}
  }
  async function cancel() {
    const id = requestId.current;
    controller.current?.abort();
    if (id) try {await api(`/api/requests/${encodeURIComponent(id)}/cancel`,token,{method:'POST'});} catch {setError('La conexión se detuvo. No se pudo confirmar la cancelación en el servidor.');}
  }
  async function send(text = input, editIndex?:number) {
    text = text.trim(); if (!text || busy || loadingChat || deletingId!==null) return;
    const originalMessages = messages;
    const startedAt = performance.now();
    setBusy(true);setError('');setInput('');setStatus('Conectando con el asistente…');requestId.current='';
    setMessages(previous=>[...(editIndex===undefined ? previous : previous.slice(0,editIndex)),{role:'user',content:text},{role:'assistant',content:''}]);
    const abort = new AbortController();controller.current=abort;
    let terminal = false;
    const update = (values:Partial<Message>) => setMessages(previous=>previous.map((m,i)=>i===previous.length-1 ? {...m,...values} : m));
    try {
      const response = await fetch('/api/chat/stream',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text,session_id:sessionId,edit_message_index:editIndex}),signal:abort.signal});
      if (!response.ok) {if(response.status===401)notifyUnauthorized();throw new Error(response.status===401 ? 'Tu sesión expiró. Inicia sesión de nuevo.' : `El servicio no pudo responder (${response.status}).`);}
      if (!response.body || !response.headers.get('content-type')?.includes('text/event-stream')) throw new Error('El servidor no entregó una conversación válida.');
      await readEvents(response.body,({event,data})=>{
        abort.signal.throwIfAborted();
        if (typeof data.request_id === 'string') {
          if (requestId.current && data.request_id !== requestId.current) throw new Error('La respuesta pertenece a otra solicitud.');
          requestId.current = data.request_id;
        }
        if (event==='request_started') {update({request_id:requestId.current});if(typeof data.session_id==='string'){setSessionId(data.session_id);navigate(data.session_id);}}
        if (event==='status') setStatus(String(data.message || data.status || 'Consultando información…'));
        if (event==='answer_chunk') setMessages(previous=>previous.map((m,i)=>i===previous.length-1 ? {...m,content:m.content + String(data.text || '')} : m));
        if (event==='completed') {terminal=true;update({...data as Result,content:String(data.answer || ''),response_seconds:(performance.now()-startedAt)/1000});}
        if (event==='error') {terminal=true;if(data.code==='unauthenticated')notifyUnauthorized();throw new Error(String(data.message || 'No se pudo completar la consulta.'));}
      });
      if (!terminal) throw new Error('La conexión se interrumpió antes de completar la respuesta. Vuelve a intentarlo.');
    } catch(e) {
      const message = abort.signal.aborted ? 'Consulta detenida.' : e instanceof Error ? e.message : 'No se pudo conectar. Verifica que el servicio esté disponible.';
      update({status:'error',response_seconds:(performance.now()-startedAt)/1000});
      setMessages(previous=>previous.map((m,i)=>i===previous.length-1 && !m.content ? {...m,content:message} : m));
      if (!abort.signal.aborted) setError(message);
      if(editIndex!==undefined && sessionId && !abort.signal.aborted){
        try{const saved=await api<{messages:Message[]}>(`/api/sessions/${encodeURIComponent(sessionId)}`,token);setMessages(saved.messages);}
        catch{setMessages(originalMessages);}
      }
      return false;
    } finally {try{if(!abort.signal.aborted)await refreshSessions();}catch{/* Keep the saved chat URL available when history refresh fails. */}setBusy(false);setStatus('');controller.current=null;requestId.current='';composer.current?.focus();}
    return true;
  }
  function submit(event:FormEvent) {event.preventDefault();void send();}
  const mode = config?.data_mode === 'fixture' ? 'Datos ficticios · PostgreSQL de prueba' : config?.data_mode === 'demo' ? 'Datos ficticios · Demostración' : config?.data_mode === 'postgres' ? (config.data_snapshot ? `Datos reales · respaldo ${config.data_snapshot.slice(0,10)}` : 'Base institucional') : 'Datos sin configurar';
  return <div className="workspace">
    <Ambient/>
    <a className="skip-link" href="#conversation">Ir a la conversación</a>
    {sidebar && <button className="sidebar-backdrop" aria-label="Cerrar historial" onClick={()=>setSidebar(false)}/>}
    <aside className={`sidebar ${sidebar ? 'is-open' : ''}`} aria-label="Conversaciones" onKeyDown={event=>{if(event.key==='Escape'){setSidebar(false);document.querySelector<HTMLButtonElement>('.menu-button')?.focus();}}}>
      <div className="sidebar-brand"><Brand/><button className="mobile-close" aria-label="Cerrar historial" onClick={()=>setSidebar(false)}><Icon name="close"/></button></div>
      <button className="new-chat" onClick={newSession} disabled={busy || loadingChat || deletingId!==null}><Icon name="plus"/> Nueva conversación </button>
      <div className="history-heading">Conversaciones <span>{sessions.length}</span></div>
      <label className="history-search"><Icon name="search" size={16}/><span className="sr-only">Buscar conversaciones</span><input type="search" value={historySearch} onChange={event=>setHistorySearch(event.target.value)} placeholder="Buscar en el historial…" autoComplete="off"/>{historySearch && <button type="button" aria-label="Limpiar búsqueda" onClick={()=>setHistorySearch('')}><Icon name="close" size={14}/></button>}</label>
      <nav aria-label="Historial">{visibleSessions.length ? visibleSessions.map(session=><div className="session-row" key={session.session_id}><a className={`session ${session.session_id === sessionId ? 'selected' : ''}`} title={session.title || 'Consulta postal'} href={chatPath(session.session_id)} aria-current={session.session_id===sessionId ? 'page' : undefined} aria-disabled={busy || loadingChat || deletingId!==null} onClick={event=>{if(event.ctrlKey || event.metaKey || event.shiftKey || event.altKey)return;event.preventDefault();if(!busy && !loadingChat)void openSession(session.session_id);}}><Icon name="chat" size={17}/><span>{session.title || 'Consulta postal'}</span></a><button type="button" className="delete-session" title="Eliminar chat" aria-label={`Eliminar chat: ${session.title || 'Consulta postal'}`} disabled={busy || loadingChat || deletingId!==null} onClick={()=>{setDeleteError('');setDeleteTarget(session);}}><Icon name="trash" size={16}/></button></div>) : <div className="history-empty"><Icon name="chat" size={24}/><p>{historySearch ? 'No encontramos conversaciones.' : 'Un espacio para tus consultas.'}</p><small>{historySearch ? 'Prueba con otras palabras.' : 'Tu historial aparecerá aquí.'}</small></div>}</nav>
      <div className="sidebar-bottom"><a className="institution-link" href="https://correos.gob.bo/" target="_blank" rel="noreferrer">Sitio de Correos Bolivia <Icon name="arrow" size={16}/></a><div className="local-note"><span className="secure-icon"><Icon name="shield"/></span><div><strong>{user.display_name || user.username}</strong><small>{user.username} · Mi cuenta</small></div><span className="online-dot"/></div><button className="logout" onClick={logout} disabled={busy || loadingChat || deletingId!==null}>Cerrar sesión <Icon name="exit" size={16}/></button></div>
    </aside>
    <main className="chat-main">
      <header className="chat-header"><div><button className="menu-button" onClick={()=>setSidebar(true)} aria-label="Abrir historial" aria-expanded={sidebar}><Icon name="menu"/></button><div><p className="eyebrow">CORREOS DE BOLIVIA</p><h1>Asistente postal <span className="internal-tag">INTERNO</span></h1>{sessionId && <p className="chat-code" title="Código de la conversación">Chat: <code>{sessionId}</code></p>}</div></div><div className="header-tools"><span className={`mode-badge ${['demo','fixture'].includes(config?.data_mode || '') ? 'demo' : ''}`}><span className="online-dot"/>{mode}</span><ThemeToggle theme={theme} onToggle={toggleTheme}/></div></header>
      <section id="conversation" className={`conversation ${!messages.length ? 'empty' : ''}`} aria-label="Conversación" aria-busy={busy || loadingChat || deletingId!==null}>
        {loadingChat ? <p role="status">Cargando conversación guardada…</p> : !messages.length ? <div className="welcome"><PostalMotion/><div className="welcome-label"><span/> CONECTAMOS CONTIGO</div><h2>Tu próxima respuesta <br/>empieza con <em>una pregunta.</em></h2><p>Envíos, oficinas y actividad postal. <br/>La información que necesitas, en una conversación.</p><div className="suggestions">{prompts.map((item,index)=><button key={item.title} style={{animationDelay:`${index*50}ms`}} onClick={()=>void send(item.prompt)}><span className="suggestion-icon"><Icon name={item.icon}/></span><strong>{item.title}</strong><small>{item.text}</small><span className="suggestion-arrow"><Icon name="arrow" size={16}/></span></button>)}</div><button className="capabilities" onClick={()=>void send('¿Qué consultas puedes responder?')}>¿En qué puede ayudarte el asistente? <Icon name="arrow" size={14}/></button></div> : <div className="message-list">{messages.map((message,index)=><MessageView key={index} message={message} token={token} onEdit={message.role==='user' ? text=>send(text,index) : undefined} editDisabled={busy || loadingChat || deletingId!==null} pending={busy && index===messages.length-1 && !message.status}/>)}<div ref={bottom}/></div>}
      </section>
      <div className="composer-area"><div className="request-status" role="status" aria-live="polite">{busy && <><span className="loading-dot" aria-hidden="true"/>{status}</>}</div>{error && <p className="inline-error" role="alert">{error}</p>}<form className="composer" onSubmit={submit}><label className="sr-only" htmlFor="message">Tu consulta</label><textarea id="message" ref={composer} rows={2} maxLength={2000} value={input} onChange={e=>setInput(e.target.value)} placeholder="Pregunta lo que necesitas saber…" disabled={busy || loadingChat || deletingId!==null} onKeyDown={e=>{if(e.key==='Enter' && !e.shiftKey && !e.nativeEvent.isComposing){e.preventDefault();void send();}}}/><div className="composer-actions"><span><Icon name="shield" size={13}/> Consulta segura · Solo lectura</span><div><span className="keyboard-hint">Enter para enviar</span>{busy ? <button type="button" className="stop" onClick={()=>void cancel()}>■ Detener</button> : <button className="send" disabled={!input.trim() || loadingChat || deletingId!==null} aria-label="Enviar consulta"><Icon name="send"/></button>}</div></div></form><p className="composer-note">Verifica la fuente y fecha de cada respuesta. {config?.inference_mode === 'rules' ? 'Modo determinista de demostración.' : 'Las conversaciones se guardan en tu cuenta.'}</p></div>
    </main>
    {deleteTarget && <DeleteChatDialog title={deleteTarget.title || 'Consulta postal'} busy={deletingId!==null} error={deleteError} onCancel={()=>setDeleteTarget(null)} onConfirm={()=>void deleteSession(deleteTarget)}/>}
  </div>;
}
