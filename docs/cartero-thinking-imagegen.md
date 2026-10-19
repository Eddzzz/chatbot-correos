# Secuencia del cartero pensando

La versión actual usa `frontend/public/cartero-thinking-v2.png`, creada con ImageGen tomando la primera secuencia como referencia: 24 poses en seis columnas y cuatro filas. El cuerpo, la mano bajo la barbilla y la sonrisa permanecen estables; los cambios se concentran en mirada, cejas y un parpadeo.

`scripts/build_thinking_animation.ps1` genera `frontend/public/cartero-thinking-v2-24fps.webm`: 320 × 320 px, 96 cuadros en cuatro segundos a 24 fps. Mezcla cuadros próximos y sus canales alfa sin deformarlos con flujo óptico. Incluye cuadros de continuidad al final para cerrar el bucle. La interfaz reproduce el vídeo transparente sin sonido y muestra la primera pose estática con movimiento reducido. Las versiones anteriores se conservan como fuentes.

## Prompt actual (ImageGen integrado)

undefined

## Prompt de la primera versión

Create ONE production animation sprite sheet using the attached Correos de Bolivia courier mascot as identity reference. This is a pose transformation/character animation asset, not a UI mockup. Preserve his exact friendly 3D cartoon face, large brown eyes, yellow postal cap and yellow vest, white long sleeves, dark blue accents and Correos de Bolivia insignia. Remove parcel and thumbs up; render BOTH arms anatomically intact. SIX consecutive animation frames arranged in a precise THREE COLUMNS by TWO ROWS grid of equal square cells (overall canvas 3:2 aspect ratio). Absolutely no borders, gutters, frame numbers, captions, background scene or checkerboard. Genuine transparent background. Each cell uses the SAME fixed camera, scale, lighting, center position and waist-up crop, with cap fully visible and generous 8% safe padding; each character fills 82% of its cell height. Sequence is read left to right, top to bottom: 1 friendly thoughtful smile, right hand resting under chin and eyes looking slightly up; 2 head tilts subtly left and right index finger taps chin; 3 eyes look up right, brows lift, hand still at chin; 4 brief blink and small thoughtful head dip; 5 eyes open and a tiny warm idea smile, index finger begins lifting near cheek; 6 hand returns under chin and head returns close to frame 1 for seamless looping. This must be six nearly identical snapshots of ONE character moving subtly, not six different characters or art styles. Rich polished high-resolution 3D rendering, clean edges and readable face at 240px display. Keep cap logo as in reference. No props outside character, no speech bubbles or text.
