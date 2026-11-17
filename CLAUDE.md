# lastfm_scrobbles

- `extraer_scrobbles.py`: descarga Last.fm + ListenBrainz a `LASTFM_DB` y exporta los dos JSON. Es incremental (`sync_state`) y guarda cada `SAVE_EVERY` páginas.
- `server.py`: `/api/jobs/run`, `/health` y la sincronización periódica opcional (`SYNC_EVERY_HOURS`).
- El esquema de `scrobbles`, `artists` y `albums` lo leen otros servicios (ya_lo_tengo, lastfm_explorer, dieta_sonora): no renombrar columnas sin cambiarlos a ellos.
- Las credenciales llegan por entorno (`.env.example`); `sops_env.py` es solo para uso fuera de Docker.
