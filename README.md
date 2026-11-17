# lastfm_scrobbles

Descarga todo tu historial de escuchas de **Last.fm** y de **ListenBrainz**, quita los duplicados entre los dos y lo guarda en una base SQLite (`lastfm_stats.db`) que otros programas pueden leer sin volver a pedírselo a la API.

- **Incremental y reanudable:** la primera vez baja todo (con un historial largo, puede llevar un buen rato); después solo lo nuevo. Si se corta, sigue donde iba.
- **Sin duplicados:** la misma canción del mismo artista en un margen de 2 minutos es una sola escucha. Si está en los dos servicios, se queda la de Last.fm.
- **Géneros:** los de cada artista, de Last.fm y MusicBrainz.
- **Resúmenes en JSON:** `lastfm_stats.json` (totales, tops, escuchas por mes, hora y día de la semana) y `lastfm_detail.json` (detalle por artista, disco y género), listos para una web de estadísticas.

## Instalación

Necesitas Docker y al menos una cuenta (Last.fm o ListenBrainz). Para Last.fm hace falta una [API key](https://www.last.fm/api/account/create).

```bash
git clone https://github.com/volteret4/lastfm_scrobbles.git && cd lastfm_scrobbles && cp .env.example .env
```

Rellena `.env` y arranca:

```bash
mkdir -p datos && docker compose up -d --build
```

**Actualización automática:** el compose trae su propia [Ofelia](https://github.com/mcuadros/ofelia), que lanza `extraer_scrobbles.py` cada noche a las 00:00 (trabajo `lastfm-scrobbles-daily`, el mismo horario que en REPEAT-ONE). Para cambiar la hora, edita la etiqueta `ofelia.job-exec.lastfm-scrobbles-daily.schedule` (`seg min hora día mes día-semana`); para desactivarla, `docker compose stop ofelia`. Esta Ofelia solo ve los contenedores de este repo y necesita el socket de Docker en solo lectura. El resultado de cada ejecución se ve en su log:

```bash
docker compose logs -f ofelia
```

Si prefieres no usar Ofelia, `SYNC_EVERY_HOURS=24` hace que el propio servicio sincronice al arrancar y cada 24 horas.

Para sincronizar a mano en cualquier momento:

```bash
curl -X POST -H 'Content-Type: application/json' -d '{"job":"lastfm-scrobbles-daily"}' http://127.0.0.1:8797/api/jobs/run
```

Sin Docker:

```bash
pip install -r requirements.txt && python3 extraer_scrobbles.py
```

## La base de datos

| Tabla | Contenido |
|---|---|
| `scrobbles` | Una fila por escucha: `artist_id`, `album_id`, `track`, `ts` (Unix), `ts_iso`, `source` (`lastfm` o `listenbrainz`) |
| `artists` | `name`, `name_normalized`, `mbid` |
| `albums` | `artist_id`, `name`, `mbid` |
| `genres`, `artist_genres` | Géneros de cada artista |
| `sync_state` | Por dónde va cada servicio |

Ejemplo: tus 10 discos más escuchados.

```bash
sqlite3 datos/lastfm_stats.db "SELECT ar.name, al.name, COUNT(*) n FROM scrobbles s JOIN albums al USING(album_id) JOIN artists ar ON ar.artist_id = al.artist_id GROUP BY album_id ORDER BY n DESC LIMIT 10"
```

Otros programas deben abrirla en solo lectura: en Docker, montando la carpeta con `:ro`.

## Quién la usa

- [ya_lo_tengo](https://github.com/volteret4/ya_lo_tengo): el icono ♫ de «cuántas veces lo has escuchado».
- [lastfm_explorer](https://github.com/volteret4/lastfm_explorer): buscador de tu historial por fecha, género, sello…
- [dieta_sonora](https://github.com/volteret4/dieta_sonora): sus estadísticas.

Es un módulo de [REPEAT-ONE](https://volteret4.github.io/repeat-one-web/), y funciona igual por separado.

## Variables

| Variable | Para qué |
|---|---|
| `LASTFM_API_KEY`, `LASTFM_USERNAME` | Last.fm |
| `LB_USERNAME`, `LB_TOKEN` | ListenBrainz (token solo si es privado) |
| `MB_CONTACT` | Contacto para MusicBrainz, que lo pide en cada consulta |
| `SYNC_EVERY_HOURS` | Sincronización sin Ofelia, cada N horas (0, por defecto, la desactiva) |
| `LASTFM_DB`, `LASTFM_JSON`, `LASTFM_DETAIL_JSON` | Dónde se escriben (en Docker, en `/data`) |

Si prefieres no tener las claves en claro, `sops_env.py` descifra un `.encrypted.env` hecho con [SOPS](https://github.com/getsops/sops) al lanzarlo fuera de Docker.
