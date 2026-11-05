# Semester 2 — AI Engineering

## Objetivo del semestre

Pasar de entender los LLMs como objeto de estudio a usarlos como componente fiable de un sistema real.

Al terminar el Semester 2, el alumno puede tomar las decisiones de diseño clave de cualquier pipeline de IA en producción: cuándo usar un LLM (y cuándo no), cómo estructurar outputs, qué tipo de memoria aplicar en cada caso, cómo estandarizar el acceso a herramientas con MCP, cómo optimizar costes con caching, y cómo saber si el sistema funciona.

## Prerequisitos

Semester 1 — Foundations of LLMs. Sin ese contexto, las decisiones de diseño de este semestre no tienen base.

---

## Lecciones

### 2.1 — Cuándo usar un LLM y cuándo código tradicional

**Objetivo:** Tomar la decisión arquitectónica más ignorada en sistemas con IA: cuándo un LLM es la herramienta correcta y cuándo no lo es.

**Decisión de diseño:** Si la tarea es determinista, exacta o de alto volumen repetitivo → código. Si requiere comprensión de lenguaje natural, razonamiento difuso o generalización → LLM.

---

### 2.2 — Structured outputs y function calling

**Objetivo:** Diseñar la capa de salida del LLM como una interfaz tipada que el resto del sistema puede consumir de forma fiable, en lugar de texto libre que hay que parsear.

**Decisión de diseño:** Cuándo usar structured outputs (JSON schema) y cuándo function calling; cómo añadir una capa de validación que el sistema downstream pueda confiar.

---

### 2.3 — Tipos de memoria en sistemas de IA

**Objetivo:** Elegir el tipo de memoria correcto para cada caso de uso sin sobreingenierizarlo.

**Decisión de diseño:** Cuatro tipos — in-context, cached, external retrieval (RAG) y persistent store — con un árbol de decisión para seleccionar el correcto según longitud de conversación, tipo de dato y coste tolerable.

---

### 2.4 — MCP: qué resuelve arquitectónicamente

**Objetivo:** Entender MCP como estándar de integración entre modelos y herramientas, y saber cuándo construir un servidor MCP propio frente a una integración directa.

**Decisión de diseño:** Si más de un agente o modelo necesita la misma herramienta → servidor MCP. Si es una integración puntual para un solo agente → integración directa.

---

### 2.5 — Caching de prompts y optimización de costes

**Objetivo:** Estructurar prompts para maximizar el cache hit rate y entender cuándo añadir caching semántico.

**Decisión de diseño:** Orden correcto del prompt (estático arriba, dinámico abajo) como optimización obligatoria en producción; caching semántico como optimización opcional cuando hay alta repetición de queries.

---

### 2.6 — Evaluación básica: cómo sabes si tu sistema funciona

**Objetivo:** Definir qué significa "funciona" para un sistema LLM, construir un golden dataset inicial, y saber qué método de evaluación aplicar en cada contexto.

**Decisión de diseño:** Heurísticas programáticas siempre activas en producción; LLM-as-a-judge para evaluación de regresión; evaluación humana para el golden dataset inicial y para calibrar el juez.

---

### Cierre del Semester 2

**Formato:** Lección de síntesis con el diagrama de cierre construido en pantalla.

**Objetivo:** Integrar los seis conceptos del semestre en un único pipeline de referencia que muestre cómo se relacionan entre sí y qué decide cada componente.

---

## Diagrama de cierre del semestre

**Título:** Pipeline de IA — Semester 2 completo

**Elementos del diagrama (de izquierda a derecha):**
1. Input del usuario
2. Árbol de decisión LLM vs. código (L2.1)
3. Construcción del prompt — partes estáticas cacheadas / partes dinámicas (L2.5)
4. Capa de memoria — in-context o RAG path según longitud (L2.3)
5. LLM
6. Salida: structured output o function calling (L2.2)
7. Servidores MCP para herramientas compartidas (L2.4)
8. Evaluación — heurísticas / LLM-as-a-judge / humanos + golden dataset (L2.6)
9. Métricas → decisión de release / iteración

Cada componente anotado con su coste operativo y su punto de fallo más frecuente.

---

## Notas de producción

- La lección 2.1 es la más contraintuitiva: los alumnos esperan aprender a usar LLMs, no a cuándo no usarlos. Vale la pena insistir en la trampa del "es más fácil de implementar".
- La lección 2.3 (memoria) introduce RAG como patrón de external retrieval, no como tema central. El foco está en la decisión de qué tipo usar, no en los detalles de implementación del vector store.
- La lección 2.4 (MCP) es la más nueva en términos de ecosistema. Remarcar que el protocolo puede evolucionar, pero el problema que resuelve (N×M integraciones) es permanente.
- La lección 2.5 (caching) tiene impacto directo en el coste del alumno. Concretar con números reales de proveedores.
- El diagrama de cierre se construye en vivo durante la grabación — prepararlo paso a paso, no como un diagrama estático.
