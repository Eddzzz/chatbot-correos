// playwright-cli run-code --filename=scripts/check_auth_tabs_ui.js
async page => {
  const check=(ok,message)=>{if(!ok)throw Error(message);};
  await page.unrouteAll({behavior:'wait'});
  const context=page.context();
  let activeUser=null;
  const password=await page.evaluate(()=>crypto.randomUUID());
  const users={alice:{user_id:'alice-id',username:'alice',display_name:'Alicia'},bob:{user_id:'bob-id',username:'bob',display_name:'Roberto'}};
  const handler=route=>{
    const path=new URL(route.request().url()).pathname;
    if(path==='/api/auth/login'){activeUser=users[route.request().postDataJSON().username];return route.fulfill({json:{user:activeUser}});}
    if(path==='/api/auth/logout'){activeUser=null;return route.fulfill({json:{logged_out:true}});}
    if(path==='/api/auth/me')return route.fulfill({status:activeUser?200:401,json:activeUser?{user:activeUser}:{error:{message:'Sin sesión'}}});
    if(path==='/api/config')return route.fulfill({json:{data_mode:'demo'}});
    if(path==='/api/sessions')return route.fulfill({json:{sessions:activeUser?[{session_id:'11111111-1111-4111-8111-111111111111',title:`Historial de ${activeUser.username}`}]:[]}});
    return route.fulfill({json:{messages:[]}});
  };
  await context.route('http://127.0.0.1:5173/api/**',handler);
  const other=await context.newPage();
  const login=async(target,username)=>{
    await target.getByLabel('Usuario',{exact:true}).fill(username);
    await target.getByLabel('Contraseña',{exact:true}).fill(password);
    await target.getByRole('button',{name:'Iniciar sesión',exact:true}).click();
    await target.locator('.workspace').waitFor();
  };
  try {
    await page.setViewportSize({width:1440,height:1000});
    await page.goto('http://127.0.0.1:5173/');
    await login(page,'alice');
    await page.getByRole('link',{name:'Historial de alice',exact:true}).waitFor();
    await page.getByLabel('Buscar conversaciones').fill('búsqueda privada');
    await page.getByLabel('Tu consulta').fill('Borrador privado de Alicia');
    await other.goto('http://127.0.0.1:5173/');
    await other.getByRole('button',{name:'Cerrar sesión',exact:true}).click();
    await page.getByLabel('Usuario',{exact:true}).waitFor();
    check(new URL(page.url()).pathname==='/', 'Remote logout kept chat URL');
    await login(other,'bob');
    await page.getByRole('link',{name:'Historial de bob',exact:true}).waitFor();
    check(await page.locator('.local-note strong').innerText()==='Roberto','Remote login did not update displayed account');
    check(await page.getByLabel('Buscar conversaciones').inputValue()==='', 'Private search crossed accounts');
    check(await page.getByLabel('Tu consulta').inputValue()==='', 'Private draft crossed accounts');
    check(await page.getByRole('link',{name:'Historial de alice',exact:true}).count()===0,'Previous account history remains');
    await page.reload();
    await page.getByRole('link',{name:'Historial de bob',exact:true}).waitFor();
    // Simulate a cookie change while this tab is suspended and misses storage delivery.
    await other.evaluate(password=>fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:'alice',password})}),password);
    await page.evaluate(()=>window.dispatchEvent(new Event('focus')));
    await page.getByRole('link',{name:'Historial de alice',exact:true}).waitFor();
    check(await page.locator('.local-note strong').innerText()==='Alicia','Focus did not revalidate account');
    return 'PASS: cross-tab logout/login, isolated history/search/draft, reload restore, focus revalidation.';
  } finally {
    await other.close();
    await context.unroute('http://127.0.0.1:5173/api/**',handler);
  }
}
