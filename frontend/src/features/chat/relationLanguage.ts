const names: Record<string,string> = {
  alerta_empresa_destinatarios:'Destinatarios de alertas empresariales', alerta_empresa_lecturas:'Lecturas de alertas empresariales', alerta_empresa_usuarios:'Usuarios relacionados con alertas empresariales', alertas_empresa:'Alertas empresariales',
  auditoria:'Auditorías', bitacoras:'Bitácoras', cartero:'Registros de carteros', cartero_assignment_report_items:'Detalle de informes de asignación a carteros', cartero_assignment_reports:'Informes de asignación a carteros', cartero_guias:'Guías de carteros',
  cashier_flow_receivable_collections:'Cobros de cuentas por cobrar', cashier_flow_receivable_movements:'Movimientos de cuentas por cobrar', chasqui_location_points:'Puntos de ubicación Chasqui', clientes:'Clientes', conciliaciones_empresa:'Conciliaciones empresariales', destino:'Destinos', driver_incentive_reports:'Informes de incentivos a conductores', drivers:'Conductores', empresa:'Empresas', empresa_historiales:'Historial de empresas', estados:'Estados de los envíos',
  eventos:'Eventos', eventos_auditoria:'Historial de auditoría postal', eventos_certi:'Eventos de envíos certificados', eventos_contrato:'Eventos de envíos por contrato', eventos_despacho:'Eventos de despacho', eventos_ems:'Eventos de envíos EMS', eventos_ordi:'Eventos de envíos ordinarios', eventos_tiktoker:'Eventos del servicio Tiktoker',
  fuel_antifraud_cases:'Casos de revisión de combustible', fuel_invoice_details:'Detalle de facturas de combustible', fuel_invoices:'Facturas de combustible', fuel_logs:'Registros de combustible', gas_stations:'Estaciones de servicio', maintenance_alert_user_reads:'Lecturas de alertas de mantenimiento', maintenance_alerts:'Alertas de mantenimiento', maintenance_appointments:'Citas de mantenimiento', maintenance_logs:'Registros de mantenimiento', maintenance_types:'Tipos de mantenimiento', malencaminados:'Envíos mal encaminados', origen:'Orígenes',
  paquetes_certi:'Envíos certificados', paquetes_contrato:'Envíos por contrato', paquetes_ems:'Envíos EMS', paquetes_ems_formulario:'Formularios de envíos EMS', paquetes_ordi:'Envíos ordinarios', peso:'Pesos de referencia', preregistros:'Prerregistros', roles:'Roles del personal', servicio:'Servicios postales', servicio_extras:'Servicios adicionales', solicitud_clientes:'Solicitudes de clientes', sucursales:'Sucursales', tarifa_contrato:'Tarifas por contrato', tarifario:'Tarifas postales', tarifario_tiktoker:'Tarifas del servicio Tiktoker', users:'Personal y usuarios relacionados',
  vehicle_assignments:'Asignaciones de vehículos', vehicle_log:'Bitácora de vehículos', vehicle_log_investigation_tickets:'Casos de investigación de vehículos', vehicles:'Vehículos', ventanilla:'Ventanillas', workshop_catalogs:'Catálogos de talleres', workshop_part_changes:'Cambios de repuestos', workshops:'Talleres',
};
export function categoryName(name:string):string {return names[name] || name.replaceAll('_',' ');}
export function relationSentence(table:{table_name:string;total_count:number;descendant_count:number;lookup_count:number}):string {
  if(!table.total_count) return 'No hay información de esta categoría relacionada con la sucursal en el respaldo consultado.';
  const count=(n:number)=>n.toLocaleString('es-BO');
  const parts:string[]=[];
  if(table.descendant_count) {
    if(table.table_name==='sucursales') parts.push('Se incluye la ficha de la sucursal solicitada.');
    else if(table.table_name==='users') parts.push(`Hay ${count(table.descendant_count)} ${table.descendant_count===1?'usuario asignado':'usuarios asignados'} a esta sucursal.`);
    else parts.push(`Hay ${count(table.descendant_count)} ${table.descendant_count===1?'registro relacionado':'registros relacionados'} con el personal asignado a esta sucursal.`);
  }
  if(table.lookup_count) parts.push(`Se ${table.lookup_count===1?'incluye':'incluyen'} ${count(table.lookup_count)} ${table.lookup_count===1?'registro':'registros'} como información de referencia. Esto no significa que ${table.lookup_count===1?'pertenezca':'pertenezcan'} a esta sucursal.`);
  return parts.join(' ');
}
