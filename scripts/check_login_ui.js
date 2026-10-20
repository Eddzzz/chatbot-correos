// Requires local services and .runtime/login-check.json containing two distinct
// provisioned accounts: {first:{username,password},second:{username,password}}.
// Run from the repository root in an isolated Playwright CLI session.
async (page) => {
  const check = (ok, message) => { if (!ok) throw new Error(message); };
  const origin = 'http://127.0.0.1:5173';
  await page.context().clearCookies();
  await page.goto(origin);
  // The CLI sandbox has no filesystem imports. Read the private fixture through
  // a temporary file input, keeping credentials out of command text and output.
  await page.evaluate(()=>{const input=document.createElement('input');input.type='file';input.id='verification-credentials';input.hidden=true;document.body.append(input);});
  const fixture=page.locator('#verification-credentials');
  await fixture.setInputFiles('.runtime/login-check.json');
  const accounts=await fixture.evaluate(async input=>JSON.parse(await input.files[0].text()));
  await fixture.evaluate(input=>input.remove());
  const headers = {Origin: origin};
  const login = async account => {
    await page.getByLabel('Usuario', {exact:true}).fill(account.username);
    await page.getByLabel('Contraseña', {exact:true}).fill(account.password);
    await page.getByRole('button', {name:'Iniciar sesión',exact:true}).click();
    await page.getByRole('heading', {name:'Asistente postal'}).waitFor();
  };
  const logout = async () => {
    const response = page.waitForResponse(result=>result.url()===origin+'/api/auth/logout' && result.request().method()==='POST');
    await page.getByRole('button', {name:'Cerrar sesión'}).click();
    check((await response).ok(), 'Logout request failed');
    await page.getByRole('button', {name:'Iniciar sesión',exact:true}).waitFor();
  };
  await page.setViewportSize({width:1440,height:1000});
  await login(accounts.first);
  await page.getByLabel('Tu consulta', {exact:true}).fill('hola');
  await page.getByRole('button', {name:'Enviar consulta'}).click();
  await page.locator('.message.assistant .evidence').waitFor();
  const chatPath = new URL(page.url()).pathname;
  const chatId = chatPath.split('/').pop();
  check(chatPath.startsWith('/c/'), 'Missing saved conversation URL');
  const saved = page.locator(`.session[href="${chatPath}"]`);
  await saved.waitFor();
  await page.reload();
  await page.locator('.message.user').filter({hasText:'hola'}).waitFor();
  check((await (await page.request.get(origin+'/api/auth/me')).json()).user.username === accounts.first.username, 'Session did not survive reload');
  const cookies = await page.context().cookies(origin+'/api/auth/me');
  const cookie = cookies.find(item=>item.name==='chatbot_session');
  check(cookie?.httpOnly && cookie.sameSite==='Strict', 'Missing protected session cookie');
  check(await page.evaluate(()=>!localStorage.getItem('chatbot_session') && !sessionStorage.getItem('chatbot_session')), 'Session exposed in browser storage');
  await logout();
  check(new URL(page.url()).pathname==='/', 'Logout retained private conversation URL');
  check((await page.request.get(origin+'/api/sessions')).status()===401, 'Logout did not revoke access');
  await login(accounts.second);
  const otherHistory = await (await page.request.get(origin+'/api/sessions')).json();
  check(!otherHistory.sessions.some(item=>item.session_id===chatId), 'Other account lists private chat');
  const url = origin+'/api/sessions/'+chatId;
  check((await page.request.get(url)).status()===404, 'Other account reads private chat');
  check((await page.request.delete(url,{headers})).status()===404, 'Other account deletes private chat');
  check((await page.request.post(origin+'/api/chat',{headers,data:{message:'otro',session_id:chatId,edit_message_index:0}})).status()===404, 'Other account edits private chat');
  await page.goto(origin+chatPath);
  await page.getByRole('alert').waitFor();
  check(await page.locator('.message.user').count()===0, 'Deep link exposed private messages');
  await logout();
  await login(accounts.first);
  await page.locator(`.session[href="${chatPath}"]`).click();
  await page.locator('.message.user').filter({hasText:'hola'}).waitFor();
  check((await page.request.delete(url,{headers})).ok(), 'Could not clean up verification chat');
  await logout();
  await page.screenshot({path:'output/playwright/login-multiusuario.png'});
  return 'Login, cookie HttpOnly, reload, logout, account switching, private history/deep links/edit/delete and cleanup passed.';
}
