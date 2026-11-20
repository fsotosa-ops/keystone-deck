// Escenas del pitch de Asisto: preparan la app ficticia y definen qué pasa en cada clic.
// Los rótulos leen lo que muestra la app (el contador de horas recuperadas sube en vivo).
const A = app => app.win.__app

window.ESCENAS = {
  // Portada: llega el recordatorio al celular de Marta.
  portada: {
    async preparar({ tel }) {
      A(tel).reiniciar(false)
      setTimeout(() => A(tel).decir(A(tel).RECORDATORIO, 1100), 900)
    }
  },

  // Conoce a Marta: el recordatorio ya está; el jueves no puede.
  marta: {
    async preparar({ tel }) { A(tel).reiniciar(true) },
    pasos: [
      async ({ tel }, lam, H) => H.rotulo(lam, tel, '.msg[data-i="0"]',
        { dato: 'Jueves 10:30', texto: 'ese día lleva a su madre a diálisis. No va a poder ir.', lado: 'aba', ancho: 340 })
    ]
  },

  // El producto en contexto: Marta libera su hora y la agenda del centro se reasigna sola.
  producto: {
    async preparar({ tel, lap }) { A(tel).reiniciar(true); A(lap).render() },
    pasos: [
      async ({ tel }, lam, H) => H.rotulo(lam, tel, '.msg[data-i="0"]',
        { dato: '48 h antes', texto: 'el recordatorio llega por chat, sin descargar nada', lado: 'izq', ancho: 380 }),
      async ({ tel, lap }, lam, H) => {
        await H.clic(lam, tel, '[data-acc="no-puedo"]', 500)
        await H.espera(2600)
        H.rotulo(lam, lap, 'tr[data-h="10:30"]', { dato: 'Reasignada', texto: 'la hora de Marta pasa sola a quien esperaba', lado: 'der', ancho: 380 })
      },
      async ({ lap }, lam, H) => H.rotulo(lam, lap, '.k-recuperadas',
        { dato: el => el.querySelector('b').textContent.trim(), texto: 'horas recuperadas esta semana, sin una sola llamada', lado: 'der', ancho: 380, vivo: 300 })
    ]
  },

  // Modelo: lo mismo que ve cada uno, al lado de lo que paga.
  modelo: {
    async preparar({ tel, lap }) { A(tel).reiniciar(true); A(lap).render() }
  },

  // Cierre: Marta avisa y su hora vuelve a la agenda.
  cierre: {
    async preparar({ tel }) {
      A(tel).reiniciar(true)
      setTimeout(() => A(tel).noPuedo(), 1400)
    }
  }
}
