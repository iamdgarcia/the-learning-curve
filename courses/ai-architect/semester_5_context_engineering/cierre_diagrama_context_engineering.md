# Cierre del Semestre 5 — Diagrama: El sistema completo de Context Engineering

**Semestre:** 5 — Context Engineering
**Tipo:** Diagrama de cierre de semestre
**Formato visual:** Excalidraw (mapa arquitectónico completo)

---

## Propósito del diagrama

Este diagrama integra todas las lecciones del Semestre 5 en una arquitectura cohesiva. El alumno ve cómo las cinco capas del contexto, el pipeline RAG, la gestión de memoria, las defensas y la evaluación forman un sistema diseñado intencionalmente — no un conjunto de piezas sueltas.

Es el artefacto que el AI Architect puede llevar a una revisión de diseño y explicar en 5 minutos.

---

## Descripción del diagrama

El diagrama tiene cuatro zonas horizontales apiladas verticalmente, conectadas por flechas de flujo.

---

### Zona 1 — Fuentes de conocimiento (arriba)

Tres bloques horizontales en la zona superior:

- **Documentos base** — `PDFs, wikis, bases de conocimiento, código`
- **Datos dinámicos** — `APIs, bases de datos, resultados de herramientas`
- **Memoria de usuario** — `preferencias, historial de sesiones, perfil`

Cada bloque apunta hacia abajo a la Zona 2.

---

### Zona 2 — Pipeline RAG y gestión de memoria (centro-superior)

Esta es la zona más densa, con dos sub-pipelines paralelos:

**Sub-pipeline izquierdo — Ingestión (offline):**
```
Documentos → Chunking (fixed / semantic / hierarchical) → Embedding model → Vector DB
```
Anotaciones:
- En Chunking: `"estrategia según densidad semántica del documento"`
- En Embedding: `"mismo modelo en ingest y query"`
- En Vector DB: `"pgvector / Qdrant / Pinecone"`

**Sub-pipeline derecho — Query (runtime):**
```
User query → Embedding → Similarity search (top-20) → Reranker (top-5) → Context injection
```
Anotaciones:
- En Similarity search: `"bi-encoder: rápido, amplio"`
- En Reranker: `"cross-encoder: lento, preciso"`
- En Context injection: `"capa 3 del contexto"`

**Bloque de memoria jerárquica (derecha, paralelo al pipeline):**
```
[COLD: archivo] ↔ [WARM: resúmenes + preferencias, vector DB] ↔ [HOT: en contexto]
```
Con flecha hacia Context injection indicando: `"se recupera por relevancia"`

---

### Zona 3 — Las cinco capas del contexto (centro)

Bloque central: stack vertical con las cinco capas en colores distintos:

```
┌─────────────────────────────────┐
│ [1. System prompt]              │  ← fijo, raramente cambia
│ [2. Few-shot examples]          │  ← fijo o semi-fijo
│ [3. Retrieved documents] ◄──────┼── desde pipeline RAG + memoria warm
│ [4. Conversation history]       │  ← compresión activa si sesión larga
│ [5. Tool results]               │  ← normalizado antes de inyectar
└─────────────────────────────────┘
```

Anotación lateral izquierda: `"User prompt: solo el 2-10% del total"`

Anotación lateral derecha indicando flujos de compresión:
- `"History > threshold → summarización → resumen reemplaza historial"`
- `"Tool results → normalizar y truncar antes de inyectar"`

---

### Zona 4 — Defensas y evaluación (abajo)

Dos bloques paralelos en la zona inferior:

**Bloque izquierdo — Defensas:**
- `[Sandbox de contexto]` — `"separación instrucciones / datos externos"`
- `[Validación de input]` — `"filtro antes de inyectar contenido externo"`
- `[Mínimo privilegio]` — `"agentes solo con las herramientas que necesitan"`
- `[Anclas de contexto]` — `"refuerzo periódico del rol y restricciones"`
- Etiqueta: `"contra: poisoning + drift"`

**Bloque derecho — Evaluación:**
- `[Golden dataset]` → `[Evaluación offline]` → `[CI gate]`
- Métricas RAG: `"Faithfulness | Context Precision | Context Recall"`
- Métricas agentes: `"Goal completion | Context utilization"`
- Monitorización: `"tokens por capa | latencia | anomalías"`
- Etiqueta: `"sin evaluación = intuición, con evaluación = ingeniería"`

---

### Conectores transversales

- Flecha desde `[LLM]` (implícito, entre zona 3 y el output) hacia `[Evaluación offline]`: `"LLM-as-a-judge"`
- Flecha desde `[Monitorización]` hacia `[Golden dataset]`: `"incidentes → ampliar dataset"`
- Flecha desde `[Compresión de historial]` retroalimentando a zona 3: `"historial limpio = menos drift"`

---

## Spec del diagrama Excalidraw

**Tipo:** Excalidraw
**Dimensiones:** ancho amplio (landscape), cuatro filas horizontales
**Paleta:**
- Zona 1 (fuentes): gris suave
- Zona 2 (pipeline): azul suave para ingestión, verde suave para query
- Zona 3 (capas): colores por capa (naranja, amarillo, azul, verde, púrpura)
- Zona 4 (defensas): rojo suave izquierda, verde suave derecha

**Anotaciones clave a mantener visibles simultáneamente:**
- `"Mismo modelo: ingest y query"` en el pipeline
- `"2-10% del contexto = prompt del usuario"` junto a las capas
- `"Sin evaluación = intuición"` en la zona de evaluación

**Flujo visual en presentación:** el diagrama se presenta completo como imagen de cierre. El presentador recorre de arriba a abajo explicando cómo cada zona conecta con la anterior. Se puede usar como referencia de diseño durante el desarrollo de un sistema real.

---

## Texto de cierre del semestre (para grabar)

Esto es lo que construye un AI Architect cuando diseña un sistema de context engineering.

Empezamos por el conocimiento: documentos, datos dinámicos, memoria de usuario. Los procesamos con un pipeline RAG que elige la estrategia de chunking correcta para cada tipo de documento y añade reranking para aumentar la precisión del retrieval.

Ese conocimiento procesado entra como una de las cinco capas del contexto — junto al system prompt, los few-shots, el historial comprimido activamente, y los resultados de herramientas normalizados.

El contexto que construimos tiene defensas: separación entre instrucciones y datos externos, validación antes de inyectar, mínimo privilegio para los agentes con herramientas de alto impacto.

Y todo esto se evalúa: con un golden dataset, con métricas de faithfulness y context precision para RAG, con goal completion rate para agentes, y con monitorización continua en producción.

El prompt del usuario — lo que parece lo más importante — es el 2-10% de este sistema. El resto es context engineering.

---

## Notas de producción

**Para la grabación:**
- Este diagrama se muestra al final de la lección de cierre del Semestre 5.
- Presentar primero el diagrama completo durante 20-30 segundos sin hablar — que el alumno lo absorba visualmente.
- Luego recorrerlo de arriba a abajo siguiendo el flujo natural.
- El cierre verbal es la última sección: "El prompt del usuario es el 2-10%..." — es el remate de todo el semestre.

**Conexiones con otros semestres:**
- Zona 3 (capas) amplía la Lección 1.2 (tokens y context windows) del Semestre 1.
- El pipeline RAG conecta con los pipelines de Semestre 2.
- Las defensas de agentes conectan con el Semestre 3 (verifiers, supervisores).
- La memoria distribuida conecta con el Semestre 4 (distributed context, 4.7).
