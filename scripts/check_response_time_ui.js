// playwright-cli run-code --filename=scripts/check_response_time_ui.js
async (page) => {
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  await page.route('**/api/config', route => route.fulfill({json:{data_mode:'demo'}}));
  await page.route('**/api/sessions', route => route.fulfill({json:{sessions:[]}}));
  let fail = false;
  await page.route('**/api/chat/stream', async route => {
    await new Promise(resolve => setTimeout(resolve, 250));
    await route.fulfill(fail
      ? {status:500,body:'Unavailable'}
      : {contentType:'text/event-stream',body:'event: completed\ndata: {"answer":"La oficina se encuentra en La Paz.","status":"answer"}\n\n'});
  });
  await page.route('**/api/auth/**', route => {
    const path=new URL(route.request().url()).pathname;
    return route.fulfill({status:path==='/api/auth/me'?401:200,json:path==='/api/auth/me'?{error:{message:'Sin sesión'}}:path==='/api/auth/logout'?{logged_out:true}:{user:{user_id:'ui-test-user',username:'ui-test-account',display_name:'Cuenta de prueba'}}});
  });
  await page.goto('http://127.0.0.1:5173/');
  await page.getByLabel('Usuario', {exact:true}).fill('test-only');
  await page.getByLabel('Contraseña',{exact:true}).fill(await page.evaluate(()=>crypto.randomUUID()));
  await page.getByRole('button', {name:'Iniciar sesión'}).click();
  await page.getByRole('button', {name:/Oficinas y sucursales/}).click();
  const timing = page.locator('.response-time').first();
  await timing.waitFor();
  check(/\d+[,.]\d s/.test(await timing.innerText()), 'Missing seconds');
  check(await timing.evaluate(el => parseFloat(el.getAttribute('aria-label').split(': ')[1]) >= 0.2), 'Response duration was not measured');
  check(await page.locator('.message.user .response-time').count() === 0, 'User messages have a response duration');
  for (const theme of ['light','dark']) {
    await page.evaluate(value => document.documentElement.dataset.theme = value, theme);
    for (const width of [320,768,1440]) {
      await page.setViewportSize({width,height:900});
      check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Overflow at ${width}px`);
      check(await timing.evaluate(el => {
        const label = el.getBoundingClientRect();
        const author = el.parentElement.querySelector('.message-author').getBoundingClientRect();
        return label.right <= author.left && getComputedStyle(el).fontSize === '10px';
      }), `Timing must be small and to the left at ${width}px (${theme})`);
    }
  }
  fail = true;
  await page.getByRole('button', {name:'Nueva conversación'}).click();
  await page.getByRole('button', {name:/Oficinas y sucursales/}).click();
  await page.locator('.response-time').waitFor();
  check(await page.locator('.message.assistant .evidence').innerText() === 'Solicitud interrumpida', 'Failed request did not finish');
  await page.unrouteAll({behavior:'wait'});
}
