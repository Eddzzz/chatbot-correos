export function chatIdFromPath(path:string):string|null {
  return /^\/c\/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\/?$/.exec(path)?.[1] || null;
}
export function chatPath(id:string|null):string {return id ? `/c/${encodeURIComponent(id)}` : '/';}
