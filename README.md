# FM1 Cofrade 🎺🥁 — Semana Santa en tu M-VAVE FM1

Firmware de la comunidad para el **M-VAVE FM1**, hecho con el SDK oficial **FM1 Open V14**
(<https://github.com/m-vave/fm1_open>). Sustituye los 16 proyectos de fábrica por 16 marchas
de Semana Santa con cornetas, trompetas, tambores y todo el salero de la madrugá. La idea es
la misma que la de [`fm1-betis-mode`](https://github.com/cotrino/fm1-betis-mode), pero con
más incienso y menos Heliópolis.

**Demo en el navegador (simulador + instalador):** <https://cotrino.github.io/fm1-cofrade/>

> **Honestidad por delante (que aquí no se engaña a nadie, illo):**
> * El firmware **compila y empaqueta con la toolchain oficial**, los 16 proyectos **pasan la
>   validación del motor real** del SDK (`groove_project_valid`, ejecutado en el simulador WASM)
>   y **se ha instalado y verificado en un FM1 físico** (la identidad y el build id coinciden).
>   Eso sí, las voces y las marchas no se han "escuchado" todavía desde aquí.
> * Proyecto de la comunidad, **no avalado por M-VAVE**. Flashéalo bajo tu responsabilidad.
> * Todas las marchas son **composiciones originales "al estilo de"**. **No** son
>   transcripciones de marchas reales (Amargura, Esperanza de Triana…): no tengo partituras
>   verificadas y no voy a inventarme notas atribuyéndolas a otros. Para aprender de verdad una
>   marcha concreta, sácala de la partitura oficial de la banda.

## Qué incluye

16 proyectos editables (8 pistas × 64 pasos). Cada uno trae
melodía, bajo y percusión. Los 4 primeros son **piezas de aprendizaje**; los demás, formas típicas del repertorio.

| # | Proyecto | BPM | Instrumentos | Para qué sirve |
|---|----------|-----|--------------|----------------|
| 1 | DIANA ILLO | 120 | corneta, trompeta, tuba, percusión | Toque de diana: arpegio de corneta en Do mayor |
| 2 | REDOBLE ILLO | 100 | campana, tuba, percusión | Rudimentos de tambor: redobles, acentos y llamador |
| 3 | POR ANDALUZA | 88 | oboe, guitarra, tuba, percusión | Cadencia andaluza (La m – Sol – Fa – Mi) |
| 4 | SAETA BALCON | 56 | saeta, guitarra, coro, percusión | Melodía quejumbrosa en modo frigio, a media luz |
| 5 | PASO LENTO | 66 | trompeta, fliscorno, tuba, percusión | Marcha procesional lenta en Do menor |
| 6 | LA CHICOTA | 84 | corneta, trombón, tuba, percusión | Marcha de cornetas y tambores, redoble de cierre |
| 7 | A LA IGUALA | 76 | trompeta, campana, tuba, percusión | Paso de costaleros acompasado por el llamador |
| 8 | FUNEBRE ARTE | 52 | oboe, trombón, tuba, percusión | Marcha fúnebre, solemne y contenida |
| 9 | LA MADRUGA | 72 | corneta, flauta, tuba, percusión | La madrugá: arpegios de flauta sobre corneta |
| 10 | CORNETAS YA | 120 | corneta, trompeta, trombón, tuba, percusión | Banda de cornetas y tambores a plena potencia |
| 11 | VIVA TRIANA | 108 | clarinete, campanilla, tuba, percusión | Marcha alegre con swing, tipo "pasodoble" |
| 12 | LEVANTA YA | 96 | corneta, trompeta, trombón, tuba, percusión | La levantá: de menos a más |
| 13 | SOLEA PALIO | 34 | oboe, guitarra, tuba, percusión | Compás de 12 tiempos (soleá) con palmas |
| 14 | CAMPANILLERO | 96 | flauta, campanilla, guitarra, tuba, percusión | Ligera y campanillera, con swing |
| 15 | COSTALERO | 58 | trombón, bombardino, tuba, percusión | Marcha de palio a ritmo de costal |
| 16 | RESURRECCION | 126 | corneta, trompeta, trombón, tuba, percusión | Domingo de Resurrección, a toda pastilla |

Los instrumentos usan voces del **banco FM de fábrica del FM1** (BRASS, WOODWIND, ORGAN, VOICE,
bells…) y el kit de percusión 808. Las pistas de percusión usan los pads
BD = bombo, SD = tambor, LT/MT/HT = tambores graves/medios/agudos, RS = palo, CB = llamador,
CP = palmas, CY = platillos.

La pantalla de arranque dice *FM1 · MODO COFRADE · SEMANA SANTA · "QUE VIENE EL PASO, ILLO!"*.

### Cómo aprender con ello

1. Empieza por **DIANA ILLO** a 60 BPM: toca encima con las teclas lo que oyes.
2. Usa **REDOBLE ILLO** para fijar el pulso con el llamador (el 'CB' del primer tiempo).
3. Pasa a **POR ANDALUZA** y **SAETA BALCON** para oído armónico.
4. Silencia (mute) la melodía de cualquier marcha y tócala tú; edita pasos, notas y tempo: son proyectos normales.

## Instalar

1. **Haz copia de seguridad** de tus proyectos y de la configuración (el firmware sustituye los proyectos de fábrica, no los slots de usuario).
2. Si el FM1 trae otro firmware de terceros (Felucca, SLOOP… se identifican como `FM-1_9xx`), su actualizador rechaza los paquetes basados en el SDK Open: **instala antes el V15 oficial** (p. ej. desde thefirmwarehub.com, «Back to official V15»).
3. Con el FM1 en V15 u Open, por USB y con Chrome/Edge: abre [`dist/FM1_COFRADE_Instalador.html`](dist/FM1_COFRADE_Instalador.html) (el workbench oficial con este firmware integrado; sírvelo con `python -m http.server` desde `dist`) y usa «Device update», o bien ejecuta sin navegador `python tools\fm1_flash.py --go` (SysEx por winmm; con `--stock` instala el V15 oficial del SDK).
4. Para volver al original, instala V15 con el mismo script (`--stock`) o desde la web oficial.

Probado en un FM1 real (Felucca → V15 → Cofrade): el dispositivo reporta `FM-1_8000014` y el build id del paquete.

SHA-256: ver [`dist/SHA256SUMS.txt`](dist/SHA256SUMS.txt). Informes del build: `dist/firmware-report.json`,
`dist/package-report.json`.

## Recompilar

Requisitos: Windows, PowerShell, Python 3.10+ y la toolchain JieLi 2.5.3 (instrucciones en
`vendor\fm1_open\README.md`; el SDK verifica sus hashes). Por defecto se busca en
`.tools\jieli-2.5.3\C$\JL\pi32`, o en la ruta de la variable `FM1_PI32_TOOLCHAIN`.

```powershell
.\Build-Cofrade.ps1                  # firmware -> dist\FM1_COFRADE.fwsc
.\Build-Cofrade.ps1 -Web             # además, simulador web (requiere WASI SDK 27 extraído en .tools\wasi-sdk-27.0-x86_64-windows)
python tools\check_factory.py build\work\build\web\simulator.wasm   # valida las 16 marchas (pip install wasmtime)
```

Qué hace el script: genera `overlay\app\cofrade_marchas.h` desde `tools\gen_marchas.py`, copia
`vendor\fm1_open` (SDK oficial intacto) a `build\work`, le superpone `overlay\` y retoca el texto del arranque
de `screen.c` (cada ancla se comprueba y falla si el SDK cambia). Después ejecuta el `sdk\Build.ps1` oficial.

### Presupuesto de flash (por qué las marchas son pequeñas)

El SDK permite ≤ 453 921 bytes de aplicación y el firmware oficial ya ocupa 453 576. Este firmware ocupa
**453 896**: sobran **25 bytes**. Por eso las marchas se almacenan comprimidas (compases deduplicados, notas de
16 bits, percusión por líneas de bits) y tienen 3–5 pistas. Para añadir música hay que quitar otra.

Editar marchas: toda la música está en `tools\gen_marchas.py` (notación documentada en su cabecera).

## Estructura

```
Build-Cofrade.ps1      script de compilación
overlay/app/           presets.c (proyectos de fábrica) + cofrade_marchas.h (generado)
tools/                 gen_marchas.py, check_factory.py
vendor/fm1_open/       SDK oficial FM1 Open V14, sin modificar
dist/                  FM1_COFRADE.fwsc + informes
upstream.json          versiones y hashes de lo usado
```

## Licencia

Este proyecto sigue la del SDK: **GPL-3.0-only con la excepción de enlazado del SDK FM1** (ver [`LICENSE.md`](LICENSE.md)
y [`THIRD_PARTY.md`](THIRD_PARTY.md)). Las marchas son originales, publicadas bajo la misma licencia.

*M-VAVE y FM1 son marcas de sus propietarios. Que Dios reparta suerte y el costalero no se duerma.*
