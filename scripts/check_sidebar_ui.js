// Requires an authenticated local chat in the open Playwright CLI browser.
// playwright-cli run-code --filename=scripts/check_sidebar_ui.js
async (page) => {
  const check = (condition, message) => {if (!condition) throw new Error(message);};
  await page.setViewportSize({width:1440,height:1000});
  const search = page.getByRole('searchbox', {name:'Buscar conversaciones'});
  const links = page.locator('.session');
  const count = await links.count();
  await search.fill('consulta-inexistente-9b6089');
  check(await links.count() === 0, 'Search did not filter history');
  check(await page.getByText('No encontramos conversaciones.', {exact:true}).isVisible(), 'Missing search empty state');
  await page.getByRole('button', {name:'Limpiar búsqueda'}).click();
  check(await links.count() === count, 'Clear did not restore history');
  if (count) {
    const title = await links.first().getAttribute('title');
    await search.fill(title.toLocaleUpperCase('es'));
    check(await links.count() > 0, 'Search must ignore case');
    await page.getByRole('button', {name:'Limpiar búsqueda'}).click();
  }
  await page.setViewportSize({width:390,height:844});
  await page.getByRole('button', {name:'Abrir historial'}).click();
  check(await search.isVisible(), 'Mobile history search hidden');
  await page.keyboard.press('Escape');
  check(await page.locator('.sidebar').evaluate(el => getComputedStyle(el).visibility === 'hidden'), 'Escape did not close history');
  check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Sidebar causes horizontal overflow');
  await page.setViewportSize({width:1440,height:1000});
}
