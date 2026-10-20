// Run with an open Playwright CLI browser:
// playwright-cli run-code --filename=scripts/check_frontend_ui.js
async (page) => {
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  await page.route('**/api/auth/**', route => {
    const path=new URL(route.request().url()).pathname;
    return route.fulfill({status:path==='/api/auth/me'?401:200,json:path==='/api/auth/me'?{error:{message:'Sin sesión'}}:path==='/api/auth/logout'?{logged_out:true}:{user:{user_id:'ui-test-user',username:'ui-test-account',display_name:'Cuenta de prueba'}}});
  });
  await page.goto('http://127.0.0.1:5173/');
  await page.getByRole('heading', {name:'Hola, bienvenido.'}).waitFor();
  const original = await page.evaluate(() => document.documentElement.dataset.theme);
  const next = original === 'dark' ? 'light' : 'dark';
  await page.getByRole('button', {name:original === 'dark' ? 'Activar modo claro' : 'Activar modo oscuro'}).click();
  check(await page.evaluate(() => document.documentElement.dataset.theme) === next, 'Theme toggle did not apply');
  await page.reload();
  await page.getByRole('heading', {name:'Hola, bienvenido.'}).waitFor();
  check(await page.evaluate(() => document.documentElement.dataset.theme) === next, 'Theme did not survive reload');
  check(await page.getByRole('button', {name:'Iniciar sesión'}).isDisabled(), 'Empty credentials must not submit');
  for (const width of [320,390,768,1440]) {
    await page.setViewportSize({width,height:900});
    check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Horizontal overflow at ${width}px`);
    check(await page.getByLabel('Usuario', {exact:true}).isVisible(), `Username field hidden at ${width}px`);
    check(await page.getByLabel('Contraseña', {exact:true}).isVisible(), `Password field hidden at ${width}px`);
  }
  await page.emulateMedia({reducedMotion:'reduce'});
  check(await page.locator('.theme-toggle').evaluate(el => getComputedStyle(el).transitionDuration) === '0s', 'Reduced motion preference ignored');
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.getByRole('button', {name:next === 'dark' ? 'Activar modo claro' : 'Activar modo oscuro'}).click();
  check(await page.evaluate(() => document.documentElement.dataset.theme) === original, 'Original theme not restored');
}
