import {detailSections,displayValue} from './detailPresentation';

export function DetailView({value,title='Datos principales'}:{value:unknown;title?:string}) {
  const sections=detailSections(value,title);
  return <div className="detail-sections">{sections.map((section,index)=><section className="detail-section" key={index}>
    {section.context && <p className="detail-context">{section.context}</p>}
    <h4>{section.title}</h4>
    {section.limited && <p className="detail-limit" role="status">Se muestra una parte de los registros disponibles.</p>}
    {!!section.fields.length && <dl className="detail-fields">{section.fields.map(([label,field],fieldIndex)=><div key={fieldIndex}><dt>{label}</dt><dd><span>{displayValue(label,field)}</span></dd></div>)}</dl>}
  </section>)}</div>;
}
