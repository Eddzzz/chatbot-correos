// playwright-cli run-code --filename=scripts/check_personnel_ui.js
async (page) => {
  const check=(value,message)=>{if(!value)throw new Error(message);};
  const id='11111111-1111-4111-8111-111111111111';
  await page.unrouteAll({behavior:'wait'});
  await page.route('http://127.0.0.1:5173/api/**',route=>{
    const path=new URL(route.request().url()).pathname;
    const body=path==='/api/config'?{data_mode:'demo'}:path==='/api/sessions'?{sessions:[]}:{messages:[
      {role:'user',content:'dame que personal hay en la sucursal de beni en tablas'},
      {role:'assistant',status:'answer',content:'Personal asignado según el respaldo.',rows:[{nombre:'Persona de prueba',correo_electronico:'persona@example.test',documento_identidad:'123456',ciudad:'Trinidad',sucursal:'TRINIDAD',departamento:'BENI'}]},
    ]};
    return route.fulfill({json:body});
  });
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(`http://127.0.0.1:5173/c/${id}`);
  await page.getByLabel('Clave de acceso',{exact:true}).fill('personnel-test-only');
  await page.getByRole('button',{name:'Iniciar conversación'}).click();
  await page.getByRole('table').waitFor();
  check(await page.getByRole('columnheader',{name:'Correo electrónico',exact:true}).count()===1,'Email label missing');
  check(await page.getByRole('columnheader',{name:'Documento de identidad',exact:true}).count()===1,'Document label missing');
  check(await page.getByRole('cell',{name:'Persona de prueba',exact:true}).count()===1,'Personnel missing');
  check(await page.locator('.full-details').count()===0,'Returned an office fiche instead of personnel table');
  for(const width of [320,768,1440]){
    await page.setViewportSize({width,height:900});
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`Page overflow at ${width}px`);
  }
  check(errors.length===0,'Browser errors');
  console.log('PASS: readable personnel table, no nested fiche, 320/768/1440px.');
}
