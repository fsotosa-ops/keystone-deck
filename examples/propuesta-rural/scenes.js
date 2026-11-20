// Guiones de clic para las láminas con el producto. Cada paso es una acción real en la app.
// apps.tel = celular de Rosa (productora) · apps.lap = panel de la cocina del colegio (comprador)
window.ESCENAS = {
  demo: {
    async preparar(apps) {
      apps.tel?.win.__app?.reset();
      apps.lap?.win.__app?.reset();
    },
    pasos: [
      // 1. Rosa publica su oferta; aparece en el panel del colegio
      async (apps, lam, H) => {
        await H.clic(lam, apps.tel, '#publicar');
        apps.lap.win.__app.render();
        await H.espera(350);
        H.rotulo(lam, apps.lap, '#oferta-rosa', { lado: 'der', ancho: 380, dx: 0,
          dato: 'Al instante', texto: 'La cocina del colegio ve la oferta de Rosa, a 9 km' });
      },
      // 2. El colegio pide; el pedido llega al celular
      async (apps, lam, H) => {
        await H.clic(lam, apps.lap, '#pedir');
        apps.tel.win.__app.render();
        await H.espera(500);
        H.rotulo(lam, apps.tel, '#pedido-nuevo', { lado: 'izq', ancho: 380,
          dato: 'Pedido nuevo', texto: '40 lechugas y 15 kg de tomate para el jueves' });
      },
      // 3. Rosa acepta; sube la compra local del colegio (lee el número vivo del panel)
      async (apps, lam, H) => {
        await H.clic(lam, apps.tel, '#aceptar');
        apps.lap.win.__app.render();
        await H.espera(900);
        H.rotulo(lam, apps.lap, '#local', { lado: 'der', ancho: 360, dx: 0, vivo: 400,
          dato: el => el.querySelector('.pct').textContent, texto: 'compra local del mes: cruza la meta de 5%' });
      },
      // 4. Lo que Rosa vendió directo esta semana (número vivo del celular)
      async (apps, lam, H) => {
        H.rotulo(lam, apps.tel, '#ventas', { lado: 'izq', ancho: 380, vivo: 400,
          dato: el => el.querySelector('#ventas-cifra').textContent, texto: 'vendido directo esta semana, sin camión intermediario' });
      },
    ],
  },
};
