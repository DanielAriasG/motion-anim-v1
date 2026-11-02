# Plantilla de prompt

Esta plantilla sirve para encargar una película. Se rellena por campos y sigue la estructura del prompt de
"Anonymization and pseudonymization of structured data" (película 1, v9), el piloto narrado del que
nace este skill. Debajo de la plantilla hay un ejemplo resuelto con esa película.

**Cómo usarla**
1. Copia el bloque y rellena los marcadores `<...>`.
2. Borra las líneas que no apliquen.
3. Pégalo en Claude con el skill instalado.

Las seis **RESPUESTAS DEL BRIEF** son las preguntas que el skill hace antes de construir. Si ya están
respondidas aquí, no necesita hacerlas.

```
PELÍCULA · <TÍTULO> (<narrada | sin voz>, <duración, p. ej. 60-90 s>)

IDEA
Qué explica la película: <una frase>.
Titular (la frase que se recuerda): "<titular>"
Público: <quién>. Sensación: <p. ej. precisa, tranquila, fiable, con un momento de sorpresa>.
Mensaje central: <2-3 frases: lo que el espectador debe entender al final>.

RESPUESTAS DEL BRIEF (las seis preguntas del skill)
1. Documentación de marca: <ruta a la guía de marca, o "ninguna: estilo Apple por defecto">
   Colores (hex), tipografías, reglas que respetar: <...>
2. Logos: <ruta(s), mejor SVG>, colocados <esquina arriba-izquierda | arriba-derecha | intro | tarjeta final | ninguno>
3. Voz: <ninguna | voz local gratuita | ElevenLabs (clave API / MCP) | Fish Audio (MCP / clave API) | otra | mi grabación>
   Nombre o ID de la voz: <...>. Idioma: <es | en | ...>. Audios ya hechos: <carpeta o "no">
4. Música: <generada: estilo <alegre | tranquilo | serio> | mi archivo <ruta> (licencia: <...>) | ninguna>
5. Subtítulos: <sí: .srt + pista de subtítulos | no>
6. Intro: <ninguna | descripción: "<qué dice y qué muestra>" | vídeo: <ruta>>
   Cierre (outro): <ninguno | descripción: "<...>" | vídeo: <ruta>>

NARRACIÓN (si es narrada)
Una línea por bloque; los títulos en pantalla son las palabras dichas, que aparecen una a una al pronunciarse.
Escribe para el oído: frases cortas, sin abreviaturas que la voz lea mal. Unas 130-150 palabras por minuto.
<pega el guion, o "escríbelo a partir de los bloques de abajo">

GRÁFICOS
- Contenido en tarjetas blancas sobre un fondo claro; componentes conocidos: <tablas, etiquetas, tarjetas, gráficos...>
- Tipografía: la del sistema (o la de la marca); jerarquía por tamaño y peso.
- Movimiento: muelles suaves, una cosa cada vez; nada pasa por encima de texto legible.
- Un momento estrella: <el fotograma que la gente recordará>
- Cabecera / etiqueta de capítulo: <texto, o ninguna>

COLOR (un color, un significado)
<color #hex> significa <...> · <color #hex> significa <...> · <color #hex> significa <...>
El texto sobre relleno es negro o blanco (comprueba el contraste).

REGLA DE DATOS
<p. ej. todos los registros son sintéticos: nombres, IDs y lugares inventados. Nunca personas ni filas reales.>
Fuentes de datos y cifras: <...>

BLOQUES DE LA HISTORIA (cada uno narrado)
1. Gancho: <...>
2. <...>
3. Clímax / momento estrella: <...>
4. <...>
5. Tarjeta final: el titular, <título de la serie>, línea de fuentes: "<fuentes>", <logos / texto de financiación>.

REFERENCIAS EN PANTALLA (opcional)
<artículos de ley, estudios, guías: etiquetas cortas junto a la idea que apoyan, cita completa en la tarjeta final>

ENTREGA
<ruta/nombre>.mp4, 1920x1080, 60 fps, -16 LUFS (o <-16.9 para igualar una serie>), subtítulos como arriba.
Revisar fotogramas de cada bloque antes del render final; informar de lo que no se pudo comprobar.
```

---

## Ejemplo resuelto: película 1 v9 (plantilla rellenada)

Es el brief más reciente de la película 1, pasado a la plantilla. La narración está en inglés porque así
es la película. Usa la marca eCAN Plus. Las películas de eCAN Plus se hacen con el skill eCAN Motion Anim,
que ya incluye la marca, la intro y el cierre. Cualquier otro cliente rellena los mismos campos con su
propia marca.

