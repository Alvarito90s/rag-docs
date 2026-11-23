# 082-b · Poner al día docs/STATE.md tras 080–082
Fase: 8 · Depende de: 082

## Objetivo
El código de 080, 081 y 082 está aprobado, pero `docs/STATE.md` quedó mal: la 082 no lo actualizó (paso 4 de "Cómo trabajar una tarea" en `AGENTS.md`) y hay un error de texto. Esta spec solo corrige ese archivo.

Precondición: el humano ya ha hecho commit de 080–082, así que el árbol de trabajo está limpio al empezar.

## Archivos
- modificar: `docs/STATE.md` (solo las líneas indicadas)

## Interfaz
Ninguna. No se toca código ni tests.

## Comportamiento
1. Cabecera, línea "Fase actual": el nombre de la fase es `8 · Deuda y evaluación v2`, no `8 · Depuración`. El resto de la línea (66 specs y la lista) se queda igual, añadiendo `082-b` al final de la lista. El total pasa a 67.
2. Línea "Última spec completada": `082-b-state-al-dia`.
3. En "Qué falta en la fase actual", la línea de la spec 080 contiene el texto `formato移入` (caracteres chinos colados). Sustitúyelo por `formato movidas a`, de modo que quede `6 funciones de formato movidas a \`cli_format.py\``.
4. En esa misma sección, cambia la etiqueta `Fase 8 · Depuración` por `Fase 8 · Deuda y evaluación v2`.
5. Añade, justo después de la línea de la spec 081, esta línea exacta:
   `- Spec 082 completada: campo \`category\` en \`EvalQuestion\` (por defecto \`general\`, patrón \`^[a-z_]+$\`) + \`eval/questions_v2.jsonl\` (80 preguntas sobre samples_v2: 70 con respuesta, 10 sin ella, 8 categorías de 10) + \`tests/evaluation/test_dataset_v2.py\` (12 tests). Pendiente en la fase 8: specs 083–086 y la puerta H1 (línea base con oMLX).`
6. En "Qué funciona", la línea de pytest pasa a ser exactamente: `- \`uv run pytest -q\` → 509 passing (497 + 12 de preguntas v2)`.
7. Tabla de módulos, fila `report`: `✅ 68 informes` (los 67 que hay en `reports/` sin contar `_TEMPLATE.md`, más el de esta spec).
8. Tabla de módulos, fila `evaluation`: añade al final de la celda de estado, antes del `|` de cierre, el texto ` · \`082\`: campo \`category\` + \`questions_v2.jsonl\` + 12 tests`. Añade `tests/evaluation/test_dataset_v2.py` a la lista de archivos de esa fila.
9. No cambies nada más del archivo.

## Tests obligatorios
Ninguno nuevo: es una corrección de documentación. La suite tiene que seguir en 509.

## Aceptación
- [ ] `grep -c "Depuración" docs/STATE.md` → `0`
- [ ] `uv run python -c "import re,sys; t=open('docs/STATE.md',encoding='utf-8').read(); sys.exit(1 if re.search(r'[一-鿿]', t) else 0)"` → código de salida 0
- [ ] `grep -c "509 passing" docs/STATE.md` → `1`
- [ ] `grep -c "Spec 082 completada" docs/STATE.md` → `1`
- [ ] `grep -c "68 informes" docs/STATE.md` → `1`
- [ ] `git diff --stat` solo muestra `docs/STATE.md` (y el informe nuevo aparece como archivo sin seguir)
- [ ] `uv run pytest -q` → 509 passed

## Fuera de alcance
Cualquier archivo que no sea `docs/STATE.md`, salvo el informe `reports/082-b-state-al-dia.md`. No reescribas ni reordenes otras secciones.
