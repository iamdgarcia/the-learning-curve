# Semester 4 — AI Architect

## Objetivo del semestre

Diseñar sistemas multi-agente usando grafos de dependencias y ejecución como modelo mental central. El alumno pasa de orquestar agentes individuales a construir sistemas donde la estructura, el paralelismo, el contexto distribuido y la resiliencia son decisiones de arquitectura explícitas.

Al terminar el Semester 4, el alumno puede modelar un sistema multi-agente completo con su grafo de dependencias, su grafo de ejecución, su estrategia de concurrencia y su diseño de fallo — y justificar cada decisión.

## Prerequisitos

Semesters 1, 2 y 3. Se asume conocimiento de cómo funciona un LLM, cómo se construye un pipeline de IA, y cómo se diseña y supervisa un agente individual.

---

## Lecciones

### 4.1 — Graph Engineering: por qué los grafos

**Objetivo:** Entender por qué el modelo mental de grafo es el correcto para diseñar sistemas multi-agente, y por qué el modelo lineal falla a escala.

**Decisión de diseño:** Cuándo un pipeline lineal es suficiente y cuándo necesitas un grafo.

---

### 4.2 — Dependency Graphs

**Objetivo:** Saber construir un dependency graph desde cero, identificando qué puede ejecutarse en paralelo y qué debe esperar.

**Decisión de diseño:** Cómo representar las dependencias reales del sistema antes de escribir una línea de código.

---

### 4.3 — Execution Graphs

**Objetivo:** Entender la diferencia entre el grafo de dependencias (estático) y el grafo de ejecución (dinámico), y diseñar nodos condicionales y de recuperación.

**Decisión de diseño:** Qué nodos necesitan lógica condicional y cuáles deben terminar el sistema antes de llegar al final.

---

### 4.4 — Workflow Design: determinista vs dinámico

**Objetivo:** Elegir el nivel correcto de dinamismo para cada sistema, entendiendo los trade-offs reales en una escala de cinco niveles.

**Decisión de diseño:** En qué punto del espectro determinista-dinámico debe vivir tu sistema según sus requisitos de auditabilidad y flexibilidad.

---

### 4.5 — Task Decomposition a escala

**Objetivo:** Saber descomponer objetivos complejos en tareas que un agente puede ejecutar y verificar.

**Decisión de diseño:** Cuándo descomponer en paralelo y cuándo mantener la secuencia. Cuándo la descomposición es demasiado fina y cuándo es demasiado gruesa.

---

### 4.6 — Concurrencia en sistemas de agentes

**Objetivo:** Diseñar sistemas donde múltiples agentes ejecutan en paralelo sin condiciones de carrera ni costes inesperados.

**Decisión de diseño:** Qué estrategia de concurrencia (fan-out, semáforos, batching) encaja con el patrón de cada sistema.

---

### 4.7 — Distributed Context

**Objetivo:** Diseñar cómo el contexto compartido fluye entre agentes en un sistema distribuido, sin duplicación innecesaria ni pérdida de coherencia.

**Decisión de diseño:** Cuándo usar contexto centralizado, cuándo proyecciones por agente, y cuándo contexto mínimo por nodo.

---

### 4.8 — Diseñar para el fallo

**Objetivo:** Asumir que los agentes van a fallar y diseñar el sistema para tolerarlo: retries, circuit breakers, terminación anticipada, fallbacks y degradación controlada.

**Decisión de diseño:** Qué nivel de resiliencia es necesario en cada nodo según el coste del fallo y la reversibilidad de la operación.

---

### Cierre del Semester 4

**Formato:** Lección de síntesis con diagrama de cierre construido por capas. Es el diagrama más elaborado del curso.

**Objetivo:** Integrar todos los conceptos de los cuatro semestres en un único sistema multi-agente completo que pueda servir como referencia de diseño.

---

## Diagrama de cierre del semestre

**Título:** Sistema multi-agente completo

**Elementos del diagrama:**
- Input del usuario o trigger externo
- Orquestador con grafo de dependencias y estado global
- Nodos de ejecución condicional y retries
- Agentes especializados con herramientas y memoria local
- Capa de contexto distribuido compartido
- Verifiers de output antes de respuesta final
- Mecanismos de resiliencia: circuit breakers, fallbacks, terminación anticipada
- Capa de observabilidad cruzando todos los componentes
- Output al usuario

El diagrama se construye por capas durante la lección: primero el grafo de dependencias, luego la ejecución dinámica, luego el contexto distribuido, luego la capa de resiliencia. La numeración de flujo permite seguir el camino de una petición de principio a fin.

---

## Notas de producción

- Este semestre es el núcleo técnico del curso — si una lección no queda bien en grabación, repetirla.
- Las lecciones 4.2 y 4.3 son la base de todo el semestre — el diagrama de dependency graph debe quedar perfectamente claro.
- La lección 4.4 (espectro determinista-dinámico) es la más conceptual — usar la escala visual de cinco niveles y quedarse en ella todo el tiempo.
- Las lecciones 4.6 (concurrencia) y 4.8 (diseño para el fallo) son donde el alumno demuestra criterio de producción — no bajar el nivel.
- El diagrama de cierre requiere más tiempo de preparación que cualquier otro del curso. Planificar al menos una sesión dedicada solo al diagrama.
