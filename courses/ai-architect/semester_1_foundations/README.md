# Semester 1 — Foundations of LLMs

## Objetivo del semestre

Que el alumno construya el modelo mental correcto sobre cómo funciona un LLM antes de diseñar ningún sistema. Sin este semestre, el alumno construye sobre supuestos incorrectos que se manifiestan como bugs difíciles de diagnosticar en producción.

Al terminar el Semester 1, el alumno entiende la mecánica real de un LLM —tokens, context windows, temperatura, embeddings, coste— y puede tomar las primeras decisiones de diseño con criterio: cuándo confiar en el output, cuándo añadir verificadores, cuándo usar RAG vs. fine-tuning, y cuánto va a costar el sistema antes de construirlo.

## Audiencia objetivo

Software Engineers con experiencia en sistemas convencionales que nunca han trabajado directamente con LLMs. Conocen APIs, bases de datos, sistemas distribuidos — pero los LLMs son nuevos para ellos.

## Prerequisitos

Ninguno. Este es el punto de entrada al curso.

---

## Lecciones

| # | Título | Objetivo (una línea) | Duración |
|---|--------|----------------------|----------|
| 1.1 | Cómo piensan los LLMs | Entender next-token prediction para saber cuándo necesitas un verificador externo y cuándo no | 7–9 min |
| 1.2 | Tokens y context windows | Desarrollar intuición numérica sobre límites y costes, y saber elegir entre chunking, RAG y summarization | 8–10 min |
| 1.3 | Embeddings para arquitectos | Saber cuándo usar embeddings y cómo elegir entre búsqueda semántica, por keywords e híbrida | 7–9 min |
| 1.4 | Temperatura y determinismo | Elegir el valor de temperatura correcto para cada tipo de tarea y entender su impacto en producción | 6–8 min |
| 1.5 | Fine-tuning vs RAG | Elegir correctamente entre fine-tuning y RAG sin cometer el error de usar fine-tuning para enseñarle hechos al modelo | 8–10 min |
| 1.6 | Prompt engineering para arquitectos | Diseñar system prompts como interfaces tipadas: versionables, testeables, revisables en PR | 7–9 min |
| 1.7 | El coste real de un LLM en producción | Estimar el coste de un sistema LLM antes de diseñarlo para que las decisiones de arquitectura sean económicamente viables | 7–9 min |

---

## Detalle de lecciones

### 1.1 — Cómo piensan los LLMs

**Archivo:** `1.1_como_piensan_los_llms.md`
**Duración:** 7–9 min
**Formato visual:** Excalidraw (diagrama animado por bloques)

**Objetivo:** Al terminar esta lección, el alumno puede explicar qué hace exactamente un LLM cuando procesa texto — y usarlo para decidir cuándo necesita un verificador externo y cuándo no.

**Decisión de diseño:** Cuándo confiar directamente en el output del LLM y cuándo añadir una capa de verificación externa, en función de la reversibilidad y consecuencia del error.

---

### 1.2 — Tokens y context windows: los límites reales

**Archivo:** `1.2_tokens_y_context_windows.md`
**Duración:** 8–10 min
**Formato visual:** Slides PDF (tablas y ejemplos numéricos)

**Objetivo:** Al terminar esta lección, el alumno tiene intuición numérica sobre cuánto cabe en un LLM, cuánto cuesta, y sabe elegir entre chunking, RAG y summarization según el caso.

**Decisión de diseño:** Cómo gestionar contenido que excede la ventana de contexto: chunking, RAG o summarization.

---

### 1.3 — Embeddings para arquitectos

**Archivo:** `1.3_embeddings_para_arquitectos.md`
**Duración:** 7–9 min
**Formato visual:** Excalidraw (espacio semántico 2D)

**Objetivo:** Al terminar esta lección, el alumno sabe cuándo usar embeddings, cuándo no usarlos, y cómo elegir entre búsqueda semántica, búsqueda por keywords y búsqueda híbrida según el caso de uso.

**Decisión de diseño:** Tipo de búsqueda a usar según la naturaleza del contenido y las queries del sistema.

