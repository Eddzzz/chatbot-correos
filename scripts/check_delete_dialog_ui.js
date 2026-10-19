async page => {
  const check=(ok,message)=>{if(!ok)throw Error(message)};
  const id='11111111-1111-1111-1111-111111111111';
  let deleted=0,fail=false,release;
  await page.unrouteAll({behavior:'wait'});
  await page.route('**/api/config',r=>r.fulfill({json:{data_mode:'demo'}}));
  await page.route('**/api/sessions',r=>r.fulfill({json:{sessions:[{session_id:id,title:'Mi conversación postal'}]}}));
  await page.route('**/api/sessions/*',async r=>{
    if(r.request().method()==='DELETE') {
      deleted++;
      if(fail)return r.fulfill({status:500,json:{error:'test'}});
      await new Promise(resolve=>release=resolve);
      return r.fulfill({json:{deleted:true}});
    }
    return r.fulfill({json:{messages:[{role:'user',content:'Pregunta de prueba'}]}});
  });
  await page.goto(`http://127.0.0.1:5173/c/${id}`);
  // Any use of the browser confirmation is a regression.
  await page.evaluate(()=>window.confirm=()=>{throw Error('Browser confirmation used')});
  await page.getByLabel('Clave de acceso',{exact:true}).fill('ui-check');
  await page.getByRole('button',{name:'Iniciar conversación'}).click();
  const trigger=page.getByRole('button',{name:'Eliminar chat: Mi conversación postal',exact:true});
  await trigger.click();
  const dialog=page.getByRole('dialog',{name:'¿Eliminar este chat?'});
  check(await dialog.count()===1,'Custom confirmation dialog missing');
  check(await dialog.getByRole('button',{name:'Cancelar',exact:true}).evaluate(el=>el===document.activeElement),'Cancel lacks initial focus');
  await page.keyboard.press('Escape');
  await dialog.waitFor({state:'detached'});
  check(deleted===0,'Escape sent DELETE');
  check(await trigger.evaluate(el=>el===document.activeElement),'Focus did not return to trigger');
  await trigger.click();
  await dialog.getByRole('button',{name:'Cancelar',exact:true}).click();
  check(deleted===0,'Cancel sent DELETE');
  for(const theme of ['light','dark']) {
    await page.evaluate(t=>document.documentElement.dataset.theme=t,theme);
    for(const width of [390,1440]) {
      await page.setViewportSize({width,height:900});
      if(width===390)await page.getByRole('button',{name:'Abrir historial',exact:true}).click();
      await trigger.click();
      check(await dialog.evaluate(el=>{const b=el.getBoundingClientRect();return b.left>=0&&b.right<=innerWidth&&b.top>=0&&b.bottom<=innerHeight}),'Dialog outside viewport');
      await page.keyboard.press('Tab');
      check(await dialog.evaluate(el=>el.contains(document.activeElement)),'Focus escaped modal');
      await page.screenshot({path:`output/playwright/delete-dialog-${theme}-${width}.png`});
      await dialog.getByRole('button',{name:'Cancelar',exact:true}).click();
      if(width===390)await page.getByRole('button',{name:'Cerrar historial',exact:true}).last().click();
    }
  }
  fail=true;
  await trigger.click();
  await dialog.getByRole('button',{name:'Eliminar chat',exact:true}).click();
  await dialog.getByRole('alert').waitFor();
  check(await trigger.count()===1,'Failure removed chat');
  fail=false;
  await dialog.getByRole('button',{name:'Eliminar chat',exact:true}).click();
  await dialog.getByRole('button',{name:'Eliminando…',exact:true}).waitFor();
  check(await dialog.getByRole('button',{name:'Cancelar',exact:true}).isDisabled(),'Cancel enabled during deletion');
  await page.keyboard.press('Escape');
  check(await dialog.isVisible(),'Escape closed pending dialog');
  check(typeof release==='function','Delete request not started');
  release();
  await dialog.waitFor({state:'detached'});
  await page.waitForURL('http://127.0.0.1:5173/');
  check(await trigger.count()===0,'Deleted chat remains');
  return 'PASS: custom modal, cancel, Escape, focus, themes, mobile, error retry, pending state and successful deletion.';
}
