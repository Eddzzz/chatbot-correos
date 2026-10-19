import {test} from 'node:test';
import assert from 'node:assert/strict';
import {detailSections,displayValue,isInternalField} from './detailPresentation.ts';
import {categoryName} from './relationLanguage.ts';

test('audit events show their recorded reason separately from the event type catalog',()=>{
  assert.equal(categoryName('auditoria'),'Tipos de auditoría');
  assert.equal(categoryName('eventos_auditoria'),'Auditorías');
  const sections=detailSections({tabla:'eventos_auditoria',campos:{id:1,codigo:'Entro a pestana MIS VENTAS INDEX',auditoria_id:4,user_id:40,created_at:'2026-07-22T16:12:14'}});
  assert.ok(sections[0].fields.some(([label,value])=>label==='Motivo' && value==='Entro a pestana MIS VENTAS INDEX'));
  assert.ok(!sections[0].fields.some(([label])=>label==='Código de seguimiento'));
  assert.ok(detailSections({tabla:'paquetes_ems',campos:{codigo:'TEST123'}})[0].fields.some(([label])=>label==='Código de seguimiento'));
});

test('flat sections keep useful fields and resolved relations without IDs or empty collections',()=>{
  const value={tabla:'sucursales',campos:{id:1,municipio:'LA PAZ',puntoVenta:0,activo:false},omitidos:['password'],relaciones:{
    usuarios:{limite:50,truncado:true,registros:[{tabla:'users',campos:{id:5,sucursal_id:1,name:'Persona de prueba'},relaciones:{empresa_id:{tabla:'empresa',campos:{id:9,nombre:'Empresa de prueba'}}}}]},
    vacia:{registros:[],limite:50,truncado:false},nula:null,
  }};
  const sections=detailSections(value);
  assert.equal(sections.length,3);
  assert.equal(sections[0].title,'Sucursal · LA PAZ');
  assert.deepEqual(sections[0].fields,[['Municipio','LA PAZ'],['Punto de venta',0],['Activo',false]]);
  assert.equal(sections[1].title,'Persona de prueba');
  assert.equal(sections[1].limited,true);
  assert.equal(sections[2].title,'Empresa de prueba');
  assert.equal(sections[2].context,'Empresas · Persona de prueba');
  assert.deepEqual(detailSections({tabla:'users',campos:{id:1},omitidos:[],relaciones:{}}),[]);
  assert.equal(detailSections({registros:[],truncado:true})[0].limited,true);
  assert.equal(isInternalField('id_estados'),true);
  assert.equal(isInternalField('fk_estado'),true);
  assert.equal(isInternalField('officeId'),true);
  assert.equal(isInternalField('valid'),false);
  assert.equal(isInternalField('tracking_code'),false);
});

test('dates keep recorded local times and translate timestamps with explicit offsets',()=>{
  assert.equal(displayValue('Fecha','2026-06-25T15:50:17'),'25/06/2026, 15:50');
  assert.equal(displayValue('Fecha','2026-06-25'),'25/06/2026');
  assert.equal(displayValue('Fecha','2026-06-25T15:50:17Z'),new Date('2026-06-25T15:50:17Z').toLocaleString('es-BO',{timeZone:'America/La_Paz',dateStyle:'short',timeStyle:'short'}));
  assert.equal(displayValue('Activo',false),'No');
  assert.equal(displayValue('Total',0),'0');
});
