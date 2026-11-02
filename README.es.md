# Motion Anim V1

[English](README.md) · **Español**

Motion Anim V1 es un skill de Claude que hace vídeos de motion graphics: vídeos explicativos, diagramas
animados y películas narradas. Cada fotograma se dibuja con código en un canvas y se renderiza a MP4 en
1080p60. El diseño sigue las Human Interface Guidelines de Apple.

Antes de construir, el skill pregunta seis cosas:
1. la documentación de marca;
2. los logos;
3. la voz: ninguna, una voz local gratuita o un servicio de pago como ElevenLabs o Fish Audio;
4. la música: generada, un archivo propio o ninguna;
5. los subtítulos;
6. la intro y el cierre, cada uno a partir de una descripción o de un vídeo que tú aportas.

Con esas seis respuestas:
- sincroniza cada animación con las palabras de la narración, usando tiempos medidos del audio;
- entrega un .srt y una pista de subtítulos;
- une la intro, la película y el cierre en un solo archivo;
- mezcla el audio a -16 LUFS;
- revisa el resultado antes de entregarlo.

## Contenido
- [Instalar el skill](#instalar-el-skill)
- [Instalar los requisitos](#instalar-los-requisitos)
- [Inicio rápido](#inicio-rápido)
- [Plantilla de prompt](#plantilla-de-prompt)
- [Voces: Fish Audio y ElevenLabs (MCP o clave API)](#voces-fish-audio-y-elevenlabs-mcp-o-clave-api)
- [Marca](#marca)
- [Música](#música)
- [Intro y cierre](#intro-y-cierre)
- [Estructura de carpetas](#estructura-de-carpetas)

## Instalar el skill
- **claude.ai**: sube `motion-anim-v1.skill` en Ajustes → Capacidades → Skills. El archivo `.skill` es un zip
  de esta carpeta sin `evals/`.
- **Claude Code**: copia esta carpeta en `~/.claude/skills/motion-anim-v1/`.

## Instalar los requisitos
El motor es JavaScript (Node.js) con algunos scripts de Python. Chrome dibuja los fotogramas y ffmpeg
codifica el vídeo y mezcla el sonido. El motor no usa React ni ningún otro framework: cada película es una
página HTML con un canvas.

| Qué | Para qué | Cómo instalarlo |
|---|---|---|
| **Node.js 18+** (incluye npm) | Ejecuta el motor, el render y la música | https://nodejs.org (LTS), o `winget install OpenJS.NodeJS.LTS` |
| **puppeteer-core** | Controla Chrome para dibujar cada fotograma | `npm i puppeteer-core` en la carpeta del proyecto, una vez |
| **Chrome o Edge** | El navegador que dibuja los fotogramas | Normalmente ya está instalado |
| **Python 3.10+** con Pillow | Plantillas, orquestador, revisión y comprobaciones | https://python.org, luego `pip install pillow` |
| **ffmpeg / ffprobe** en el PATH | Codificación, volumen, unión de clips | `winget install Gyan.FFmpeg`, `brew install ffmpeg` o `apt install ffmpeg` |
| **faster-whisper** (opcional) | Mide los tiempos de cada palabra en voces que no los dan (Fish Audio, OpenAI, grabaciones) | `pip install faster-whisper` (la primera vez descarga un modelo de unos 460 MB) |

Para comprobar la instalación:
```
node --version && npm --version && python --version && ffmpeg -version
```

## Inicio rápido
Pide un vídeo a Claude, por ejemplo *"Haz un vídeo explicativo narrado de 60 segundos sobre cómo funcionan
las vacunas"*. El skill hace sus seis preguntas y después prepara la película, la anima, la revisa y la
construye. Los mismos pasos a mano:
```
python scripts/new_film.py <proyecto> mi-pelicula --narrated --title "Cómo funcionan las vacunas" \
    --intro-text "Ciencia Básica presenta: cómo funcionan las vacunas." --outro-video cierre.mp4
cd <proyecto> && npm i puppeteer-core
python engine/make_film.py mi-pelicula --voice sapi --music fondo.mp3   # o --voice elevenlabs / import:<carpeta>
```
El resultado es `mi-pelicula/mi-pelicula.mp4` y `mi-pelicula.srt`. El informe de `check_film.py` sale al final.

En una narración que no esté en inglés, pon `"language": "es"` (o el idioma que sea) en `narration.json`.
Así los tiempos se miden con el modelo multilingüe y la pista de subtítulos lleva ese idioma.

## Plantilla de prompt
[prompts/plantilla-prompt.md](prompts/plantilla-prompt.md) es un brief para rellenar. Incluye las seis
respuestas del brief, la idea, la narración, los gráficos, el color, los datos, los bloques de la historia
y la entrega. Sigue el prompt de la película 1 ("Anonymization and pseudonymization of structured data",
v9) y trae ese ejemplo ya rellenado. Versión en inglés:
[prompts/prompt-template.md](prompts/prompt-template.md).

## Voces: Fish Audio y ElevenLabs (MCP o clave API)
Cada servicio se puede usar de dos maneras:
- **Conector MCP**: Claude usa el servicio como una herramienta dentro de la conversación y guarda los audios.
  Inicias sesión una vez y ninguna clave aparece en los comandos.
- **Clave API**: un script llama al servicio directamente. La clave va en una variable de entorno solo para
  ese comando.

No pongas claves en archivos, scripts ni en el chat. Si pegas una clave en un chat por error, cámbiala.

### ElevenLabs
ElevenLabs devuelve los tiempos de cada palabra, así que es la sincronización más precisa.
- **Clave API** (integrado en el skill):
  ```
  # macOS / Linux / Git Bash
  ELEVENLABS_API_KEY=sk_... python engine/make_film.py mi-pelicula --voice elevenlabs --voice-id <id de voz>
  # PowerShell
  $env:ELEVENLABS_API_KEY="sk_..."; python engine/make_film.py mi-pelicula --voice elevenlabs --voice-id <id de voz>
  ```
  - El plan gratuito solo permite las voces predefinidas, por ejemplo Daniel `onwK4e9ZLuTAKqWW03F9`.
  - La voz se guarda en `vo-<id de voz>/`, así que reconstruir la película no gasta créditos.
- **MCP**: ElevenLabs publica un servidor MCP (`elevenlabs-mcp`). El comando de instalación, que también
  pide tu clave, está en la documentación de ElevenLabs. Claude guarda un archivo por línea de narración
  como `<id de línea>.mp3` en una carpeta. Después:
  ```
  python engine/make_film.py mi-pelicula --voice import:<carpeta>
  ```
  Esos audios no traen tiempos, así que se miden del audio (necesita faster-whisper).

### Fish Audio
Fish Audio no devuelve los tiempos de cada palabra. Siempre se miden del audio, así que instala
faster-whisper.
- **MCP** (recomendado):
  ```
  claude mcp add --transport http fish-audio https://api.fish.audio/mcp
  ```
  - Luego ejecuta `/mcp` en Claude Code para iniciar sesión.
  - Claude genera un archivo por línea con la voz elegida y guarda cada uno como `<id de línea>.mp3`.
  - Las líneas de la intro y del cierre van en la misma carpeta, como `intro.mp3` y `outro.mp3`.
  - Después ejecuta `python engine/make_film.py mi-pelicula --voice import:<carpeta>`.
- **Clave API**: llama a la API de texto a voz de Fish Audio (`POST https://api.fish.audio/v1/tts` con
  `Authorization: Bearer $FISH_API_KEY` y el `reference_id` de tu voz). El modelo y los parámetros
  actuales están en docs.fish.audio. Guarda un MP3 por línea como `<id de línea>.mp3` e importa la carpeta
  igual que con MCP.

### Voces gratuitas y otras
- `--voice sapi` usa la voz gratuita de Windows. Suena sintética, pero sirve para borradores de tiempos.
- macOS `say`, Piper, OpenAI, Azure, Polly o tu propia grabación: guarda un archivo por línea y usa
  `--voice import:<carpeta>`.
- `--voice none` hace una película sin narración. Los tiempos salen de `beats.js`.

## Marca
Por defecto se usan la paleta clara y las tipografías de sistema de Apple. Para usar tu marca, dale al skill
tu guía de marca y tus logos cuando los pida, y escribirá un `theme.js`. También puedes escribirlo tú y
pasarlo con `new_film.py --theme theme.js --assets <carpeta con logos>`:
```js
window.THEME = {
  colors: { brand: '#026873', accent: '#ED6D7C', grey: '#9E9E9E', white: '#FFFFFF', black: '#000000' },
  derive: { brand50: ['tint', 'brand', .9] },            // tintes y sombras de tus colores
  roles:  { canvas: 'brand50', surface: 'white', ink: 'black', secondary: 'grey', hair: 'brand50', shadow: 'black' },
  on:     { brand: 'white', accent: 'white' },           // color del texto sobre cada relleno
  fonts:  { display: ['Montserrat', 'Arial'], text: ['Montserrat', 'Arial'], mono: ['Consolas'] },
  logo:   { src: 'logos/logo.svg', w: 160, h: 48 },      // a este tamaño exacto, arriba a la izquierda por defecto
  margin: 120,
};
```
- Da a cada color un solo significado.
- Comprueba el contraste del texto con `python engine/contrast.py theme.js`.
- Mejor un logo en SVG, a su tamaño de dibujo.
- Solo se ve un logo por fotograma: el de la esquina se aparta cuando una intro o una tarjeta de créditos
  muestra el logo en grande.

## Música
Elige una opción cuando el skill pregunte:
- **Música generada** (por defecto): `score.js` toca un fondo suave y pequeños efectos en los momentos clave
  de la animación. Baja automáticamente bajo la voz. Dile al skill el estilo (alegre, tranquilo, serio) y
  elegirá los acordes.
- **Tu propio archivo de música**:
  ```
  python engine/make_film.py mi-pelicula --music ruta/a/musica.mp3 [--music-level -34]
  ```
  - Se recorta a la duración de la película, entra y sale con fundido y se repite si es más corta.
  - Queda 15 LU por debajo de la voz y baja 8 dB más mientras alguien habla.
  - Los efectos de la música generada se mantienen encima.
  - Comprueba que la licencia de la pista permite tu uso.
- **Ninguna**: quita el fondo y los efectos de `score.js`.

## Intro y cierre
Cada uno puede construirse a partir de una descripción, aportarse como vídeo o no ponerse:
```
# a partir de una descripción: una escena corta con tu logo, la frase y un título
python scripts/new_film.py <proyecto> mi-pelicula --narrated --title "..." \
    --intro-text "Acme presenta: cómo funcionan las copias de seguridad." --intro-title "Copias de seguridad" \
    --outro-text "Gracias por ver el vídeo." --outro-title "acme.example/aprende"

# aportados como vídeos
python scripts/new_film.py <proyecto> mi-pelicula --narrated --intro-video intro.mp4 --outro-video cierre.mp4
```
- **Escenas construidas**: viven en `mi-pelicula/intro/` y `mi-pelicula/outro/`.
  - En una película narrada las dice la misma voz. En una película sin voz se mantienen el tiempo de lectura.
  - Para cambiar su estilo, edita `scene.js` en esas carpetas.
  - Con una voz importada, añade `intro.mp3` y `outro.mp3` a la carpeta de la voz.
- **Vídeos aportados**: se escalan a 1080p sin deformarse, se pasan a 60 fps y se igualan al volumen de la
  película.
- **Unión**: `make_film.py` junta intro + película + cierre en un solo MP4, con una sola pista de subtítulos
  para los tres. Con `--bookends none` se entrega solo la película.

## Estructura de carpetas
- `SKILL.md`: el flujo de trabajo que sigue Claude.
- `prompts/`: plantilla de prompt en inglés y en español, con un ejemplo resuelto.
- `references/`: guía de diseño, narración, API del motor, mapa del código.
- `scripts/`: el motor y sus servicios (`services.json`, ejecutados por `make_film.py`).
- `assets/template/`: la película inicial y la escena de intro y cierre.
- `tools/build_code_graph.py`: regenera `references/code-map.md` después de cambiar el código.
- `evals/`: casos de prueba. Todavía no se han ejecutado: ver `evals/PENDING.md`.
