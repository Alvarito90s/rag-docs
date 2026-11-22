# NNN · <título>
Fase: N · Depende de: <specs previas o "ninguna">

## Objetivo
<una o dos frases>

## Archivos
- crear: <ruta>
- modificar: <ruta> (solo <función/sección>)

## Interfaz
<firmas exactas con tipos y docstring de una línea>

## Comportamiento
<reglas numeradas, casos límite incluidos>

## Tests obligatorios
<ruta del test + lista de casos con entrada y salida esperada>

## Referencia de librerías
<fragmentos de documentación oficial, si aplica>

## Aceptación
- [ ] uv run pytest -q tests/<ruta> pasa
- [ ] uv run ruff check . y uv run mypy src sin errores
- [ ] <comprobación funcional con un comando>

## Fuera de alcance
<lo que NO debe tocar>
