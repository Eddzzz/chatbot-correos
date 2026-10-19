import {categoryName} from './relationLanguage.ts';

type Fields = Record<string, unknown>;
export type DetailSection = {title:string;context:string;fields:[string,unknown][];limited?:boolean};
const labels:Record<string,string> = {
  municipio:'Municipio',municipality:'Municipio',departamento:'Departamento',department:'Departamento',
  telefono:'Teléfono',phone:'Teléfono institucional',created_at:'Fecha de registro',registered_at:'Fecha de registro',updated_at:'Última actualización',
  deleted_at:'Fecha de baja',name:'Nombre',nombre:'Nombre',email:'Correo electrónico',ci:'Documento de identidad',
  puntoVenta:'Punto de venta',codigoSucursal:'Código de sucursal',codigo_sucursal:'Código de sucursal',
  tracking_code:'Código de seguimiento',codigo:'Código de seguimiento',source:'Familia postal',status:'Estado',
  origin:'Origen',destination:'Destino',nombre_estado:'Estado del envío',ciudad:'Ciudad',
  nombre_r:'Nombre del remitente',telefono_r:'Teléfono del remitente',direccion_r:'Dirección del remitente',
  nombre_d:'Nombre del destinatario',telefono_d:'Teléfono del destinatario',direccion_d:'Dirección del destinatario',
  nombre_remitente:'Nombre del remitente',nombre_destinatario:'Nombre del destinatario',telefono_remitente:'Teléfono del remitente',telefono_destinatario:'Teléfono del destinatario',
};
const metadata = new Set(['tabla','campos','relaciones','omitidos','campos_excluidos','tablas_asociadas','limite','truncado','record_key','relation_kind','path_info','password','remember_token','email_verified_at']);
export function isInternalField(key:string) {
  return metadata.has(key) || /^(id$|id_|fk_)|_id$/i.test(key) || /(?:Id|ID)$/.test(key);
}
export function fieldLabel(key:string) {
  const name=key.replace(/([a-z])([A-Z])/g,'$1 $2').replaceAll('_',' ');
  return labels[key] || name.charAt(0).toLocaleUpperCase('es')+name.slice(1);
}
function object(value:unknown):value is Fields {return value!==null && typeof value==='object' && !Array.isArray(value);}
function hasValue(value:unknown):boolean {
  if (value==null || value==='') return false;
  if (Array.isArray(value)) return value.some(hasValue);
  if (object(value)) {
    if (object(value.campos)) return hasValue(value.campos) || hasValue(value.relaciones);
    if (Array.isArray(value.registros)) return hasValue(value.registros) || value.truncado===true;
    return Object.entries(value).some(([key,item])=>!isInternalField(key) && hasValue(item));
  }
  return true;
}
export function displayValue(key:string,value:unknown):string {
  if (typeof value==='boolean') return value ? 'Sí' : 'No';
  if (Array.isArray(value)) return value.map(item=>displayValue(key,item)).join(', ');
  const text=String(value);
  // A timestamp without an offset is the recorded local time, not a UTC instant.
  const local=/^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?)?$/.exec(text);
  if (local) return `${local[3]}/${local[2]}/${local[1]}${local[4] ? `, ${local[4]}:${local[5]}` : ''}`;
  if (/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(text)) {
    const date=new Date(text);
    if (!Number.isNaN(date.getTime())) return date.toLocaleString('es-BO',{timeZone:'America/La_Paz',dateStyle:'short',timeStyle:'short'});
  }
  return text;
}
function relationTitle(key:string) {
  if (key==='usuarios' || key==='usuarios_asignados') return 'Personal asignado';
  const name=key.replace(/^fk_|^id_|_id$/g,'');
  return categoryName(name).replace(/^./,letter=>letter.toLocaleUpperCase('es'));
}

// Flatten the transport wrappers into sibling sections; no recursive UI or internal IDs.
export function detailSections(value:unknown,heading='Datos principales'):DetailSection[] {
  const sections:DetailSection[]=[];
  function visit(item:unknown,title:string,context='') {
    if (Array.isArray(item)) {
      item.forEach((record,index)=>visit(record,item.length>1 ? `${title} · ${index+1}` : title,context));
      return;
    }
    if (!object(item)) {
      if (hasValue(item)) sections.push({title,context,fields:[['Información',item]]});
      return;
    }
    if (Array.isArray(item.registros)) {
      const start=sections.length;
      visit(item.registros,title,context);
      if (item.truncado===true) {
        if (sections.length===start) sections.push({title,context,fields:[],limited:true});
        else sections[start].limited=true;
      }
      return;
    }
    const fields=object(item.campos) ? item.campos : item;
    const visible=Object.entries(fields).filter(([key,field])=>!isInternalField(key) && hasValue(field));
    const scalar=visible.filter(([,field])=>!object(field) && !(Array.isArray(field) && field.some(object)));
    const name=fields.name || fields.nombre;
    const office=item.tabla==='sucursales' && (fields.municipio || fields.municipality);
    const recordTitle=office ? `Sucursal · ${office}` : typeof name==='string' && name ? name : title;
    if (scalar.length) sections.push({title:recordTitle,context:recordTitle!==title ? [title,context].filter(Boolean).join(' · ') : context,fields:scalar.map(([key,field])=>[item.tabla==='eventos_auditoria' && key==='codigo' ? 'Motivo' : fieldLabel(key),field])});
    for (const [key,field] of visible) {
      if (object(field) || (Array.isArray(field) && field.some(object))) visit(field,relationTitle(key),recordTitle);
    }
    if (object(item.relaciones)) {
      for (const [key,relation] of Object.entries(item.relaciones)) {
        const relatedTable=object(relation) && typeof relation.tabla==='string' ? categoryName(relation.tabla) : relationTitle(key);
        visit(relation,relatedTable,recordTitle);
      }
    }
    // Event records may carry resolved user/event objects beside campos.
    if (object(item.campos)) {
      for (const [key,related] of Object.entries(item)) {
        if (!isInternalField(key) && object(related)) visit(related,relationTitle(key),recordTitle);
      }
    }
  }
  visit(value,heading);
  return sections;
}
