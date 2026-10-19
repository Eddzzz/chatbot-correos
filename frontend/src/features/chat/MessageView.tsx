import {PostalMascot} from './PostalMascot';
import {Icon} from '../../PostalUI';
import {categoryName} from './relationLanguage';
import {PostalRecords} from './PostalRecords';
import {DetailView} from './DetailView';
import {isInternalField,displayValue} from './detailPresentation';
import type {Message} from '../../shared/api/client';
import {api} from '../../shared/api/client';
import {useEffect,useRef,useState} from 'react';
const statusNames: Record<string,string> = {answer:'Respuesta verificada',no_results:'Sin resultados',needs_clarification:'Necesita precisión',unsupported:'Consulta no disponible',out_of_scope:'Fuera del alcance',forbidden:'Acceso restringido',error:'Solicitud interrumpida'};
const columnNames: Record<string,string> = {source:'Familia',tracking_code:'Código de seguimiento',status:'Estado',origin:'Origen',destination:'Destino',registered_at:'Fecha de registro',updated_at:'Última actualización',office_id:'Referencia de sucursal',codigo_sucursal:'Código de sucursal',municipality:'Municipio',department:'Departamento',office:'Sucursal por municipio de destino',phone:'Teléfono institucional',total:'Registros',nombre:'Nombre',correo_electronico:'Correo electrónico',documento_identidad:'Documento de identidad',fecha_registro:'Fecha de registro',ciudad:'Ciudad',sucursal:'Sucursal',departamento:'Departamento'};
type RelatedTable = {table_name:string;total_count:number;relation_kind:string;path_info:unknown;descendant_count:number;lookup_count:number};
type RelatedPage = {rows:{record_key:string;record:unknown;relation_kind:string}[];total_count:number;next_offset:number|null;offset:number;source:string;queried_at:string};
function OfficeRelations({officeId,token}: {officeId:number;token:string}) {
  const [tables,setTables]=useState<RelatedTable[]>([]);
  const [inventoryBusy,setInventoryBusy]=useState(true);
  const [inventoryError,setInventoryError]=useState('');
  const [inventoryLimited,setInventoryLimited]=useState(false);
  useEffect(()=>{const controller=new AbortController();
    api<{rows:RelatedTable[];truncated:boolean}>(`/api/offices/${officeId}/relations`,token,{signal:controller.signal})
      .then(result=>{setTables(result.rows);setInventoryLimited(result.truncated);})
      .catch(error=>{if(!controller.signal.aborted)setInventoryError(error instanceof Error?error.message:'No se pudo cargar el inventario.');})
      .finally(()=>{if(!controller.signal.aborted)setInventoryBusy(false);});
    return ()=>controller.abort();},[officeId,token]);
  const [filter,setFilter]=useState('');
  const [selected,setSelected]=useState('');
  const [page,setPage]=useState<RelatedPage|null>(null);
  const [previous,setPrevious]=useState<number[]>([]);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  async function load(table:string,offset=0,history:number[]=[]) {
    setBusy(true);setError('');setSelected(table);setPage(null);
    try {setPage(await api<RelatedPage>(`/api/offices/${officeId}/relations/${encodeURIComponent(table)}?offset=${offset}&limit=10`,token));setPrevious(history);}
    catch(error){setError(error instanceof Error ? error.message : 'No se pudieron cargar los registros asociados.');}
    finally{setBusy(false);}
  }
  const available=tables.filter(table=>table.total_count>0);
  if (!inventoryBusy && !inventoryError && !inventoryLimited && available.length===0) return null;
  return <section className="office-relations" aria-label="Información de la consulta">
    <h3>Lo que sabemos de esta sucursal</h3>
    {inventoryBusy && <p role="status">Buscando la información…</p>}
    {inventoryError && <p role="alert">{inventoryError}</p>}
    {inventoryLimited && <p role="alert">La lista está limitada; puede haber más información disponible.</p>}
    {!inventoryBusy && !inventoryError && <p>Hay información en {available.length} {available.length===1?'categoría':'categorías'}. Selecciona la que quieras consultar.</p>}
    <label>Buscar información<input value={filter} onChange={event=>setFilter(event.target.value)} placeholder="Por ejemplo: envíos, personal o vehículos"/></label>
    <div className="relation-stories" role="region" aria-label="Información por categoría">
      {available.filter(table=>categoryName(table.table_name).toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g,'').includes(filter.toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g,''))).map(table=><section key={table.table_name} className="relation-story">
        <h4>{categoryName(table.table_name)}</h4><p>{table.total_count.toLocaleString('es-BO')} {table.total_count===1?'registro disponible':'registros disponibles'}.</p>
        {table.total_count>0 && <button type="button" disabled={busy} aria-expanded={selected===table.table_name} onClick={()=>selected===table.table_name ? setSelected('') : void load(table.table_name)}>{selected===table.table_name ? 'Ocultar' : 'Ver'} {categoryName(table.table_name).toLocaleLowerCase('es')}</button>}
        {selected===table.table_name && <div className="relation-result" aria-busy={busy}>
          {busy && <p role="status">Consultando {categoryName(selected).toLocaleLowerCase('es')}…</p>}
          {error && <p role="alert">{error}</p>}
          {page && <section className="related-page" aria-label={`Registros de ${categoryName(selected)}`}>
            <h4>{categoryName(selected)}</h4><p>{page.rows.length ? `Te muestro los registros ${page.offset+1} al ${page.offset+page.rows.length} de un total de ${page.total_count.toLocaleString('es-BO')}` : 'No hay registros en esta página'}. Fuente: {page.source}</p>
            {page.rows.map(row=><DetailView key={row.record_key} value={row.record} title={categoryName(selected)}/>)}
            <div className="related-pagination"><button type="button" disabled={busy || previous.length===0} onClick={()=>void load(selected,previous[previous.length-1],previous.slice(0,-1))}>Anterior</button><button type="button" disabled={busy || page.next_offset===null} onClick={()=>page.next_offset!==null && void load(selected,page.next_offset,[...previous,page.offset])}>Siguiente</button></div>
          </section>}
        </div>}
      </section>)}
    </div>
  </section>;

}
export function MessageView({message,token,pending=false,onEdit,editDisabled=false}: {message:Message;token:string;pending?:boolean;onEdit?:(text:string)=>Promise<boolean|undefined>;editDisabled?:boolean}) {
  const [editing,setEditing]=useState(false);
  const [draft,setDraft]=useState(message.content);
  const [copyStatus,setCopyStatus]=useState<'idle'|'copied'|'error'>('idle');
  const editField=useRef<HTMLTextAreaElement>(null);
  useEffect(()=>{if(editing && editField.current){editField.current.style.height='auto';editField.current.style.height=`${editField.current.scrollHeight}px`;}},[editing,draft]);
  useEffect(()=>{if(copyStatus==='idle')return;const timer=window.setTimeout(()=>setCopyStatus('idle'),2000);return()=>window.clearTimeout(timer);},[copyStatus]);
  async function copyQuery(){try{await navigator.clipboard.writeText(message.content);setCopyStatus('copied');}catch{setCopyStatus('error');}}
  useEffect(()=>{setEditing(false);setDraft(message.content);},[message.content]);
  const editor=message.role==='user' && onEdit && (editing ? <form className="message-edit" onSubmit={event=>{event.preventDefault();if(draft.trim() && !editDisabled)void onEdit(draft).then(saved=>{if(saved)setEditing(false);});}}>
    <textarea ref={editField} aria-label="Editar consulta" autoFocus rows={1} maxLength={2000} value={draft} disabled={editDisabled} onChange={event=>setDraft(event.target.value)} onKeyDown={event=>{if(event.key==='Escape' && !editDisabled)setEditing(false);}}/>
    <div><button type="button" aria-label="Cancelar edición" title="Cancelar edición" disabled={editDisabled} onClick={()=>setEditing(false)}><Icon name="close" size={18}/></button><button type="submit" aria-label="Guardar y reenviar" title="Guardar y reenviar" disabled={editDisabled || !draft.trim()}><Icon name="check" size={18}/></button></div>
  </form> : <div className="message-actions"><button type="button" aria-label={copyStatus==='copied'?'Consulta copiada':'Copiar consulta'} title={copyStatus==='copied'?'Copiado':'Copiar consulta'} onClick={()=>void copyQuery()}><Icon name={copyStatus==='copied'?'check':'copy'} size={16}/></button><button type="button" className="edit-query" aria-label="Editar consulta" title="Editar consulta" disabled={editDisabled} onClick={()=>{setDraft(message.content);setEditing(true);}}><Icon name="pencil" size={16}/></button><span className="sr-only" role="status">{copyStatus==='copied'?'Consulta copiada':copyStatus==='error'?'No se pudo copiar la consulta. Intenta nuevamente.':''}</span></div>);

  const responseTime = message.role === 'assistant' && message.response_seconds != null
    ? <small className="response-time" title="Tiempo de respuesta" aria-label={`Tiempo de respuesta: ${message.response_seconds.toFixed(1)} segundos`}>{message.response_seconds.toLocaleString('es-BO',{minimumFractionDigits:1,maximumFractionDigits:1})} s</small>
    : null;
  const columns = (message.columns?.length ? message.columns : Object.keys(message.rows?.[0] || {})).filter(column=>!isInternalField(column));
  return <article className={`message ${message.role}${editing ? " is-editing" : ""}`}>{responseTime}{message.role === 'assistant' && <div className="message-author"><span className="assistant-mark" aria-hidden="true">↗</span> Asistente postal</div>}{pending && <PostalMascot/>}{!editing && (message.content || !pending) && <p className="message-text">{message.content || 'Preparando la respuesta…'}</p>}{editor}{!!message.rows?.length && message.rows.some(row=>row.details && typeof row.details === 'object') ? <section className="full-details" aria-label="Ficha completa y datos asociados">{message.rows.map((row,index)=><section key={index}><DetailView value={row.details}/>{typeof row.office_id==='number' && <OfficeRelations officeId={row.office_id} token={token}/>}</section>)}</section> : !!message.rows?.length && <div className="table-scroll" tabIndex={0} role="region" aria-label="Resultados de la consulta"><table><caption>Datos de la consulta</caption><thead><tr>{columns.map(column=><th key={column} scope="col">{columnNames[column] || column.replaceAll('_',' ')}</th>)}</tr></thead><tbody>{message.rows.map((row,index)=><tr key={index}>{columns.map(column=><td key={column}>{row[column] == null ? '—' : typeof row[column] === 'object' ? JSON.stringify(row[column]) : displayValue(column,row[column])}</td>)}</tr>)}</tbody></table></div>}{message.role === 'assistant' && message.record_browser && <PostalRecords key={JSON.stringify(message.record_browser)} filters={message.record_browser} token={token}/>} {message.role === 'assistant' && (message.source || message.queried_at || message.status) && <footer className="evidence">{message.status && <span>{statusNames[message.status] || message.status}</span>}{message.source && <span>Fuente: {message.source}</span>}{message.queried_at && <time dateTime={message.queried_at}>{new Date(message.queried_at).toLocaleString('es-BO',{timeZone:'America/La_Paz'})}</time>}</footer>}</article>;
}
