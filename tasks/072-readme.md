# 072 · README
Fase: 7 · Depende de: 071

## Objetivo
Sustituir el README provisional por el definitivo (lo ha escrito el cerebro) y proteger con tests lo que en él puede quedarse desfasado: los resultados, los comandos, los enlaces y las variables.

## Archivos
- modificar (copia exacta): `README.md` ← `tasks/assets/072/README.md` (NO lo edites)
- crear: `tests/test_readme.py`

## Comportamiento
1. `README.md` queda idéntico byte a byte al asset.
2. El GIF `docs/demo.gif` lo graba el humano (ver Aceptación). Hasta entonces el enlace está roto, y el test de enlaces lo deja como única excepción.

## Tests obligatorios
`tests/test_readme.py`. NO cambies los valores esperados. `ROOT = Path(__file__).resolve().parents[1]`, `README = (ROOT / "README.md").read_text("utf-8")`, `RESULTS = (ROOT / "eval" / "results.md").read_text("utf-8")`. Ningún test llama a oMLX.

1. **Copia exacta.** Los bytes de `README.md` son iguales a los de `tasks/assets/072/README.md`.
2. **Tabla de recuperación al día.**
   - Las líneas de `RESULTS` que cumplen `re.match(r"\| (500|800|1200) \|", línea)` son 9.
   - Todas están entre las líneas de `README`.
3. **Tabla de generación al día.**
   - Se toman las líneas de `RESULTS` desde `"| Métrica | Valor |"` hasta la primera línea vacía, sin incluirla. Son 9.
   - Todas están entre las líneas de `README`.
4. **Comandos reales.**
   - El conjunto `set(re.findall(r"(?:uv run |`)docuchat ([a-z]+)", README))` es exactamente `{"ingest", "search", "ask", "serve"}`.
   - Es subconjunto de `set(typer.main.get_command(app).commands)`, con `app` de `docuchat.cli`.
5. **Enlaces locales.**
   - Se toman los enlaces de `re.findall(r"\]\(([^)#\s]+)\)", README)` que no empiezan por `http`.
   - Cada uno existe (`(ROOT / enlace).exists()`), salvo los de `PENDIENTES = {"docs/demo.gif"}` (comentario: lo graba el humano).
   - Hay al menos 9 enlaces comprobados.
6. **Variables reales.**
   - Los nombres de `re.findall(r"DOCUCHAT_([A-Z_]+)", README)`, en minúsculas, son subconjunto de `set(Settings.model_fields)`.
   - Hay al menos 8 distintos.
7. **Rutas de la API reales.** Cada ruta de `re.findall(r"\| (?:GET|POST) \| `([^`]+)`", README)` está en `set(create_app(settings).openapi()["paths"])`.
   - Las encontradas son 7.
   - Prepara `settings` como en el test 4 de `tests/test_ci_workflow.py`.

## Aceptación
- [ ] `uv run pytest -q tests/test_readme.py` → 7 passed
- [ ] `uv run pytest -q` pasa entero (459)
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `cmp README.md tasks/assets/072/README.md` → sin salida
- [ ] (humano) Graba el GIF de unos 15–20 s:
  1. Con `uv run docuchat serve`, haz una pregunta y pulsa una cita para que se abra el PDF en su página.
  2. Graba la pantalla con Cmd+Shift+5 → `demo.mov`.
  3. Convierte el vídeo con `brew install ffmpeg` y
     `ffmpeg -i demo.mov -vf "fps=12,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" -loop 0 docs/demo.gif`.
  4. Objetivo: menos de 5 MB.

## Fuera de alcance
No cambies ningún otro archivo. Si un test falla porque el README no cuadra con el código, para y explícalo en "Bloqueos": no edites el README.
