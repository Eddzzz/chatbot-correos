export type Result = {request_id?: string; status?: string; answer?: string; rows?: Record<string, unknown>[]; columns?: string[]; source?: string; queried_at?: string};
export type Message = Result & {role: 'user' | 'assistant'; content: string};
export type Session = {session_id: string; title: string; updated_at?: string};
export async function api<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {...init, headers: {...init?.headers, Authorization:`Bearer ${token}`, 'Content-Type':'application/json'}});
  if (!response.ok) throw new Error(response.status === 401 ? 'La clave de acceso no es válida o expiró.' : response.status === 403 ? 'No tienes permiso para esta operación.' : `No se pudo completar la solicitud (${response.status}).`);
  return response.json() as Promise<T>;
}
