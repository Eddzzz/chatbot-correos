// playwright-cli --session mascot run-code --filename=scripts/check_mascot_ui.js
async (page) => {
  const check = (value, message) => { if (!value) throw new Error(message); };
  await page.route('**/api/config', route => route.fulfill({json:{data_mode:'demo'}}));
  await page.route('**/api/sessions', route => route.fulfill({json:{sessions:[]}}));
  let release;
  let fail = false;
  await page.route('**/api/chat/stream', async route => {
    await new Promise(resolve => { release = resolve; });
    await route.fulfill(fail ? {status:500,body:'Unavailable'} : {
      contentType:'text/event-stream',
      body:'event: completed\ndata: {"answer":"Tu consulta está lista.","status":"answer"}\n\n'
    }).catch(() => {});
  });
  await page.goto('http://127.0.0.1:5173/');
  await page.getByLabel('Clave de acceso', {exact:true}).fill('test-only');
  await page.getByRole('button', {name:'Iniciar conversación'}).click();
  const mascot = page.locator('.message.assistant .postal-thinking');
  check(await mascot.count() === 0, 'Loader visible while idle');
  check(await page.locator('.composer-dock,.postal-mascot').count() === 0, 'Corner mascot remains');
  const asset = await page.request.get('http://127.0.0.1:5173/cartero-thinking-v2.png');
  check(asset.ok() && asset.headers()['content-type'].includes('image'), 'Thinking sprite missing');
  for (const outcome of ['success','error','cancel']) {
    await page.getByLabel('Tu consulta', {exact:true}).fill('Consulta de prueba');
    await page.getByRole('button', {name:'Enviar consulta'}).click();
    await mascot.waitFor();
    const video = mascot.locator('video');
    await video.evaluate(el => el.readyState >= 2 ? Promise.resolve() : new Promise(resolve => el.addEventListener('loadeddata',resolve,{once:true})));
    check(await video.evaluate(el => el.loop && el.muted && el.playsInline && Math.abs(el.duration - 4) < .05), 'Video loop configuration is incorrect');
    await page.waitForFunction(() => document.querySelector('.thinking-frames video')?.currentTime > .1);
    if (outcome === 'success') {
      await video.evaluate(el => { el.currentTime = el.duration - .1; });
      await page.waitForFunction(() => document.querySelector('.thinking-frames video')?.currentTime < 1, null, {timeout:3000});
    }
    check((await mascot.innerText()).trim() === '', 'Loader must show only the character');
    for (const theme of ['light','dark']) {
      await page.evaluate(value => document.documentElement.dataset.theme = value, theme);
      for (const width of [320,390,768,1440]) {
        await page.setViewportSize({width,height:900});
        await page.locator('.conversation').evaluate(el => { el.scrollTop = el.scrollHeight; });
        check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Overflow at ${width}`);
        const clear = await mascot.evaluate(el => {
          const m = el.getBoundingClientRect();
          const input = document.querySelector('.composer').getBoundingClientRect();
          const frame = el.querySelector('.thinking-frames').getBoundingClientRect();
          const article = el.closest('.message').getBoundingClientRect();
          return m.right <= innerWidth && m.bottom <= input.top && frame.width >= 200 && m.top >= article.top && m.bottom <= article.bottom;
        });
        check(clear, `Mascot overlaps composer at ${width} (${theme})`);
      }
    }
    await page.emulateMedia({reducedMotion:'reduce'});
    await page.waitForFunction(() => document.querySelector('.thinking-frames video')?.paused);
    check(await video.evaluate(el => getComputedStyle(el).visibility === 'hidden'), 'Reduced motion ignored');
    await page.emulateMedia({reducedMotion:'no-preference'});
    await page.screenshot({path:`output/playwright/mascot-${outcome}.png`});
    if (outcome === 'cancel') await page.getByRole('button', {name:'Detener'}).click();
    else fail = outcome === 'error';
    // Wait until the intercepted request has installed its completion callback.
    await page.waitForTimeout(100);
    release();
    await mascot.waitFor({state:'hidden'});
    check(await page.locator('.postal-thinking').count() === 0, `Loader stuck after ${outcome}`);
  }
  await page.unrouteAll({behavior:'wait'});
  return '24 fps video loop: large frames, success, error, cancellation, both themes, 320–1440px and reduced motion passed.';
}
