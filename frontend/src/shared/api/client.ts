export type PostalRecordFilters = {start_date:string;end_date:string;family:string|null};
export type Result = {request_id?: string; status?: string; answer?: string; rows?: Record<string, unknown>[]; columns?: string[]; source?: string; queried_at?: string; record_browser?:PostalRecordFilters|null};
export type Message = Result & {role: 'user' | 'assistant'; content: string; response_seconds?: number};
export type Session = {session_id: string; title: string; updated_at?: string};
export type User = {user_id:string;username:string;display_name:string};
export class ApiError extends Error {
  constructor(public status:number,message:string) {super(message);this.name='ApiError';}
}
let sessionController = new AbortController();
export function resetApiSession() {
  sessionController.abort();
  sessionController = new AbortController();
}
export function notifyUnauthorized() {window.dispatchEvent(new Event('session-expired'));}
export async function api<T>(path: string, token = '', init?: RequestInit): Promise<T> {
  const signal = init?.signal ? AbortSignal.any([sessionController.signal,init.signal]) : sessionController.signal;
  const headers = new Headers(init?.headers);
  headers.set('Content-Type','application/json');
  if(token) headers.set('Authorization',`Bearer ${token}`);
  const response = await fetch(path, {...init, credentials:'same-origin', signal, headers});
  signal.throwIfAborted();
  if (!response.ok) {
    if(response.status===401 && !path.startsWith('/api/auth/')) notifyUnauthorized();
    throw new ApiError(response.status,response.status === 401 ? (path==='/api/auth/login' ? 'Usuario o contraseña incorrectos.' : 'Tu sesión expiró. Inicia sesión de nuevo.') : response.status === 429 ? 'Demasiados intentos. Espera unos minutos antes de volver a intentarlo.' : response.status === 403 ? 'No tienes permiso para esta operación.' : `No se pudo completar la solicitud (${response.status}).`);
  }
  const result = response.status===204 ? undefined : await response.json();
  signal.throwIfAborted();
  return result as T;
}
