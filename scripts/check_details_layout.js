// playwright-cli run-code --filename=scripts/check_details_layout.js
// Synthetic records only: checks flat, readable office and related record views.
async (page) => {
  const check = (value, message) => { if (!value) throw new Error(message); };
  const id = '11111111-1111-4111-8111-111111111111';
  const record = {tabla:'users',campos:{id:987654,sucursal_id:876543,name:'Persona de prueba con nombre completo',ci:'123456789',email:'persona.de.prueba@example.test'},relaciones:{empresa_id:{tabla:'empresa',campos:{id:765432,nombre:'Empresa de prueba'}}}};
  const message = {role:'assistant',content:'Ficha completa de prueba.',status:'answer',rows:[{office_id:1,details:{tabla:'sucursales',campos:{id:654321,municipio:'LA PAZ',telefono:'2152423',created_at:'2026-06-25T15:50:17',puntoVenta:0},omitidos:[],relaciones:{usuarios:{limite:50,truncado:true,registros:[record]},vehiculos:{limite:50,truncado:false,registros:[]}}}}]};
  await page.unroute('http://127.0.0.1:5173/api/**');
  await page.route('http://127.0.0.1:5173/api/**', route => {
    const path = new URL(route.request().url()).pathname;
    const body = path === '/api/config' ? {data_mode:'demo',inference_mode:'rules'}
      : path === '/api/sessions' ? {sessions:[]}
      : path === `/api/sessions/${id}` ? {messages:[message]}
      : path === '/api/offices/1/relations' ? {rows:[{table_name:'users',total_count:1},{table_name:'vehicles',total_count:0}],truncated:false}
      : path === '/api/offices/1/relations/users' ? {rows:[{record_key:'987654',record}],total_count:1,offset:0,next_offset:null,source:'Datos de prueba'} : {};
    return route.fulfill({json:body});
  });
  const errors=[];
  page.on('pageerror', error=>errors.push(error.message));
  await page.goto(`http://127.0.0.1:5173/c/${id}`);
  await page.getByLabel('Clave de acceso',{exact:true}).fill('synthetic-layout-test');
  await page.getByRole('button',{name:'Iniciar conversación'}).click();
  await page.locator('.full-details').waitFor();
  check(await page.locator('.full-details details').count()===0,'Fiche still uses nested disclosures');
  const text=await page.locator('.full-details').innerText();
  for (const hidden of ['987654','876543','765432','654321','0 elementos','Ver datos','Tabla de origen','Campos excluidos','Sin registros asociados']) check(!text.includes(hidden),`Technical or empty content visible: ${hidden}`);
  check(text.includes('25/06/2026') && !text.includes('2026-06-25T'),'Dates are not readable');
  check(text.includes('Persona de prueba') && text.includes('Empresa de prueba'),'Related data was lost');
  check(await page.locator('.detail-limit').count()>0,'Truncation warning was lost');
  check(await page.locator('.relation-story').count()===1,'Empty categories are visible');
  await page.getByRole('button',{name:'Ver personal y usuarios relacionados',exact:true}).click();
  await page.locator('.related-page').waitFor();
  check(await page.locator('.related-page details').count()===0,'Related page still uses disclosures');
  check(!(await page.locator('.related-page').innerText()).includes('987654'),'Internal record key visible');
  for (const theme of ['light','dark']) {
    if (await page.getByRole('button',{name:theme==='light'?'Activar modo claro':'Activar modo oscuro'}).count()) {
      await page.getByRole('button',{name:theme==='light'?'Activar modo claro':'Activar modo oscuro'}).click();
    }
    for (const width of [1440,768,600,390,320]) {
      await page.setViewportSize({width,height:1000});
      const metrics=await page.locator('.full-details').evaluate(card=>({
        overflow:document.documentElement.scrollWidth>innerWidth || card.scrollWidth>card.clientWidth,
        values:[...card.querySelectorAll('dd')].filter(dd=>dd.firstElementChild?.tagName==='SPAN' && dd.textContent.includes('Persona de prueba')).map(dd=>dd.getBoundingClientRect().width),
      }));
      check(!metrics.overflow,`Ficha overflows at ${width}px (${theme})`);
      check(metrics.values.length===2 && metrics.values.every(value=>value>=120),`Values squeezed at ${width}px (${theme}): ${metrics.values}`);
    }
  }
  check(errors.length===0,`Browser errors: ${errors.join(', ')}`);
  console.log('PASS: flat records, no internal IDs or empty categories, readable dates, related pages, 320/390/600/768/1440px, light/dark.');
}