```
PELÍCULA · ANONYMIZATION AND PSEUDONYMIZATION OF STRUCTURED DATA (narrada, ~85 s + intro + cierre)

IDEA
Qué explica: cómo funcionan la anonimización y la seudonimización en una tabla de historias clínicas.
Titular: "A name is not the only thing that names you."
Público: responsables de datos de hospitales, investigadores y DPD. Sensación: precisa, tranquila,
fiable, con un momento de inquietud.
Mensaje central: quitar el nombre es seudonimizar, y los datos siguen siendo personales mientras
exista una clave. La reidentificación llega por combinaciones (código postal + fecha de nacimiento
+ sexo). La generalización rompe esas combinaciones.

RESPUESTAS DEL BRIEF
1. Documentación de marca: guía de identidad de eCAN Plus. Colores: verde #026873, coral #ED6D7C,
   turquesa #41B9C6, coral claro #F1A6A0, gris #C1D0D9 (solo tintes y sombras, sin colores nuevos).
   Emblema de la UE y texto de financiación obligatorios.
2. Logos: logo corto de eCAN Plus arriba a la derecha, 80 px de alto (SVG, tamaño exacto); sello
   "Co-funded by" de la UE en la tarjeta final y en la intro.
3. Voz: Fish Audio por el conector MCP, voz "Ethan" 536d3a5e000945adb7038665781a4aca, modelo
   s2.1-pro, en inglés. Una llamada por línea; audios guardados en fish-ethan/. Tiempos de cada
   palabra medidos del audio (faster-whisper).
4. Música: mi archivo Free-audios/musinova-calm-ambient-science-medical-tech.mp3, bajo la voz;
   mantener los efectos generados en los momentos clave. (Segunda versión: fondo generado, acordes
   mayores, luminoso, nada lúgubre.)
5. Subtítulos: sí (.srt + pista de subtítulos).
6. Intro: descripción: el logo horizontal grande de eCAN Plus, el bloque de la UE y la frase hablada
   "eCAN Plus, a European Joint Action bringing the benefits of digital health to cancer centres,
   presents: anonymization and pseudonymization of structured data."
   Cierre: vídeo: eCANPlus_outro.mp4.

GRÁFICOS
- Tarjetas blancas (radio 28, sombra suave) sobre un fondo claro teñido del gris de marca.
  Componentes conocidos: tablas, etiquetas en cápsula, una tarjeta de clave, una tarjeta de contacto.
- Tipografía: Segoe UI Variable Display y Text; Consolas para códigos y tokens. Etiquetas en negrita.
- Momento estrella: la fila reidentificada se convierte en una tarjeta de contacto (monograma coral,
  nombre, "Re-identified", el diagnóstico adjunto).
- Cabecera: "Anonymization and pseudonymization of structured data", arriba a la izquierda, en
  verde; la técnica de la que habla la voz se ilumina en una cápsula verde.

COLOR
coral = identifica a una persona · turquesa = da pistas de una persona (cuasi-identificadores) ·
verde = protegido o seguro (tokens, valores generalizados, pruebas superadas) · verde-900 = la clave
· coral claro = datos externos (el registro) · gris = atributo sensible.

REGLA DE DATOS
Todos los registros son sintéticos. La generalización sigue las Directrices 02/2026 del CEPD
(borrador), ejemplos 10 y 12: las fechas de nacimiento pasan a 1946 y los códigos postales a 54***.

BLOQUES DE LA HISTORIA
1. Gancho: "You don't need a name to find someone." se convierte en el título; aparece la tabla de
   pacientes y se nombra el papel de cada columna al decirlo.
2. Seudonimización: nombre e ID salen a una tarjeta oscura de clave, los tokens los sustituyen, la
   clave se cierra ("held separately"). "Pseudonymized data is still personal data."
3. Clímax: un registro público; sexo, fecha de nacimiento y código postal coinciden al decirlos; el
   token se convierte en una persona (la tarjeta de contacto). "No name needed."
4. Anonimización: generalizar, reagrupar en dos grupos k = 3; las tres pruebas del CEPD responden "No".
4b. Lo que se queda: el diagnóstico se queda; "Health data may serve research, with safeguards."
5. Tarjeta final: el titular, título de la serie, fuentes, bloque de la UE; tarjeta de autoría.

REFERENCIAS EN PANTALLA
Etiquetas: "Art. 4(5)" junto a la clave, "Recital 26" junto al título, "Art. 5(1)(c) minimisation"
junto a "Generalized", "Art. 9 · special category" en el diagnóstico. Tarjeta final: "GDPR Arts.
4(5), 5(1)(c), 9(2)(j), 89(1); Recital 26. Not legal advice."

ENTREGA
renders/privacy-01-structured-v9-ambient.mp4 y -generated.mp4: 1920x1080, 60 fps, -16.9 LUFS,
subtítulos .srt + pista de subtítulos.
```
