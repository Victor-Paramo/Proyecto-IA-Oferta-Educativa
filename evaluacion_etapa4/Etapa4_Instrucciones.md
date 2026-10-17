# Etapa 4 — Protocolo de evaluación integral

**Objetivo:** evaluar el comportamiento del asistente con **30 preguntas distribuidas en seis sesiones**. Son pruebas del *sistema completo*, no únicamente de la exactitud del clasificador. Las preguntas se eligieron sin repetir literalmente las 136 de entrenamiento ni las 40 del diagnóstico ampliado.

## Cómo ejecutar

1. Guarda el estado de tu proyecto y **no cambies todavía el código ni los datos de entrenamiento**.
2. En PowerShell, desde `C:\\Users\\Admin\\Desktop\\ProyectoIA`, ejecuta:

   ```powershell
   .\\.venv\\Scripts\\python.exe app.py
   ```

3. Ejecuta las **cinco preguntas de la sesión 1** en orden. Anota en la columna **Respuesta observada** lo que respondió realmente.
4. Marca cada turno como `Correcto`, `Parcial` o `Incorrecto`; deja `Sin evaluar` mientras no lo hayas probado. Apunta errores y su gravedad.
5. Escribe `salir` y vuelve a iniciar `app.py` para pasar a la sesión siguiente. **No cambies el código entre sesiones**.
6. Al terminar, comparte el Excel o CSV con los resultados. Calcularemos los indicadores y priorizaremos errores.

## Rúbrica

| Resultado | Significado | Puntaje provisional |
|---|---|---:|
| Correcto | Intención y resultado final coherentes, datos respaldados, contexto correcto | 1 |
| Parcial | Respuesta útil, pero con una omisión o un fallo no crítico | 0.5 |
| Incorrecto | Respuesta no pertinente, inventada, filtro equivocado o contexto perdido | 0 |

**Importante:** no evalúes una pregunta solo por el nombre de la intención que predice el modelo. Revisa también la respuesta final. Los saludos, despedidas y consultas fuera de alcance son comportamientos deseados del **asistente**, aunque el clasificador actual solamente tenga cuatro clases.

No se conocen por adelantado los números de ofertas para todas las preguntas: se comprobarán con los datos reales de PostgreSQL, evitando inventar cifras. La fuente son documentos SEP de abril de 2021, por lo que no se garantiza vigencia en 2026.

## Archivos

- `Etapa4_Evaluacion_Integral_30_Preguntas.xlsx`: hoja editable con rúbrica, 30 turnos y resumen automático.
- `Etapa4_Preguntas_Pruebas.csv`: versión CSV para conservar evidencia y subir a Git posteriormente.

**No hagas aún un nuevo commit:** primero registra los resultados originales. Si aparecen errores, los corregiremos después y volveremos a evaluar con consultas distintas.
