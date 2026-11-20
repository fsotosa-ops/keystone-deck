// Demo v3: the pain of passing on what you know, then the answer. Every scene scales its timing to
// window.KS_DUR (seconds the line lasts, set by the video builder) so the picture follows the voice.
const IF = lam => [...lam.querySelectorAll('iframe[data-src]')]
const load = lam => IF(lam).forEach(f => { f.src = 'about:blank'; setTimeout(() => { f.src = f.dataset.src }, 30) })
const key = f => f.contentWindow?.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }))
const dur = d => window.KS_DUR || d
const at = (frac, fn, D) => setTimeout(fn, frac * D * 1000)
const zoom = (lam, s, x, y) => { const w = lam.querySelector('.win.z'); w.style.setProperty('--zx', x); w.style.setProperty('--zy', y); w.style.transform = `scale(${s})` }
const BUL = [[1046, 329], [1046, 433], [1046, 537]]
window.ESCENAS = {
  idea: { preparar(_, lam) { const D = dur(4), el = lam.querySelector('#idea'); el.classList.remove('go', 'lleg')
    el.style.setProperty('--d', (D * .62) + 's'); at(.1, () => el.classList.add('go'), D); at(.74, () => el.classList.add('lleg'), D) } },
  plantilla: { preparar(_, lam) { const D = dur(6), el = lam.querySelector('#pl'), nd = [...el.querySelectorAll('.nd')]
    el.classList.remove('s1', 's2'); nd.forEach(n => { if (!n.dataset.l) { n.dataset.l = n.style.left; n.dataset.t = n.style.top }
      n.classList.remove('in', 'out'); n.style.left = n.dataset.l; n.style.top = n.dataset.t })
    at(.38, () => { el.classList.add('s1'); nd.forEach((n, i) => { if (i < 3) { n.classList.add('in'); n.style.left = BUL[i][0] + 'px'; n.style.top = BUL[i][1] + 'px' } else n.classList.add('out') }) }, D)
    at(.7, () => el.classList.add('s2'), D) } },
  piezas: { preparar(_, lam) { const D = dur(7), el = lam.querySelector('#pz'); load(lam)
    const ws = [...el.querySelectorAll('.w')], ty = el.querySelector('.ty'), k = el.querySelector('.k'), se = el.querySelector('.sello')
    ws.forEach(w => w.classList.remove('on', 'mu')); se.classList.remove('on'); ty.textContent = ''; k.textContent = '1'
    at(.02, () => ws[0].classList.add('on'), D); at(.2, () => ws[1].classList.add('on'), D); at(.36, () => ws[2].classList.add('on'), D)
    const hex = '#1652E0'; let n = 1
    at(.42, () => { let c = 0; const t = setInterval(() => { ty.textContent = hex.slice(0, ++c); if (c >= hex.length) { clearInterval(t)
      const q = setInterval(() => { k.textContent = ++n; if (n >= 14) clearInterval(q) }, D * 1000 * .2 / 13) } }, D * 1000 * .1 / hex.length) }, D)
    at(.66, () => ws[1].classList.add('mu'), D); at(.74, () => se.classList.add('on'), D) } },
  sesion: { preparar(_, lam) { const D = dur(5), f = lam.querySelector('iframe.rp'), l = lam.querySelector('#lumo')
    f.dataset.src = f.dataset.base + '&dur=' + (D * .7).toFixed(2); load(lam); const rw = lam.querySelector('.rpw'); rw.style.opacity = 1; l.style.opacity = 0
    at(.74, () => { l.style.opacity = 1; rw.style.opacity = 0 }, D) } },
  resultado: { preparar(_, lam) { const D = dur(6.5); load(lam); const f = IF(lam)[0]; zoom(lam, 1, '50%', '50%')
    at(.14, () => key(f), D); at(.36, () => { key(f); zoom(lam, 1.35, '78%', '45%') }, D); at(.72, () => { zoom(lam, 1.2, '45%', '30%'); key(f) }, D) } },
  brecha: { preparar(_, lam) { const D = dur(4); load(lam); const f = IF(lam)[0]; zoom(lam, 1, '50%', '50%')
    at(.18, () => key(f), D); at(.42, () => zoom(lam, 1.8, '62%', '40%'), D) } },
  tipos: { preparar(_, lam) { const D = dur(4), el = lam.querySelector('#tp'); el.classList.remove('go')
    el.style.setProperty('--u', (D * .75 / 3.5) + 's'); at(.03, () => el.classList.add('go'), D) } },
  marca: { preparar(_, lam) { const D = dur(3); load(lam); const st = [...lam.querySelectorAll('iframe.st')], lbl = lam.querySelector('.lbl')
    const names = ['brand.json → mi marca', 'brand.json → preset: warm', 'brand.json → preset: ink']
    const show = k => { st.forEach((x, j) => x.style.opacity = j === k ? 1 : 0); lbl.textContent = names[k] }
    show(0); at(.4, () => show(1), D); at(.72, () => show(2), D) } },
  ppt: { preparar(_, lam) { const v = lam.querySelector('video'); v.currentTime = 0; v.play().catch(() => {}) } },
  instalar: { preparar(_, lam) { const D = dur(2.5), f = IF(lam)[0]; f.dataset.src = f.dataset.base + '&dur=' + (D * .92).toFixed(2); load(lam) } },
  iframes: { preparar(_, lam) { load(lam) } },
}
