import {categoryName} from './relationLanguage';
import type {Message} from '../../shared/api/client';
import {api} from '../../shared/api/client';
import {useEffect,useState} from 'react';
const statusNames: Record<string,string> = {answer:'Respuesta verificada',no_results:'Sin resultados',needs_clarification:'Necesita precisión',unsupported:'Consulta no disponible',out_of_scope:'Fuera del alcance',forbidden:'Acceso restringido',error:'Solicitud interrumpida'};
const columnNames: Record<string,string> = {source:'Familia',tracking_code:'Código de seguimiento',status:'Estado',origin:'Origen',destination:'Destino',registered_at:'Fecha de registro',updated_at:'Última actualización',office_id:'Referencia de sucursal',codigo_sucursal:'Código de sucursal',municipality:'Municipio',department:'Departamento',phone:'Teléfono institucional',total:'Registros'};
const detailLabels: Record<string,string> = {...columnNames,tabla:'Tabla de origen',campos:'Datos del registro',relaciones:'Datos asociados',omitidos:'Campos excluidos',registros:'Registros asociados',truncado:'Lista limitada',usuarios_asignados:'Usuarios asignados',puntoVenta:'Punto de venta',codigoSucursal:'Código de sucursal',municipio:'Municipio',departamento:'Departamento',telefono:'Teléfono',created_at:'Fecha de registro',updated_at:'Última actualización',name:'Nombre',email:'Correo electrónico',ci:'Documento de identidad',nombre_r:'Nombre del remitente',telefono_r:'Teléfono del remitente',direccion_r:'Dirección del remitente',nombre_d:'Nombre del destinatario',telefono_d:'Teléfono del destinatario',direccion_d:'Dirección del destinatario',nombre_remitente:'Nombre del remitente',nombre_destinatario:'Nombre del destinatario',telefono_remitente:'Teléfono del remitente',telefono_destinatario:'Teléfono del destinatario',fk_estado:'Estado asociado',estado_id:'Estado asociado',estados_id:'Estado asociado',user_id:'Usuario asociado',sucursal_id:'Sucursal asociada',servicio_id:'Servicio asociado',empresa_id:'Empresa asociada',tarifario_id:'Tarifa de referencia',tarifa_contrato_id:'Tarifa de contrato',fk_ventanilla:'Ventanilla asociada'};
function DetailValue({value,depth=0}: {value:unknown;depth?:number}) {
  if(value == null) return <span className="detail-empty">Sin dato</span>;
  if(Array.isArray(value)) return value.length ? <div className="detail-records">{value.map((item,index)=><div key={index}>{typeof item === 'object' && item !== null ? <details open={depth<2}><summary>Registro {index+1}</summary><DetailValue value={item} depth={depth+1}/></details> : <DetailValue value={item} depth={depth+1}/>}</div>)}</div> : <span className="detail-empty">Sin registros asociados</span>;
  if(typeof value === 'object') return <dl className="detail-fields">{Object.entries(value).map(([key,item])=><div key={key}><dt>{detailLabels[key] || key.replaceAll('_',' ')}</dt><dd>{typeof item === 'object' && item !== null ? <details open={depth<1}><summary>{Array.isArray(item) ? `${item.length} elementos` : 'Ver datos'}</summary><DetailValue value={item} depth={depth+1}/></details> : <DetailValue value={key==='tabla' && typeof item==='string' ? categoryName(item) : item} depth={depth+1}/>}</dd></div>)}</dl>;
  return <span>{typeof value === 'boolean' ? (value ? 'Sí' : 'No') : String(value)}</span>;
}
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
  const available=tables.filter(table=>table.total_count>0).length;
  return <section className="office-relations" aria-label="Información de la consulta">
    <h3>Lo que sabemos de esta sucursal</h3>
    {inventoryBusy && <p role="status">Buscando la información…</p>}
    {inventoryError && <p role="alert">{inventoryError}</p>}
    {inventoryLimited && <p role="alert">La lista está limitada; puede haber más información disponible.</p>}
    {!inventoryBusy && !inventoryError && <p>Encontré información en {available} de las {tables.length} categorías consultadas. Abre una categoría para ver sus datos completos.</p>}
    <label>Buscar información<input value={filter} onChange={event=>setFilter(event.target.value)} placeholder="Por ejemplo: envíos, personal o vehículos"/></label>
    <div className="relation-stories" role="region" aria-label="Información por categoría">
      {tables.filter(table=>categoryName(table.table_name).toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g,'').includes(filter.toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g,''))).map(table=><section key={table.table_name} className="relation-story">
        <h4>{categoryName(table.table_name)}</h4><p>{table.total_count ? `${table.total_count.toLocaleString('es-BO')} ${table.total_count===1?'registro disponible':'registros disponibles'}.` : 'Sin datos en el respaldo consultado.'}</p>
        {table.total_count>0 && <button type="button" disabled={busy} onClick={()=>void load(table.table_name)}>Ver {categoryName(table.table_name).toLocaleLowerCase('es')}</button>}
      </section>)}
    </div>
    {busy && <p role="status">Consultando {categoryName(selected).toLocaleLowerCase('es')}…</p>}
    {error && <p role="alert">{error}</p>}
    {page && <section className="related-page" aria-label={`Registros de ${categoryName(selected)}`}>
      <h4>{categoryName(selected)}</h4><p>{page.rows.length ? `Te muestro los registros ${page.offset+1} al ${page.offset+page.rows.length} de un total de ${page.total_count.toLocaleString('es-BO')}` : 'No hay registros en esta página'}. Fuente: {page.source}</p>
      {page.rows.map(row=><details key={row.record_key}><summary>Registro {row.record_key}</summary><DetailValue value={row.record}/></details>)}
      <div className="related-pagination"><button type="button" disabled={busy || previous.length===0} onClick={()=>void load(selected,previous[previous.length-1],previous.slice(0,-1))}>Anterior</button><button type="button" disabled={busy || page.next_offset===null} onClick={()=>page.next_offset!==null && void load(selected,page.next_offset,[...previous,page.offset])}>Siguiente</button></div>
    </section>}
  </section>;

}
export function MessageView({message,token}: {message:Message;token:string}) {
  const columns = message.columns?.length ? message.columns : Object.keys(message.rows?.[0] || {});
  return <article className={`message ${message.role}`}><div className="message-author">{message.role === 'user' ? 'Tú' : <><span className="assistant-mark" aria-hidden="true">↗</span> Asistente postal</>}</div><p className="message-text">{message.content || 'Preparando la respuesta…'}</p>{!!message.rows?.length && message.rows.some(row=>row.details && typeof row.details === 'object') ? <section className="full-details" aria-label="Ficha completa y datos asociados">{message.rows.map((row,index)=><section key={index}><h3>Ficha {index+1}</h3><DetailValue value={Object.fromEntries(Object.entries(row.details as Record<string,unknown>).filter(([key])=>key!=='tablas_asociadas'))}/>{typeof row.office_id==='number' && <OfficeRelations officeId={row.office_id} token={token}/>}</section>)}</section> : !!message.rows?.length && <div className="table-scroll" tabIndex={0} role="region" aria-label="Resultados de la consulta"><table><caption>Datos de la consulta</caption><thead><tr>{columns.map(column=><th key={column} scope="col">{columnNames[column] || column.replaceAll('_',' ')}</th>)}</tr></thead><tbody>{message.rows.map((row,index)=><tr key={index}>{columns.map(column=><td key={column}>{row[column] == null ? '—' : typeof row[column] === 'object' ? JSON.stringify(row[column]) : String(row[column])}</td>)}</tr>)}</tbody></table></div>}{message.role === 'assistant' && (message.source || message.queried_at || message.status) && <footer className="evidence">{message.status && <span>{statusNames[message.status] || message.status}</span>}{message.source && <span>Fuente: {message.source}</span>}{message.queried_at && <time dateTime={message.queried_at}>{new Date(message.queried_at).toLocaleString('es-BO',{timeZone:'America/La_Paz'})}</time>}</footer>}</article>;
}
