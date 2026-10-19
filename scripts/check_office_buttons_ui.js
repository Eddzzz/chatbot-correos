// playwright-cli run-code --filename=scripts/check_office_buttons_ui.js
async (page) => {
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const id = '12345678-1234-4234-8234-123456789abc';
  let fail = false;
  await page.unrouteAll({behavior:'wait'});
  await page.route('http://127.0.0.1:5173/api/**', async route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    if (path === '/api/offices/1/relations/eventos_auditoria') {
      return route.fulfill({json:{rows:[{record_key:'audit-test',record:{tabla:'eventos_auditoria',campos:{codigo:'Entro a pestana MIS VENTAS INDEX',created_at:'2026-07-22T16:12:14'}}}],offset:0,total_count:1,next_offset:null,source:'Prueba'}});
    }
    if (path === '/api/offices/1/relations/users') {
      await new Promise(resolve => setTimeout(resolve, 350));
      return route.fulfill(fail ? {status:500,body:'Test failure'} : {json:{rows:[{record_key:'test',record:{nombre:'Persona de prueba'}}],offset:Number(url.searchParams.get('offset')),total_count:11,next_offset:url.searchParams.get('offset') === '0' ? 10 : null,source:'Prueba'}});
    }
    const body = path === '/api/config' ? {data_mode:'demo'}
      : path === '/api/sessions' ? {sessions:[]}
      : path === `/api/sessions/${id}` ? {messages:[{role:'assistant',content:'Datos de la oficina.',rows:[{office_id:1,details:{nombre:'La Paz'}}]}]}
      : path === '/api/offices/1/relations' ? {rows:['users','auditoria','eventos_auditoria',...Array.from({length:25},(_,i)=>`category_${i}`)].map(table_name=>({table_name,total_count:11})),truncated:false} : {};
    return route.fulfill({json:body});
  });
  await page.goto(`http://127.0.0.1:5173/c/${id}`);
  await page.getByLabel('Clave de acceso',{exact:true}).fill('test-only');
  await page.getByRole('button',{name:'Iniciar conversación'}).click();
  const button = page.getByRole('button',{name:/^(Ver|Ocultar) personal y usuarios relacionados$/});
  const category = page.locator('.relation-story').filter({has:button});
  await button.click();
  await page.getByRole('status').filter({hasText:'Consultando personal'}).waitFor();
  check(await category.getByRole('status').count() === 1, 'Loading feedback is outside the clicked category');
  await page.locator('.related-page').waitFor();
  check(await category.locator('.related-page').count() === 1, 'Results are outside the clicked category');
  check((await category.innerText()).includes('Persona de prueba'), 'Record missing');
  check(await button.getAttribute('aria-expanded') === 'true', 'Open category is not expanded');
  await button.click();
  await page.locator('.relation-story > button:not(:disabled)').first().waitFor();
  check(await category.locator('.related-page').count() === 0, 'Second click did not collapse results');
  check(await button.getAttribute('aria-expanded') === 'false', 'Closed category is still expanded');
  await button.click();
  await category.locator('.related-page').waitFor();
  await category.getByRole('button',{name:'Siguiente',exact:true}).click();
  await category.getByText(/registros 11 al 11/).waitFor();
  check(await category.getByRole('button',{name:'Siguiente',exact:true}).isDisabled(), 'End of pagination not respected');
  await category.getByRole('button',{name:'Anterior',exact:true}).click();
  await category.getByText(/registros 1 al 1/).waitFor();
  fail = true;
  await button.click();
  await button.click();
  await category.getByRole('alert').waitFor();
  check((await category.getByRole('alert').innerText()).includes('500'), 'Request error missing beside button');
  await page.getByRole('button',{name:'Ver auditorías',exact:true}).click();
  const audit = page.getByRole('region',{name:'Registros de Auditorías',exact:true});
  await audit.waitFor();
  check((await audit.innerText()).includes('Motivo'), 'Audit reason label missing');
  check((await audit.innerText()).includes('Entro a pestana MIS VENTAS INDEX'), 'Recorded audit reason missing');
  check(!(await audit.innerText()).includes('Código de seguimiento'), 'Audit reason mislabeled as tracking code');
  check(await page.getByRole('button',{name:'Ver tipos de auditoría',exact:true}).count() === 1, 'Audit type catalog is not separate');
  for (const width of [320,768,1440]) {
    await page.setViewportSize({width,height:900});
    check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Overflow at ${width}px`);
  }
  await page.unrouteAll({behavior:'wait'});
}
