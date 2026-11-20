// Demo scenes: load each window's iframe when its slide opens, and drive the Asisto deck inside.
const IF = lam => [...lam.querySelectorAll('iframe[data-src]')]
const load = lam => IF(lam).forEach(f => { f.src = 'about:blank'; setTimeout(() => { f.src = f.dataset.src }, 30) })
const key = (f, k = 'ArrowRight') => f.contentWindow?.dispatchEvent(new KeyboardEvent('keydown', { key: k }))
const at = (ms, fn) => setTimeout(fn, ms)
window.ESCENAS = {
  repo: { preparar(_, lam) { load(lam) } },
  iframes: { preparar(_, lam) { load(lam) } },
  asisto3: { preparar(_, lam) { load(lam) } },
  asisto5: { preparar(_, lam) { load(lam); const f = IF(lam)[0]; at(2600, () => key(f)); at(5200, () => key(f)); at(10400, () => key(f)) } },
  asisto11: { preparar(_, lam) { load(lam); const f = IF(lam)[0]; at(2600, () => key(f));
    at(4200, () => { f.src = f.dataset.src.replace('#11', '#13') }); [6600, 7300, 8000, 8700].forEach(t => at(t, () => key(f))) } },
  marca: { preparar(_, lam) { load(lam); const alt = lam.querySelector('iframe.alt'), lbl = lam.querySelector('.lbl');
    alt.style.opacity = 1; lbl.textContent = 'brand.json → preset: warm';
    at(3000, () => { alt.style.opacity = 0; lbl.textContent = 'brand.json → tu marca' }) } },
  ppt: { preparar(_, lam) { const v = lam.querySelector('video'); v.currentTime = 0; v.play().catch(() => {}) } },
}
