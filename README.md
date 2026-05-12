# Scraper @AMULTIMEDIATV

Scripts para descargar los audios del canal de YouTube `@AMULTIMEDIATV`, generar un índice JSON y preparar un dataset de MP3.

## Qué hace

- Descarga el canal completo con `yt-dlp`.
- Extrae el audio en MP3 y lo guarda por `video id` en `mp3_by_id/{id}.mp3`.
- Registra la metadata bruta en `index_raw.jsonl`: `id`, `title`, `duration` y ruta esperada.
- Genera `index.json` con los MP3 que existen en disco.
- Opcionalmente elimina audios demasiado cortos y genera `index_limpio.json`.
- Opcionalmente filtra audios sin voz hablada con `faster-whisper`.

## Requisitos

- Python 3.10+.
- `yt-dlp` disponible en `PATH`.
- `ffmpeg` disponible en `PATH`.
- Node.js, requerido por la configuración de `yt-dlp` usada para YouTube.
- Para el filtro de voz: `faster-whisper`.

Instalación rápida:

```powershell
pip install yt-dlp faster-whisper
```

`ffmpeg` y Node.js deben instalarse aparte si no están ya disponibles en el sistema.

## Ejecución recomendada

El flujo se puede lanzar desde un único script Python. Sin parámetros, pregunta qué acción ejecutar:

```powershell
python .\run_pipeline.py
```

Para descargar, generar índice y limpiar audios de menos de 60 segundos:

```powershell
python .\run_pipeline.py all --cookies-from-browser chrome
```

Con un fichero de cookies exportado:

```powershell
python .\run_pipeline.py all --cookies-file C:\ruta\youtube-cookies.txt
```

El filtro de voz es más lento y se deja como paso explícito:

```powershell
python .\run_pipeline.py voice --source index_limpio.json --output index.json
```

También puede añadirse al flujo completo:

```powershell
python .\run_pipeline.py all --cookies-from-browser chrome --with-voice
```

## Comandos disponibles

```powershell
python .\run_pipeline.py download --cookies-from-browser chrome
python .\run_pipeline.py index
python .\run_pipeline.py clean --min-duration 60
python .\run_pipeline.py voice --source index_limpio.json --output index.json
python .\run_pipeline.py all --cookies-file C:\ruta\youtube-cookies.txt
```

El script PowerShell `download_channel.ps1` se conserva como alternativa manual para la descarga.

## Salidas

- `mp3_by_id/{id}.mp3`: audios descargados.
- `index_raw.jsonl`: metadata emitida por `yt-dlp` durante la descarga.
- `index.json`: índice final o índice filtrado por voz, según el último paso ejecutado.
- `index_limpio.json`: índice tras eliminar audios por debajo de la duración mínima.
- `download_archive.txt`: histórico usado por `yt-dlp` para no redescargar vídeos.
- `voice_filter_decisions.tsv`: decisiones del filtro de voz.
- `voice_validation_sample.tsv`: muestra de validación del filtro de voz.

## Cookies

Para descargar desde YouTube puede ser necesario usar cookies de una sesión válida. Cada usuario debe generar su propio fichero de cookies, por ejemplo con `Get cookies locally` u otra extensión similar para Chrome, y pasarlo al script:

```powershell
python .\run_pipeline.py all --cookies-file C:\ruta\youtube-cookies.txt
```

También se puede intentar leerlas directamente desde el navegador:

```powershell
python .\run_pipeline.py all --cookies-from-browser chrome
```

No se incluye ningún fichero de cookies en el proyecto.

## Referencia

- Por favor, cita este repositorio usando la siguiente referencia:
```
@misc{scraper_amultimediatv,
author       = {Garc\'ia Cerd\'a, Ra\'ul and Mu{\~n}oz Guillena, Rafael},
  title        = {AMULTIMEDIATV scraper}, 
  year         = {2026},
  institution  = {Language and Information Systems Group (GPLSI) and Centro de Inteligencia Digital (CENID), University of Alicante (UA)},
  howpublished = {\url(https://github.com/gplsi/scraper-amultimediatv/)}
}
```

## Financiación

Este trabajo está financiado por el Ministerio para la Transformación Digital y de la Función Pública, cofinanciado por la UE - NextGenerationEU, en el marco del proyecto Desarrollo de Modelos ALIA.

## Agradecimientos

Expresamos nuestro agradecimiento a todas las personas e instituciones que han contribuido al desarrollo de este recurso.

Agradecimientos especiales a:

[Proveedores de datos]

[Proveedores de soporte tecnológico]

Asimismo, reconocemos las contribuciones financieras, científicas y técnicas del Ministerio para la Transformación Digital y de la Función Pública – Financiado por la UE – NextGenerationEU dentro del marco del proyecto Desarrollo de Modelos ALIA.

## Aviso legal

Tenga en cuenta que los datos pueden contener sesgos u otras distorsiones no deseadas. Cuando terceros desplieguen sistemas o presten servicios basados en estos datos, o los utilicen directamente, serán responsables de mitigar los riesgos asociados y de garantizar el cumplimiento de la normativa aplicable, incluida aquella relacionada con el uso de la Inteligencia Artificial.

La Universidad de Alicante, como propietaria y creadora del conjunto de datos, no será responsable de los resultados derivados del uso por parte de terceros.

## Licencia

Este proyecto se distribuye bajo la licencia Apache 2.0.
