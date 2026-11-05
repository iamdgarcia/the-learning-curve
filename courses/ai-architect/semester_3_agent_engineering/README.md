# Semester 3 — Agent Engineering

## Objetivo del semestre

Diseñar e implementar agentes de IA robustos. El alumno aprende a dar autonomía a un sistema de IA de forma controlada — con herramientas bien delimitadas, validación de outputs, mecanismos de auto-corrección, memoria adecuada y patrones claros de comunicación.

Al terminar el Semester 3, el alumno puede diseñar un agente completo con loop de percepción-razonamiento-acción, capa de validación, supervisión calibrada y memoria, y puede justificar cada decisión de diseño en términos de riesgo y trazabilidad.

## Prerequisitos

Semester 1 — Foundations of LLMs y Semester 2 — AI Engineering. El agente es una extensión del pipeline de IA: sin entender cómo funcionan los LLMs y cómo se construyen pipelines con herramientas y memoria, no se puede diseñar un agente con criterio.

---

## Lecciones

| # | Título | Objetivo | Duración |
|---|--------|----------|----------|
| 3.1 | Qué es un agente (definición arquitectónica) | Tener una definición precisa de "agente" que permita decidir cuándo construir uno y cuándo no. Distinguir agente de pipeline. | 7-9 min |
| 3.2 | Skills, herramientas y límites del agente | Diseñar el espacio de acción de un agente aplicando principio de mínimo privilegio. Clasificar herramientas por nivel de riesgo. | 7-9 min |
| 3.3 | Verifiers y validación de outputs | Diseñar una capa de validación que impide que los errores del agente se propaguen al siguiente paso del sistema. | 7-9 min |
| 3.4 | Supervisors y supervisión humana | Diseñar el nivel correcto de autonomía para cada sistema, evitando sobreautonomía y human-in-the-loop innecesario. | 8-10 min |
| 3.5 | Self-correction y reflexión en agentes | Diseñar agentes que detectan y corrigen sus propios errores sin intervención externa. Entender cuándo el coste vale la pena. | 7-9 min |
| 3.6 | Memoria en agentes: short vs long term | Diseñar la capa de memoria de un agente eligiendo el tipo correcto (in-context, episódica, semántica) para cada necesidad. | 7-9 min |
| 3.7 | Comunicación entre agentes: patrones | Diseñar cómo dos o más agentes se pasan información sin crear dependencias frágiles o bucles sin control. | 7-9 min |
| — | Cierre del semestre | Integrar los siete conceptos en un único diagrama de arquitectura de agente completo. | 4-5 min |

---

### 3.1 — Qué es un agente (definición arquitectónica)

**Objetivo:** Tener una definición precisa de "agente" que permita decidir cuándo construir uno y cuándo no. Distinguirlo de un pipeline secuencial y del hype de marketing.

**Decisión de diseño:** Cuándo un agente aporta valor frente a un pipeline simple, y a qué coste.

---

### 3.2 — Skills, herramientas y límites del agente

**Objetivo:** Diseñar el espacio de acción de un agente con principio de mínimo privilegio. Entender que las herramientas son código determinista tuyo, no del LLM.

**Decisión de diseño:** Qué herramientas darle al agente, con qué nivel de privilegio, y cómo limitar el blast radius de un error.

---

### 3.3 — Verifiers y validación de outputs

**Objetivo:** Diseñar una capa de validación que impide que los errores del agente lleguen al siguiente paso del sistema. El LLM no falla con excepciones — falla produciendo algo plausible pero incorrecto.

**Decisión de diseño:** Qué validar (schema, formato, reglas de negocio) y dónde colocar el verifier en el flujo.

---

### 3.4 — Supervisors y supervisión humana

**Objetivo:** Diseñar el nivel correcto de autonomía para cada tipo de acción. Evitar tanto la sobreautonomía (agente que actúa sin red) como el human-in-the-loop innecesario (que anula el valor del agente).

**Decisión de diseño:** Para cada acción del agente, en qué punto del espectro autonomía-supervisión colocarla y por qué.

---

### 3.5 — Self-correction y reflexión en agentes

**Objetivo:** Diseñar agentes que detectan y corrigen sus propios errores antes de entregar el output al sistema. Entender por qué el LLM en modo crítico detecta errores que no detectó en modo generativo, y cuándo ese ciclo extra vale el coste.

**Decisión de diseño:** Cuándo añadir un ciclo de self-correction y cuántas iteraciones son razonables antes de escalar.

---

### 3.6 — Memoria en agentes: short vs long term

**Objetivo:** Diseñar la capa de memoria de un agente individual eligiendo el tipo correcto para cada necesidad: in-context (sesión), episódica (historial de pasos), semántica (conocimiento recuperable).

**Decisión de diseño:** Qué información merece persistir, durante cuánto tiempo, y qué pasa si el agente la olvida.

---

### 3.7 — Comunicación entre agentes: patrones

**Objetivo:** Diseñar cómo dos o más agentes se pasan información sin crear dependencias frágiles. Los tres patrones fundamentales: llamada directa, paso de mensajes, pizarra compartida.

**Decisión de diseño:** Qué nivel de acoplamiento es correcto para cada relación entre agentes, y qué patrón lo implementa con el mínimo de complejidad.

---

### Cierre del Semester 3

**Formato:** Lección de síntesis con diagrama construido en pantalla en tiempo real.

**Objetivo:** Integrar los siete conceptos del semestre en un único diagrama de arquitectura de agente completo, mostrando cómo se conectan en un sistema real de producción.

---

## Diagrama de cierre del semestre

**Título:** Agente completo con supervisor y memoria

**Elementos del diagrama:**
- Input del usuario / sistema externo
- Agente orquestador (loop percepción → razonamiento → acción)
  - Módulo de razonamiento (LLM)
  - Herramientas disponibles clasificadas por nivel de riesgo (3.2)
  - Verifier de outputs entre agente y sistema destino (3.3)
  - Módulo de self-correction antes del output final (3.5)
- Memoria del agente:
  - In-context (sesión activa)
  - Episódica (log de pasos y decisiones)
  - Semántica (base de conocimiento recuperable)
- Supervisor / punto de intervención humana (3.4)
- Canal de comunicación hacia agentes externos (3.7)
- Output al sistema siguiente o al usuario

El diagrama debe dejar claro el flujo de control, dónde puede fallar el agente y dónde puede intervenir un humano o un sistema externo.

---

## Notas de producción

- La lección 3.2 (herramientas) es donde el alumno pasa de "el agente hace cosas" a "yo decido exactamente qué puede y qué no puede hacer el agente". Ese cambio de perspectiva es el punto de inflexión del semestre.
- La lección 3.4 (supervisión) es la más malentendida: muchos equipos van al extremo equivocado. El énfasis debe estar en que el nivel de supervisión es una decisión de diseño, no un parámetro que se pone por defecto.
- La lección 3.7 (comunicación) abre el terreno del Semester 4: cuando hay varios agentes que se comunican, necesitas arquitectura multi-agente. El cierre de 3.7 debe apuntar hacia eso.
- El diagrama de cierre es la base sobre la que se construye el Semester 4. Hacerlo bien aquí simplifica la siguiente etapa.
