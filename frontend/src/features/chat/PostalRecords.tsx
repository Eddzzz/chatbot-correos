import {useEffect,useState} from 'react';
import {api,type PostalRecordFilters} from '../../shared/api/client';

type PostalRecord = {
  source:string;tracking_code:string|null;status:string|null;origin:string|null;
  destination:string|null;registered_at:string|null;updated_at:string|null;
};
type PostalPage = {
  rows:PostalRecord[];offset:number;next_offset:number|null;source:string;
  queried_at:string;truncated:boolean;
};
const families:Record<string,string> = {
  ems:'EMS',certi:'Certificados',ordi:'Ordinarios',contrato:'Contratos',int:'Internacionales',
};
function dateLabel(value:string|null) {
  if(!value)return 'Sin fecha';
  const local=/^(\d{4})-(\d{2})-(\d{2})(?:T| )(\d{2}:\d{2}:\d{2})(?:\.\d+)?$/.exec(value);
  if(local)return `${local[3]}/${local[2]}/${local[1]} ${local[4]}`;
  const date=new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('es-BO',{timeZone:'America/La_Paz'});
}

export function PostalRecords({filters,token}:{filters:PostalRecordFilters;token:string}) {
  const [navigation,setNavigation]=useState({offset:0,previous:[] as number[],attempt:0});
  const [page,setPage]=useState<PostalPage|null>(null);
  const [busy,setBusy]=useState(true);
  const [error,setError]=useState('');
  const {start_date,end_date,family}=filters;
  useEffect(()=>{
    const controller=new AbortController();
    const query=new URLSearchParams({start_date,end_date,offset:String(navigation.offset),limit:'10'});
    if(family)query.set('family',family);
    setBusy(true);setError('');setPage(null);
    api<PostalPage>(`/api/postal-records?${query}`,token,{signal:controller.signal})
      .then(result=>{if(!controller.signal.aborted)setPage(result);})
      .catch(cause=>{if(!controller.signal.aborted)setError(cause instanceof Error ? cause.message : 'No se pudieron consultar los registros.');})
      .finally(()=>{if(!controller.signal.aborted)setBusy(false);});
    return ()=>controller.abort();
  },[start_date,end_date,family,token,navigation]);
  function navigate(offset:number,previous:number[]) {
    setPage(null);setBusy(true);setNavigation({offset,previous,attempt:0});
  }
  return <section className="postal-records" aria-label="Registros individuales" aria-busy={busy}>
    <h3>Registros individuales{family ? ` · ${families[family] || family}` : ''}</h3>
    {busy && <p role="status">Consultando los registros…</p>}
    {error && <div role="alert"><p>{error}</p><button type="button" onClick={()=>setNavigation(current=>({...current,attempt:current.attempt+1}))}>Volver a intentar</button></div>}
    {page && <>
      <p role="status">{page.rows.length ? `Te muestro los registros ${page.offset+1} al ${page.offset+page.rows.length}.` : 'No hay registros en esta página.'}</p>
      {!!page.rows.length && <div className="table-scroll" tabIndex={0} role="region" aria-label="Registros postales individuales">
        <table><caption>Registros del periodo consultado</caption>
          <thead><tr>{['Familia','Código de seguimiento','Estado','Origen','Destino','Fecha de registro','Última actualización'].map(label=><th key={label} scope="col">{label}</th>)}</tr></thead>
          <tbody>{page.rows.map((row,index)=><tr key={`${row.source}-${row.tracking_code}-${index}`}>
            <td>{families[row.source] || row.source}</td><td>{row.tracking_code || 'Sin código'}</td>
            <td>{row.status || 'Sin dato'}</td><td>{row.origin || 'Sin dato'}</td><td>{row.destination || 'Sin dato'}</td>
            <td>{dateLabel(row.registered_at)}</td><td>{dateLabel(row.updated_at)}</td>
          </tr>)}</tbody>
        </table>
      </div>}
      <p className="postal-records-source">Fuente: {page.source}</p>
    </>}
    <div className="related-pagination">
      <button type="button" disabled={busy || navigation.previous.length===0} onClick={()=>navigate(navigation.previous[navigation.previous.length-1],navigation.previous.slice(0,-1))}>Anterior</button>
      <button type="button" disabled={busy || !page || page.next_offset===null} onClick={()=>page?.next_offset!=null && navigate(page.next_offset,[...navigation.previous,page.offset])}>Siguiente</button>
    </div>
  </section>;
}
