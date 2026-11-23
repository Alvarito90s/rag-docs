# 071 · CI: construir y arrancar la imagen
Fase: 7 · Depende de: 070

## Objetivo
Añadir a la CI un job que construya la imagen Docker, la arranque y compruebe `/api/health`. Así la imagen se prueba en cada push aunque nadie tenga Docker en local.

## Archivos
- modificar: `.github/workflows/ci.yml` (solo AÑADIR el job `docker` al final; el job `check` no cambia)
- crear: `tests/test_ci_workflow.py`

## Contenido exacto
Añade al final de `ci.yml`, al mismo nivel de sangría que `check:` (dos espacios) y dejando una línea en blanco antes:
```yaml
  docker:
    runs-on: ubuntu-latest
    needs: check
    steps:
      - uses: actions/checkout@v7
      - name: Construir imagen
        run: docker build -t docuchat:ci .
      - name: Arrancar y comprobar /api/health
        run: |
          docker run -d --name docuchat -p 127.0.0.1:8001:8001 docuchat:ci
          for i in $(seq 1 30); do
            if curl -fsS http://127.0.0.1:8001/api/health; then exit 0; fi
            sleep 1
          done
          docker logs docuchat
          exit 1
```
La app arranca y `/api/health` responde sin servidor de modelos (comprobado por el cerebro), así que el job no necesita oMLX.

## Tests obligatorios
`tests/test_ci_workflow.py`. NO cambies los valores esperados. Solo texto: nada de `pyyaml`. `CI = ROOT / ".github" / "workflows" / "ci.yml"`.
1. El job `check` sigue completo: el texto contiene `"uv run pytest -q"`, `"uv run mypy src"` y `"uv sync --locked"`.
2. Existe el job `docker`: contiene la línea `"  docker:"` (dos espacios), `"needs: check"` y `"docker build -t docuchat:ci ."`.
3. El job `docker` va después de `check`: `text.index("  check:") < text.index("  docker:")`.
4. La comprobación usa la ruta real: contiene `"http://127.0.0.1:8001/api/health"`, y `"/api/health"` es una ruta de la app (`"/api/health" in set(create_app(settings).openapi()["paths"])`). Prepara `settings` en el propio test, porque las fixtures de `tests/api/conftest.py` no llegan a este archivo:
   - borra las variables `DOCUCHAT_*` con `monkeypatch.delenv`;
   - `monkeypatch.chdir(tmp_path)`;
   - `settings = Settings(data_dir=tmp_path / "data")`.

   `create_app` no llama al servidor de modelos.
5. Sin tabuladores: `"\t" not in text`.

## Aceptación
- [ ] `uv run pytest -q tests/test_ci_workflow.py` → 5 passed
- [ ] `uv run pytest -q` pasa entero (452)
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] (humano) tras el push, en GitHub Actions los jobs `check` y `docker` salen en verde

## Fuera de alcance
No cambies el job `check` ni añadas publicación de la imagen en un registro.
