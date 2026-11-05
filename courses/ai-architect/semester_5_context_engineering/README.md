# Semester 5 — Context Engineering

## Objetivo del semestre

Dominar el diseño, la estructuración y la optimización de contextos para sistemas de IA en producción. Al terminar este semestre, el alumno entiende que la calidad del output de un LLM depende fundamentalmente de la calidad del contexto que lo rodea — no solo del prompt — y tiene las herramientas para diseñar, depurar y evaluar ese contexto de forma sistemática.

## Prerrequisitos

- **S1 — Foundations:** necesario. Especialmente 1.1 (cómo piensan los LLMs), 1.2 (tokens y context windows) y 1.3 (embeddings).
- **S2 — AI Engineering:** necesario. El pipeline RAG de este semestre amplía los conceptos de S2.
- **S3 — Agent Engineering:** recomendado. Las lecciones sobre context poisoning y evaluación de agentes asumen familiaridad con herramientas y supervisión.

## Lecciones

| # | Título | Objetivo de arquitectura | Duración |
|---|--------|--------------------------|----------|
| 5.1 | Qué es Context Engineering | Distinguir context engineering de prompt engineering y justificar la diferencia arquitectónicamente | 8-10 min |
| 5.2 | Anatomía del contexto: las cinco capas | Mapear cualquier sistema a las cinco capas y detectar cuál de ellas causa problemas de calidad o coste | 9-11 min |
| 5.3 | RAG como Context Engineering | Diseñar el pipeline RAG completo — ingestión hasta respuesta — y elegir entre RAG y fine-tuning | 9-11 min |
| 5.4 | Chunking y reranking | Elegir estrategia de chunking y reranking para el caso de uso, entendiendo los trade-offs de cada decisión | 9-11 min |
| 5.5 | Context Compression | Diseñar gestión de contexto que no se satura durante sesiones largas ni entre sesiones | 8-10 min |
| 5.6 | Context Poisoning y Context Drift | Identificar vectores de poisoning y síntomas de drift, y añadir defensas correctas | 9-11 min |
| 5.7 | Evaluación de contextos | Diseñar un sistema de evaluación con métricas concretas para RAG y agentes | 9-11 min |
| — | Cierre: diagrama del sistema completo | Integrar todas las piezas en una arquitectura cohesiva de context engineering | 5-7 min |

**Duración total estimada:** 65-80 minutos

---

## Cierre del semestre

El diagrama de cierre muestra el sistema completo de context engineering: fuentes de conocimiento → pipeline RAG (ingestión y query) → memoria jerárquica (hot/warm/cold) → las cinco capas del contexto con compresión activa → defensas contra poisoning y drift → evaluación offline y monitorización online.

El remate es la proporción real: el prompt del usuario es el 2-10% de ese sistema. El 90-98% restante es context engineering.

---

## Notas de producción

**Audiencia objetivo:** Software Engineers con experiencia en sistemas distribuidos que han construido o están construyendo sistemas con LLMs. Conocen los fundamentos del LLM (S1) y han trabajado con al menos un pipeline de IA (S2).

**Prerequisito implícito de herramientas:** las lecciones hacen referencia a pgvector, Qdrant, Pinecone, Cohere Rerank, RAGAS, LLMLingua. No se profundiza en la implementación de ninguna herramienta específica — el foco es en las decisiones de diseño, no en el código de setup.

**Conexiones cross-semestre:**
- La Lección 5.2 amplía directamente 1.2 (context windows y tokens) y 1.3 (embeddings).
- La Lección 5.3 (RAG) cierra el gap que quedó en S2, donde RAG se mencionó pero no se desarrolló.
- Las Lecciones 5.5 y 5.6 conectan con los patrones de memoria y supervisión del S3.
- La Lección 5.7 amplía la evaluación básica de S2 con métricas específicas para contextos.

**Formato de grabación:** todas las lecciones siguen el formato estándar del curso: Excalidraw para el diagrama principal, grabación en formato slides PDF para la escala de niveles donde aplique. Duración objetivo: 9-10 minutos por lección.

**Orden de publicación recomendado:** publicar en orden secuencial (5.1 → 5.7). La Lección 5.3 (RAG) es la más autocontenida y la que más búsqueda orgánica puede captar — considerar publicar primero si el lanzamiento es por YouTube.