---

### 1.4 — Temperatura y determinismo: cuándo importa

**Archivo:** `1.4_temperatura_y_determinismo.md`
**Duración:** 6–8 min
**Formato visual:** Slides PDF (tabla de decisión)

**Objetivo:** Al terminar esta lección, el alumno sabe exactamente qué valor de temperatura usar para cualquier tipo de tarea, y por qué el determinismo importa en sistemas de producción más allá de la reproducibilidad.

**Decisión de diseño:** Valor de temperatura según el tipo de tarea (extracción, generación creativa, razonamiento, código) y las necesidades de reproducibilidad del sistema.

---

### 1.5 — Fine-tuning vs RAG: la decisión correcta

**Archivo:** `1.5_finetuning_vs_rag.md`
**Duración:** 8–10 min
**Formato visual:** Excalidraw (dos columnas paralelas)

**Objetivo:** Elegir correctamente entre fine-tuning y RAG sin cometer el error más común: usar fine-tuning para enseñarle hechos al modelo.

**Decisión de diseño:** RAG cuando el conocimiento es externo y cambia; fine-tuning cuando el comportamiento o el estilo no se puede codificar en un prompt.

---

### 1.6 — Prompt engineering para arquitectos (no para usuarios)

**Archivo:** `1.6_prompt_engineering_arquitectos.md`
**Duración:** 7–9 min
**Formato visual:** Slides PDF (anatomía anotada + ejemplo completo)

**Objetivo:** Diseñar system prompts como interfaces tipadas, no como instrucciones informales: versionables, testeables, revisables en PR.

**Decisión de diseño:** Qué entra en el system prompt vs. el user prompt, y cómo estructurar el prompt para que sea mantenible como código.

---

### 1.7 — El coste real de un LLM en producción

**Archivo:** `1.7_coste_real_llm_produccion.md`
**Duración:** 7–9 min
**Formato visual:** Slides PDF (calculadora visual + tabla de escenarios)

**Objetivo:** Estimar el coste de un sistema LLM antes de diseñarlo, para que las decisiones de arquitectura sean económicamente viables desde el inicio.

**Decisión de diseño:** Qué palancas de optimización activar según el escenario (prompt caching, modelo más barato, output limitado, arquitectura por capas).

---

## Cierre del Semester 1

**Archivo:** `cierre_diagrama_anatomia_sistema.md`
**Duración:** 4–5 min
**Formato visual:** Excalidraw complejo (diagrama de arquitectura completo)

Construye en directo el diagrama de anatomía de un sistema LLM real, mostrando cómo los 7 conceptos del semestre se integran: usuario → interfaz → constructor de prompt → recuperación (embeddings/RAG) → LLM (temperatura, tokens, context window) → verificador → respuesta. El diagrama queda como referencia visual para los semestres siguientes.

## Diagrama de cierre del semestre

```
Usuario
  └─► Interfaz / API
        └─► Constructor de prompt
              ├─► Recuperación (embeddings, RAG, chunking)
              │     └─► Vector store / Knowledge base
              └─► LLM
                    ├─► Temperatura → sampling
                    ├─► Context window → límite de tokens
                    └─► Output
                          └─► Verificador (cuando la consecuencia lo exige)
                                └─► Respuesta final
```

**Eje transversal:** Coste (tokens de entrada + tokens de salida) × volumen de llamadas.

## Notas de producción

- Cada lección termina con una decisión de diseño concreta, no con teoría abierta. El alumno sale con un criterio aplicable.
- Las lecciones 1.1, 1.2 y 1.7 forman la base económica y de límites — conviene grabarlas con ejemplos numéricos actualizados (precios de API cambian).
- La lección 1.5 (Fine-tuning vs RAG) es la que más confusión genera en el sector; es crítico que el diagrama comparativo sea claro.
- El cierre debe grabarse después de que todos los diagramas individuales estén finalizados, para que el diagrama de anatomía pueda referenciarlos visualmente.
- Los precios de modelos en la lección 1.7 necesitarán revisión periódica (cada 6 meses aproximadamente).
