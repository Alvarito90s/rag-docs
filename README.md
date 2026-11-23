# DocuChat Local

Pregunta a tus documentos en local, con citas a la página exacta. Sin enviar nada a la nube.

## Evaluación

Evaluación real con Qwen3.6-35B-A3B y 42 preguntas (32 respondibles, 10 sin respuesta):

- **Hit@5**: 1.000 (todos los aciertos en el top 5)
- **Precisión de citas**: 1.000
- **Rechazo correcto**: 1.000
- **1 falso rechazo conocido**: la pregunta **q17** (sobre el error E-17 del manual de cafetera) devuelve "No lo sé" en lugar de la respuesta. La información está en los chunks recuperados pero el modelo no la extrae.

> En construcción.