# Borrador: post de LinkedIn

> Borrador para publicar a mano. No es parte del proyecto: no lo subas al repo.
> Rellena lo que está entre [corchetes]. Datos comprobados en el repo el 2026-11-23.

## Versión en español

He construido DocuChat Local, una app RAG 100 % local: le preguntas a tus documentos (PDF, DOCX, Markdown) y responde con citas que abren el PDF en la página exacta. Si la respuesta no está, dice "No lo sé". Nada sale del Mac.

Lo interesante no es solo la app, sino cómo se ha hecho. Casi no he escrito código: lo han escrito dos agentes y yo he revisado.

🧠 Un "cerebro" (Claude) escribe una spec por tarea: objetivo, máximo 3 archivos, firmas exactas y tests con valores esperados que el otro agente no puede tocar.
⚙️ Un "ejecutor" (Qwen 3.6 35B, corriendo en local con opencode) implementa cada spec, pasa tests, ruff y mypy, y deja un informe.
👀 El cerebro verifica cada informe ejecutando la suite y probando contra los modelos reales. Si algo no cuadra, escribe una spec de corrección.

En números: 66 specs, 19 de ellas correcciones (las NNN-b), 465 tests y ni una línea de LangChain.

Lo que más me enseñó fue lo que salió al verificar:

🔴 Un test que rompía el índice real. Creaba la configuración sin carpeta temporal, así que cada `pytest` reescribía `data/` con embeddings falsos de 3 dimensiones. La app fallaba después con "expecting embedding with dimension of 3, got 1024". Todos los tests pasaban.

🟡 Tests que fallaban 1 de cada 10-20 veces. El ejecutor los dio por "errores internos de ChromaDB, preexistentes". La causa real: Chroma cachea el cliente por la cadena de la ruta, y con rutas relativas reutilizaba la carpeta de un test anterior ya borrada. Resolver la ruta a absoluta: 0 fallos en 30 ejecuciones.

🟢 Un índice que se creía completo. El registro decía 7 documentos indexados y Chroma tenía 0 chunks; "actualizar" respondía "0 añadidos, 7 sin cambios". Ahora el indexador se repara solo.

Lo que me llevo:
1. Un modelo local pequeño sigue muy bien instrucciones precisas, pero no toma buenas decisiones de diseño. El valor está en separar quién decide y quién ejecuta.
2. Los tests escritos por quien diseña son el contrato. Si el ejecutor puede ajustarlos para que pasen, lo hará: un test que comprobaba el número exacto de páginas acabó como `>= 9`, y hizo falta una spec de corrección para recuperar los tests originales.
3. "Todos los tests pasan" no significa "funciona". Dos de esos bugs salieron al usar la app con los modelos reales, no en la CI.

También hay evaluación reproducible con 42 preguntas: Hit@5 de 1.0, citas correctas al 100 % y las 10 preguntas sin respuesta rechazadas. Y un fallo conocido que dejo documentado: en una pregunta recupera la página correcta y aun así responde "No lo sé".

Código, specs e informes de cada tarea: https://github.com/Alvarito90s/RAG-Docs

#RAG #LLM #LocalLLM #MLX #AIAgents #Python #FastAPI

---

## English version

I built DocuChat Local, a 100% local RAG app: you ask questions about your documents (PDF, DOCX, Markdown) and it answers with citations that open the PDF at the exact page. If the answer isn't there, it says "I don't know". Nothing leaves the Mac.

The interesting part isn't just the app, it's how it was made. I barely wrote any code: two AI agents wrote it, and I reviewed.

🧠 A "brain" (Claude) writes one spec per task: a goal, at most 3 files, exact signatures and tests with expected values the other agent can't touch.
⚙️ An "executor" (Qwen 3.6 35B, running locally through opencode) implements each spec, gets tests, ruff and mypy passing, and writes a report.
👀 The brain checks every report by running the suite and testing against the real models. When something is off, it writes a correction spec.

By the numbers: 66 specs, 19 of them corrections, 465 tests, zero lines of LangChain.

What taught me the most was what turned up during verification:

🔴 A test that broke the real index. It built its config without a temp folder, so every `pytest` run overwrote `data/` with 3-dimensional fake embeddings. The app then failed with "expecting embedding with dimension of 3, got 1024". Every test passed.

🟡 Tests that failed 1 run in 10-20. The executor wrote them off as "pre-existing ChromaDB internal errors". The real cause: Chroma caches its client by the path string, and with relative paths it reused a previous test's folder that had already been deleted. Resolving the path to absolute: 0 failures in 30 runs.

🟢 An index that thought it was complete. The registry listed 7 indexed documents while Chroma held 0 chunks; "update" answered "0 added, 7 unchanged". The indexer now repairs itself.

Takeaways:
1. A small local model follows precise instructions very well, but it doesn't make good design decisions. The value is in separating who decides from who executes.
2. Tests written by the designer are the contract. If the executor can tweak them to pass, it will: a test that checked an exact page count ended up as `>= 9`, and it took a correction spec to restore the original tests.
3. "All tests pass" doesn't mean "it works". Two of those bugs only showed up when using the app with the real models, not in CI.

There's also a reproducible evaluation with 42 questions: Hit@5 of 1.0, 100% correct citations and all 10 unanswerable questions refused. Plus one documented known failure: on one question it retrieves the right page and still answers "I don't know".

Code, specs and per-task reports: https://github.com/Alvarito90s/RAG-Docs

#RAG #LLM #LocalLLM #MLX #AIAgents #Python #FastAPI

---

## Notas para publicar

- Adjunta `docs/demo.gif` (o un vídeo corto): en LinkedIn un post con imagen o vídeo rinde bastante más que solo texto.
- Pon el enlace al repo en el primer comentario si prefieres no penalizar el alcance del post; deja una línea en el texto que diga "enlace en comentarios".
- Si escribes el artículo largo, cada bug da para una sección: síntoma, cómo se encontró, la causa y la spec de corrección (051-b, 024-c y 026-b).
