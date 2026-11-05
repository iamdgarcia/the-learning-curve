# Bonus — Production Essentials

## Objetivo

Cubrir los cuatro pilares operacionales que todo sistema de IA necesita antes de llegar a producción robusta: saber qué pasa dentro (observabilidad), confiar en el comportamiento sin assertions exactas (testing), proteger el sistema ante vectores de ataque específicos de LLMs (seguridad), y cumplir compromisos de rendimiento desde el diseño (latencia y escalado).

Este bloque bonus no es teoría de producción — es el conjunto mínimo de decisiones de diseño que separan un prototipo funcional de un sistema que puedes operar con confianza.

## Prerequisitos

Semestres 1–4 recomendados. El contenido asume familiaridad con la arquitectura de agentes y sistemas multi-agente. Puede seguirse de forma independiente si ya se trabaja con sistemas LLM en producción.

## Lecciones

### B.1 — Tracing y Observabilidad
**Archivo:** `b1_tracing_observabilidad.md`
**Duración:** 7–9 min

Saber exactamente qué hizo el sistema y por qué cuando algo falla en producción. Cubre tracing distribuido con spans por agente y por llamada al LLM, qué registrar en cada span (tokens, latencia, coste, retries), niveles de logging por entorno (desarrollo / staging / producción con restricciones de privacidad), y el dashboard mínimo operacional (P50/P95/P99, tasa de error por agente, coste por hora, alertas).

**Decisión de diseño:** qué nivel de logging activar en cada entorno y qué tres preguntas hay que responder antes del primer deploy.

---

### B.2 — Testing en Sistemas No Deterministas
**Archivo:** `b2_testing_sistemas_no_deterministas.md`
**Duración:** 7–9 min

Tener confianza en el sistema sin poder hacer assertions exactas sobre el output. Cubre por qué los tests de igualdad exacta no funcionan con LLMs, el golden dataset como entregable obligatorio previo al deploy (inputs + criterios, no inputs + outputs exactos), las tres estrategias complementarias (property-based testing, LLM-as-a-judge, evaluación humana), el ciclo de mejora continua alimentado por fallos en producción, y el threshold de release como decisión que se toma antes de ver los números.

**Decisión de diseño:** cuándo construir el golden dataset y qué porcentaje de casos debe pasar para hacer deploy.

---

### B.3 — Seguridad y Guardrails
**Archivo:** `b3_seguridad_guardrails.md`
**Duración:** 7–9 min

Diseñar la capa de seguridad para los riesgos específicos de sistemas LLM, no solo los de software tradicional. Cubre los tres vectores de ataque propios de sistemas de agentes (prompt injection, data exfiltration, privilege escalation), por qué la separación instrucción/datos no existe de forma nativa en un LLM, y el diseño completo de guardrails: capa de validación de input antes del agente y capa de validación de output antes de que llegue al usuario.

**Decisión de diseño:** para cada tipo de dato sensible, contar cuántas capas de protección tiene y actuar si son menos de las necesarias.

---

### B.4 — Latencia y Escalado
**Archivo:** `b4_latencia_escalado.md`
**Duración:** 7–9 min

Diseñar para el rendimiento antes de que la latencia o el coste sean un problema, no después. Cubre las tres fuentes de latencia en sistemas de agentes (llamadas al LLM dominan, herramientas externas, overhead del orquestador), paralelización como palanca principal (llamadas independientes van en paralelo desde el diseño), streaming para reducir latencia percibida, caching a nivel de agente para inputs recurrentes, y la distinción entre escalar para latencia (diseño) vs escalar para throughput (horizontal). Incluye tabla de SLA por tipo de sistema (batch, near-real-time, real-time).

**Decisión de diseño:** definir el SLA de latencia (P50/P95/P99) antes de construir e identificar qué partes del sistema paralelizar primero.

---

## Notas de producción

- Las cuatro lecciones son independientes entre sí pero se refuerzan: la observabilidad (B.1) alimenta el ciclo de mejora del testing (B.2); el testing incluye validación de guardrails de seguridad (B.3); los guardrails son parte de la latencia total del sistema (B.4).
- El orden recomendado es B.1 → B.2 → B.3 → B.4, ya que cada lección hace referencia a conceptos introducidos en la anterior.
- No hay diagrama de cierre de semestre para este bloque. Cada lección tiene su propio diagrama (Excalidraw para B.1 y B.3, Slides PDF para B.2 y B.4).
- CTA de este bloque: newsletter The Learning Curve + consultoría para equipos que quieren llevar sus sistemas a producción.
