// keystone-html «stage» engine: 1920x1080 stage, click steps, presenter view (P), live product
// mounted in phones and laptops ([data-app]), and per-slide scenes (window.ESCENAS) that click
// inside the product and place callouts that read its live numbers.
// - Escala el escenario de 1920×1080 a la pantalla.
// - Avanza por pasos: cada clic revela [data-paso=n] y ejecuta el paso n de la escena de la lámina (escenas.js).
// - Monta la app real (../app) dentro de laptops y celulares ([data-app]) y pone rótulos que leen sus números.
// - Sincroniza la vista del presentador (tecla P) por BroadcastChannel.
// Teclas: → espacio PageDown clic = adelante · ← PageUp = atrás · P = presentador · N = número · Inicio / Fin.
(() => {
  const APP = document.body.dataset.app || '../app/index.html';
  // Modo informe (body.informe): todas las láminas quedan abiertas a la vez, con todos sus pasos, dentro de páginas para imprimir.
  const INFORME = document.body.classList.contains('informe');
  const laminas = [...document.querySelectorAll('section.lam')];
  const ids = laminas.map(l => l.id);
  const canal = new BroadcastChannel(document.body.dataset.channel || 'keystone-stage');
  let i = 0, k = 0, S = 1, ocupado = false, intervalos = [];
  const espera = ms => new Promise(r => setTimeout(r, ms));

  function ajustar() {
    if (INFORME) return;
    S = Math.min(innerWidth / 1920, innerHeight / 1080);
    document.body.style.transform = `translate(${(innerWidth - 1920 * S) / 2}px, ${(innerHeight - 1080 * S) / 2}px) scale(${S})`;
  }

  // ---------- Dispositivos
  function limpiarApp() {
    (document.body.dataset.reset || '').split(',').filter(Boolean).forEach(k => localStorage.removeItem(k));
  }

  function montar(lam) {
    const devs = [...lam.querySelectorAll('[data-app]')];
    if (!devs.length) return Promise.resolve({});
    limpiarApp();
    const apps = {};
    return Promise.all(devs.map(d => new Promise(ok => {
      d.querySelector('iframe')?.remove();
      const f = document.createElement('iframe');
      f.width = 1440; f.height = 900; f.title = 'product';
      f.setAttribute('tabindex', '-1');
      if (d.classList.contains('libre')) { f.width = 1920; f.height = 1080; }
      const caja = d.classList.contains('laptop') ? d.querySelector('.vidrio') : d;
      if (d.classList.contains('laptop')) {
        const w = caja.clientWidth, s = w / 1440;
        caja.style.height = `${900 * s}px`;
        f.style.transform = `scale(${s})`;
        f.dataset.s = s;
      }
      caja.classList.add('cargando');
      f.onload = async () => {
        const win = f.contentWindow;
        for (let n = 0; n < 60 && !win.__app; n++) await espera(50);
        const libre = d.classList.contains('libre');
        win.addEventListener('keydown', e => {
          const nav = libre ? ['PageDown', 'PageUp'] : ['ArrowRight', 'ArrowLeft', ' ', 'PageDown', 'PageUp', 'Enter'];
          if (nav.includes(e.key) && !(e.target.matches?.('input, textarea') && !e.key.startsWith('Page'))) { e.preventDefault(); teclas(e.key); }
        });
        if (d.classList.contains('tel')) await ajustarTel(d, f);
        caja.classList.remove('cargando');
        apps[d.dataset.app] = { win, doc: win.document, f, dev: d };
        ok();
      };
      f.src = `${APP}${d.dataset.ruta || '#/'}`;
      caja.appendChild(f);
    }))).then(() => apps);
  }

  // El celular usa el marco que dibuja la propia app (.celular) y recorta el resto de la página.
  async function ajustarTel(d, f) {
    const doc = f.contentWindow.document;
    for (let n = 0; n < 40 && !doc.querySelector('.celular'); n++) await espera(50);
    const c = doc.querySelector('.celular');
    if (!c) return;
    const r = c.getBoundingClientRect();
    const alto = d.clientHeight || 640, s = alto / r.height;
    d.style.width = `${r.width * s}px`;
    f.style.transform = `scale(${s})`;
    f.style.left = `${-r.left * s}px`;
    f.style.top = `${-r.top * s}px`;
    f.dataset.s = s;
  }

  // ---------- Rótulos: aro en el elemento de la app + caja con el dato, en coordenadas de la lámina
  function capa(lam) {
    let c = lam.querySelector('.capa-rotulos');
    if (!c) { c = document.createElement('div'); c.className = 'capa-rotulos'; lam.appendChild(c); }
    return c;
  }
  function rectEnLamina(lam, app, sel) {
    const el = typeof sel === 'string' ? app.doc.querySelector(sel) : sel;
    if (!el) return null;
    const fr = app.f.getBoundingClientRect(), lr = lam.getBoundingClientRect();
    const s = +app.f.dataset.s || 1, r = el.getBoundingClientRect();
    return { x: (fr.left - lr.left) / S + r.left * s, y: (fr.top - lr.top) / S + r.top * s, w: r.width * s, h: r.height * s, el };
  }
  function rotulo(lam, app, sel, { texto = '', dato = null, lado = 'izq', dx = 0, dy = 0, ancho = 400, vivo = null } = {}) {
    const r = rectEnLamina(lam, app, sel);
    if (!r) return;
    const c = capa(lam);
    const aro = document.createElement('div');
    aro.className = 'aro';
    Object.assign(aro.style, { left: `${r.x - 8}px`, top: `${r.y - 8}px`, width: `${r.w + 16}px`, height: `${r.h + 16}px` });
    const caja = document.createElement('div');
    caja.className = 'rotulo';
    caja.style.maxWidth = `${ancho}px`;
    const actual = () => (typeof sel === 'string' && app.doc.querySelector(sel)) || r.el;
    let ultimo = '';
    const pinta = () => {
      const html = `${dato !== null ? `<span class="dato">${typeof dato === 'function' ? dato(actual()) : dato}</span>` : ''}${texto}`;
      if (html !== ultimo) { ultimo = html; caja.innerHTML = html; }  // solo si cambió el número: sin parpadeo
    };
    pinta();
    c.append(aro, caja);
    const cw = Math.min(ancho, caja.offsetWidth || ancho), ch = caja.offsetHeight || 90;
    let x, y;
    if (lado === 'izq') { x = r.x - cw - 60; y = r.y + r.h / 2 - ch / 2; }
    if (lado === 'der') { x = r.x + r.w + 60; y = r.y + r.h / 2 - ch / 2; }
    if (lado === 'arr') { x = r.x + r.w / 2 - cw / 2; y = r.y - ch - 50; }
    if (lado === 'aba') { x = r.x + r.w / 2 - cw / 2; y = r.y + r.h + 50; }
    x = Math.max(30, Math.min(1890 - cw, x + dx)); y = Math.max(300, Math.min(1000 - ch, y + dy));
    Object.assign(caja.style, { left: `${x}px`, top: `${y}px` });
    // Línea del borde de la caja al aro
    const ax = Math.max(r.x - 8, Math.min(r.x + r.w + 8, x + cw / 2)), ay = Math.max(r.y - 8, Math.min(r.y + r.h + 8, y + ch / 2));
    const bx = Math.max(x, Math.min(x + cw, ax)), by = Math.max(y, Math.min(y + ch, ay));
    const lin = document.createElement('div');
    lin.className = 'linea-r';
    const len = Math.hypot(ax - bx, ay - by);
    Object.assign(lin.style, { left: `${bx}px`, top: `${by}px`, width: `${len}px`, transform: `rotate(${Math.atan2(ay - by, ax - bx)}rad)` });
    c.insertBefore(lin, caja);
    requestAnimationFrame(() => requestAnimationFrame(() => [aro, caja, lin].forEach(e => e.classList.add('ver'))));
    if (vivo) intervalos.push(setInterval(pinta, vivo));
  }
  function quitarRotulos(lam) { lam.querySelector('.capa-rotulos')?.replaceChildren(); }

  // Clic visible dentro de la app: un aro breve y el clic real.
  async function clic(lam, app, sel, pausa = 450) {
    const el = app.doc.querySelector(sel);
    if (!el) return false;
    const r = rectEnLamina(lam, app, el);
    const p = document.createElement('div');
    p.className = 'aro ver';
    Object.assign(p.style, { left: `${r.x - 6}px`, top: `${r.y - 6}px`, width: `${r.w + 12}px`, height: `${r.h + 12}px` });
    capa(lam).appendChild(p);
    await espera(pausa);
    el.click();
    setTimeout(() => p.remove(), 250);
    await espera(250);
    return true;
  }
  async function escribir(app, sel, texto, ms = 45) {
    const el = app.doc.querySelector(sel);
    if (!el) return;
    el.focus();
    for (const ch of texto) { el.value += ch; await espera(ms); }
  }

  const H = { espera, rotulo, quitarRotulos, clic, escribir, rectEnLamina };

  // ---------- Navegación
  const pasosDe = lam => {
    const v = [...lam.querySelectorAll('[data-paso]')].map(e => +e.dataset.paso);
    const esc = window.ESCENAS?.[lam.dataset.escena];
    return Math.max(v.length ? Math.max(...v) : 0, esc?.pasos?.length || 0);
  };

  async function mostrar(n, todos = false) {
    if (ocupado) return;
    ocupado = true;
    intervalos.forEach(clearInterval); intervalos = [];
    const antes = laminas[i];
    i = Math.max(0, Math.min(ids.length - 1, n));
    const lam = laminas[i];
    k = 0;
    lam.querySelectorAll('[data-paso]').forEach(e => e.classList.remove('ver'));
    quitarRotulos(lam);
    lam.classList.remove('ver');
    // Reinicia las animaciones de entrada
    lam.classList.remove('activa'); void lam.offsetWidth; lam.classList.add('activa');
    if (antes && antes !== lam && !INFORME) setTimeout(() => { antes.classList.remove('activa'); antes.querySelectorAll('[data-app] iframe').forEach(f => f.remove()); }, 450);
    lam.querySelectorAll('.num-l').forEach(e => { e.textContent = `${i + 1} / ${ids.length}`; });
    if (!INFORME) history.replaceState(null, '', `#${i + 1}`);
    const esc = window.ESCENAS?.[lam.dataset.escena];
    lam._apps = await montar(lam);
    if (esc?.preparar) await esc.preparar(lam._apps, lam, H);
    esc?.entrar?.(lam, H);
    if (!lam.classList.contains('libre-lam')) { try { document.activeElement?.blur?.(); } catch (e) {} window.focus(); }
    setTimeout(() => lam.classList.add('ver'), 350);
    ocupado = false;
    emitir();
    if (todos) { const m = pasosDe(lam); for (let p = 0; p < m; p++) await adelante(true); }
  }

  async function adelante(interno = false) {
    if (ocupado && !interno) return;
    const lam = laminas[i];
    const m = pasosDe(lam);
    if (k < m) {
      ocupado = true;
      k++;
      lam.querySelectorAll(`[data-paso="${k}"]`).forEach(e => e.classList.add('ver'));
      const paso = window.ESCENAS?.[lam.dataset.escena]?.pasos?.[k - 1];
      if (paso) quitarRotulos(lam);  // un destacado a la vez: los rótulos no se acumulan ni se superponen
      try { if (paso) await paso(lam._apps || {}, lam, H); } catch (e) { console.warn('paso', lam.id, k, e); }
      if (!lam.classList.contains('libre-lam')) { try { document.activeElement?.blur?.(); } catch (e) {} window.focus(); }
      ocupado = false;
      emitir();
    } else if (i < ids.length - 1) await mostrar(i + 1);
  }
  function atras() { if (!ocupado && i > 0) mostrar(i - 1); }

  function emitir() {
    const l = laminas[i], sig = laminas[i + 1];
    canal.postMessage({ i, total: ids.length, id: l.id, paso: k, pasos: pasosDe(l), quien: l.dataset.quien, tiempo: l.dataset.tiempo, notas: l.dataset.notas,
      siguiente: sig ? { id: sig.id, quien: sig.dataset.quien } : null });
  }
  canal.onmessage = ({ data }) => {
    if (data.cmd === 'adelante') adelante();
    if (data.cmd === 'atras') atras();
    if (data.cmd === 'ir') mostrar(data.n);
    if (data.cmd === 'estado') emitir();
  };

  function teclas(key) {
    if (['ArrowRight', ' ', 'PageDown', 'Enter'].includes(key)) adelante();
    else if (['ArrowLeft', 'PageUp', 'Backspace'].includes(key)) atras();
    else if (key === 'Home') mostrar(0);
    else if (key === 'End') mostrar(ids.indexOf('cierre'));
    else if (key.toLowerCase() === 'p') open('presenter.html?channel=' + encodeURIComponent(document.body.dataset.channel || 'keystone-stage'), 'presentador', 'width=1200,height=800');
    else if (key.toLowerCase() === 'n') document.body.classList.toggle('con-num');
  }
  addEventListener('keydown', e => {
    if ([' ', 'ArrowRight', 'ArrowLeft', 'PageDown', 'PageUp', 'Backspace', 'Enter'].includes(e.key)) e.preventDefault();
    teclas(e.key);
  });
  // Clic avanza, salvo en la lámina de la app libre (ahí el clic es de la app).
  // Mientras corre el video de la demo, un clic no avanza: se pasa con el teclado o al terminar.
  addEventListener('click', e => { if (!laminas[i].classList.contains('libre-lam') && !(laminas[i].classList.contains('sonando') && !laminas[i].classList.contains('fin'))) adelante(); });
  addEventListener('resize', ajustar);

  window.__deck = { ids, total: ids.length, ir: (n, todos = true) => mostrar(n, todos), ocupado: () => ocupado };
  ajustar();
  const ini = parseInt(location.hash.slice(1), 10);
  if (INFORME) {
    (async () => {
      for (let n = 0; n < ids.length; n++) { await mostrar(n, true); await espera(250); }
      await espera(1500);
      document.body.classList.add('listo');
    })();
  } else mostrar(Number.isFinite(ini) ? ini - 1 : 0);
})();
