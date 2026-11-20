<div align="center">

<img src="docs/assets/logo.svg" width="96" alt="keystone-deck">

# keystone-deck

**Presentaciones que dicen lo que quieres decir, como lo quieres decir.**<br>
Un plugin de Claude Code que convierte tu argumento, tus cifras y tu marca en un deck en vivo con movimiento, y lo exporta a PowerPoint.

[![Versión](https://img.shields.io/badge/versión-0.2.0-1652E0)](CHANGELOG.md)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-1652E0)](LICENSE)
[![Plugin de Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-F4A93C)](https://docs.claude.com/en/docs/claude-code/plugins)

[English](README.md) · [Español](README.es.md)

[Por qué](#por-qué) · [Instalación](#instalación) · [Escenas](#escenas) · [Cómo funciona](#cómo-funciona) · [Ejemplo](#ejemplo) · [Comparación](#comparación) · [Preguntas](#preguntas-frecuentes)

<img src="docs/assets/hero.png" width="900" alt="Tres láminas de un pitch hecho con keystone-deck: una población que se queda en el camino, el producto funcionando en un laptop y un celular, y una proyección con la brecha rotulada">

</div>

## Por qué

Las herramientas de presentaciones deciden qué puedes decir. Eliges una plantilla y doblas la historia para que quepa en sus cajas: una lista de viñetas donde debería haber una persona, un gráfico genérico donde tus cifras deberían moverse, un menú de animaciones en vez del momento que necesitas mostrar.

keystone-deck lo da vuelta. Tú describes el argumento; Claude escribe el guion, revisa cada cifra y compone cada lámina como una escena hecha para ese punto: las personas que se quedan en el camino, el producto funcionando en las manos de alguien, la brecha en la proyección. El resultado corre en el navegador, se abre en PowerPoint y lleva tu marca.

<div align="center">
<img src="docs/assets/demo.gif" width="760" alt="Una lámina donde una paciente toca «No puedo» en su celular y la agenda del centro reasigna la hora sola">
<br><sub>La lámina del producto en el pitch de ejemplo: el celular y el laptop son una maqueta en vivo, manejada clic a clic.</sub>
</div>

## Qué incluye

- **El guion antes que las láminas.** `talk.md` reúne la audiencia, el hilo en una oración y lo que dices en cada lámina. Cada lámina contesta la pregunta que dejó la anterior.
- **Cifras que puedes defender.** Las cifras viven en un registro de evidencia con su nivel (verificada, dato propio, supuesto, meta) y su fuente. Las láminas las referencian; nada se escribe a mano.
- **Escenas, no plantillas.** Quince escenas para decks de alto impacto: una persona en un día concreto, una población que se queda en el camino, problema y solución en espejo, el producto funcionando en dispositivos, la competencia en dos ejes, el mercado como presupuesto de quien paga, la tracción, proyecciones con la brecha rotulada y el pedido con uso de fondos. Cuando ninguna calza, Claude compone la lámina.
- **Tu marca, en todo.** Un solo `brand.json` (design tokens del W3C), revisado por contraste, mueve el deck en vivo, el PowerPoint y las figuras.
- **Tu guion, narrado.** El mismo guion se convierte en un video con tu voz clonada (ElevenLabs): cada escena dura lo que su frase y los clics caen cuando la voz los nombra.
- **Un PowerPoint que conserva el movimiento.** Cada escena se graba en video y se pone en PowerPoint con los títulos como texto nativo editable y las notas del orador de tu guion. Quien nunca toca HTML solo lo abre y presenta.

## Escenas

Cada lámina es una escena compuesta para su punto. Las catorce de abajo vienen del pitch de ejemplo, construido por el plugin; `html` le permite a Claude componer cualquier otra.

| | | |
|---|---|---|
| <img src="docs/assets/scenes/cover.png" width="260" alt="Portada"> | <img src="docs/assets/scenes/persona.png" width="260" alt="Persona"> | <img src="docs/assets/scenes/journey.png" width="260" alt="Población en el camino"> |
| `cover` · Portada | `persona` · Persona | `journey` · Población en el camino |
| <img src="docs/assets/scenes/mirror.png" width="260" alt="Espejo"> | <img src="docs/assets/scenes/product.png" width="260" alt="Producto en vivo"> | <img src="docs/assets/scenes/why-now.png" width="260" alt="Por qué ahora"> |
| `mirror` · Espejo | `product` · Producto en vivo | `why-now` · Por qué ahora |
| <img src="docs/assets/scenes/matrix.png" width="260" alt="Matriz"> | <img src="docs/assets/scenes/model.png" width="260" alt="Modelo"> | <img src="docs/assets/scenes/funnel.png" width="260" alt="Embudo"> |
| `matrix` · Matriz | `model` · Modelo | `funnel` · Embudo |
| <img src="docs/assets/scenes/timeline.png" width="260" alt="Línea de tiempo"> | <img src="docs/assets/scenes/projection.png" width="260" alt="Proyección"> | <img src="docs/assets/scenes/team.png" width="260" alt="Equipo"> |
| `timeline` · Línea de tiempo | `projection` · Proyección | `team` · Equipo |
| <img src="docs/assets/scenes/ask.png" width="260" alt="Pedido"> | <img src="docs/assets/scenes/closing.png" width="260" alt="Cierre"> |
| `ask` · Pedido | `closing` · Cierre |

Referencia completa: [skill `stage-deck`](plugins/keystone-html/skills/stage-deck/SKILL.md).

## Instalación

En Claude Code:

```text
/plugin marketplace add fsotosa-ops/keystone-deck
/plugin install keystone@keystone-deck
/plugin install keystone-html@keystone-deck
/plugin install keystone-pptx@keystone-deck
/plugin install keystone-video@keystone-deck
```

| Plugin | Qué agrega | Requiere |
|---|---|---|
| `keystone` | El método: narrativa, evidencia, gramática visual, kit de marca, chequeos | Python 3.10+ |
| `keystone-html` | El motor de escenas | Python, Chrome |
| `keystone-pptx` | La exportación a PowerPoint con movimiento | Python, Chrome; `python-pptx`, `playwright`, `imageio-ffmpeg` con `uv run --with …` |
| `keystone-video` | Un video narrado desde tu guion, con tu voz vía ElevenLabs | Python, Chrome, `imageio-ffmpeg`; opcional `ELEVENLABS_API_KEY` |

## Inicio rápido

```text
/keystone:new mi-pitch               # Claude pregunta quién decide y qué, y propone la secuencia de láminas
/keystone:brand ruta/a/guia.pdf      # o un sitio web, o preset:ocean
/keystone:review mi-pitch            # todos los chequeos y una revisión independiente
```

Después pide: *«ármalo como deck en vivo»* o *«expórtalo a PowerPoint»*.

## Tipos de presentación

Eliges el tipo y el método adapta el orden y las reglas:

| Tipo | Orden |
|---|---|
| **Pitch** | persona → problema con evidencia propia → solución en espejo → producto en contexto → por qué ahora → competencia → modelo → mercado → tracción → números → equipo → pedido |
| **Keynote** | un momento vivido → la tensión → el giro → tres ideas con una historia cada una → qué hacer el lunes → la frase que la gente repite |
| **Clase** | intuición → ejemplo con números → versión formal → pregunta de chequeo → trampas |
| **Informe** | la decisión que se necesita → qué cambió → evidencia → opciones → recomendación → próximos pasos |

## Cómo funciona

```text
   talk.md        evidence.json        brand.json
  (argumento)       (cifras)        (design tokens)
       └───────────── keystone check ─────────────┘
                           │
                 deck.json  →  escenas
                           │
          ┌────────────────┴────────────────┐
   deck en vivo (navegador)          PowerPoint (.pptx)
   pasos · presentador · producto    video por escena · texto nativo · notas
```

Tres contratos separan contenido, evidencia y marca, así que puedes cambiar la marca o la salida sin reescribir la historia. El detalle está en [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Ejemplo

[`examples/pitch-asisto`](examples/pitch-asisto) es un pitch de inversión completo de 14 láminas para una startup ficticia: el guion, el registro de cifras, las láminas, una maqueta del producto con un celular y un panel de clínica, y los guiones de clics. Constrúyelo, preséntalo y expórtalo:

```bash
python3 plugins/keystone-html/scripts/build_stage.py examples/pitch-asisto
python3 -m http.server 8770 --directory examples/pitch-asisto/build   # abre /stage/
uv run --with playwright --with python-pptx --with imageio-ffmpeg \
  python plugins/keystone-pptx/scripts/build_pptx.py examples/pitch-asisto
```

## Comparación

| | keystone-deck | Generadores de láminas con IA (Gamma, Beautiful.ai, StarryKit) | Láminas como código (Slidev, reveal.js) | PowerPoint / Keynote |
|---|---|---|---|---|
| Parte de | tu argumento y tus cifras | un prompt o un documento | Markdown que escribes | una lámina en blanco |
| Chequeos de narrativa (hilo, fuentes, palabras por lámina) | sí, el build falla | no | no | no |
| Producto funcionando dentro de la lámina | sí, en vivo y guionado | capturas | posible, a mano | video o capturas |
| Tu marca | un archivo de tokens, con contraste revisado | tema o kit de marca | CSS | plantilla |
| Corre en local | sí | servicio en la nube | sí | sí |
| Salida | deck en vivo, PowerPoint con movimiento, video narrado | su editor, PPTX, PDF | web, PDF | PPTX, PDF, video |

Usa un generador de láminas con IA cuando necesitas muchas piezas bonitas rápido. Usa keystone-deck cuando la presentación tiene que sostenerse frente a un inversionista, un comité o una audiencia que va a cuestionar las cifras.

## Preguntas frecuentes

**¿Funciona en claude.ai?** El método sí: las skills y los comandos cargan en claude.ai cuando agregas el plugin desde *Personalizar › Plugins*. Construir decks ejecuta scripts locales y un navegador, así que los motores necesitan Claude Code.

**¿Necesito saber programar?** No. Le hablas a Claude y él escribe los archivos. El resultado es un enlace para abrir en el navegador y un `.pptx` para presentar.

**¿Puedo editar el PowerPoint?** Los títulos, el texto y las notas son nativos y editables. La parte animada de cada lámina es un video; para cambiarla, se lo pides a Claude y exportas de nuevo.

**¿Mis datos salen de mi computador?** Los plugins corren en local. Las fuentes se cargan desde Google Fonts; nada más sale de tu equipo salvo que actives una integración.

## Contribuir

Los issues y pull requests son bienvenidos; revisa [CONTRIBUTING.md](CONTRIBUTING.md). Las escenas nuevas mantienen intactos los tres contratos y vienen con un ejemplo renderizado.

## Licencia

[MIT](LICENSE) · Creado por [Felipe Soto Santibáñez](https://github.com/fsotosa-ops).
