// keystone-html runtime. Scales the stage to the window, reveals steps on click or arrow keys,
// and syncs a presenter view (key P) over a BroadcastChannel.
// URL options: #3 opens slide 3 · ?step=2 opens two steps · ?all opens every step on every slide
//              ?record hides the cursor and the progress bar (for screen recording and screenshots).
(() => {
  const $ = (s, r = document) => r.querySelector(s)
  const $$ = (s, r = document) => [...r.querySelectorAll(s)]
  const stage = $('#stage')
  const slides = $$('.slide')
  const W = +stage.dataset.w || 1920, H = +stage.dataset.h || 1080
  const channel = new BroadcastChannel(document.body.dataset.channel || 'keystone-deck')
  const params = new URLSearchParams(location.search)
  const showAll = params.has('all')
  let idx = 0, step = 0

  const fit = () => {
    const k = Math.min(innerWidth / W, innerHeight / H)
    stage.style.transform = `translate(-50%, -50%) scale(${k})`
  }
  addEventListener('resize', fit); fit()

  // Stagger entrance order within each slide
  slides.forEach(s => $$('.a', s).forEach((e, i) => e.style.setProperty('--i', i)))

  const steps = s => $$('.step', s)

  function go(i, nSteps = 0) {
    i = Math.max(0, Math.min(slides.length - 1, i))
    if (slides[idx]) slides[idx].classList.remove('on')
    idx = i; step = 0
    const s = slides[idx]
    steps(s).forEach(p => p.classList.remove('seen')); s.querySelectorAll('.dots').forEach(d => d.classList.remove('go'))
    void s.offsetWidth
    s.classList.add('on')
    const n = showAll ? steps(s).length : nSteps
    for (let k = 0; k < n; k++) nextStep(true)
    sync()
  }
  function nextStep(quiet) {
    const ps = steps(slides[idx])
    if (step >= ps.length) return false
    const el = ps[step++]; el.classList.add('seen')
    const d = slides[idx].querySelector('.dots'); if (d && el.classList.contains('dots-fig')) d.classList.add('go')
    if (!quiet) sync()
    return true
  }
  const next = () => { if (!nextStep()) go(idx + 1) }
  const prev = () => { if (step > 0) go(idx, step - 1); else go(idx - 1, steps(slides[idx - 1] || slides[0]).length) }

  function sync() {
    history.replaceState(null, '', location.search + '#' + (idx + 1))
    const bar = $('#progress'); if (bar) bar.style.width = ((idx + 1) / slides.length * 100) + '%'
    const s = slides[idx], n = slides[idx + 1]
    channel.postMessage({
      n: idx + 1, total: slides.length, step, steps: steps(s).length,
      title: s.dataset.title || s.id, onSlide: s.dataset.onSlide || '', notes: s.dataset.notes || '',
      leadsTo: s.dataset.leadsTo || '', seconds: +s.dataset.seconds || 0, speaker: s.dataset.speaker || '',
      next: n ? (n.dataset.title || n.id) : '(end)',
    })
  }

  addEventListener('keydown', e => {
    const k = e.key
    if (['ArrowRight', 'PageDown', ' ', 'Enter'].includes(k)) { e.preventDefault(); next() }
    else if (['ArrowLeft', 'PageUp', 'Backspace'].includes(k)) { e.preventDefault(); prev() }
    else if (k === 'Home') go(0)
    else if (k === 'End') go(slides.length - 1)
    else if (k.toLowerCase() === 'f') document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen()
    else if (k.toLowerCase() === 'p') open(location.pathname.replace(/[^/]*$/, '') + 'presenter.html?channel=' + encodeURIComponent(document.body.dataset.channel || 'keystone-deck'), 'presenter', 'width=1100,height=720')
  })
  stage.addEventListener('click', e => { if (!e.target.closest('a, button, iframe, video')) next() })
  channel.onmessage = e => { if (e.data === 'next') next(); else if (e.data === 'prev') prev(); else if (e.data === 'hello') sync() }

  if (params.has('record')) document.body.classList.add('record')
  // Automation API, used by screenshot, PDF and video tools.
  window.__deck = {
    go: (n, opts = {}) => go(n - 1, opts.allSteps ? 1e6 : (opts.steps || 0)),
    next, prev,
    get count() { return slides.length },
    get index() { return idx + 1 },
    get step() { return step },
    stepsOf: n => steps(slides[n - 1]).length,
    ids: () => slides.map(s => s.id),
  }
  go((parseInt(location.hash.slice(1)) || 1) - 1, +params.get('step') || 0)
})()
