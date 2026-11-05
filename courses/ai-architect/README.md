# AI Architect Academy
### De software engineer a AI architect

**The Learning Curve** · Curso técnico en español para engineers que quieren diseñar sistemas de IA en producción.

---

## A quién va dirigido

Software engineers con experiencia real en sistemas convencionales — APIs, bases de datos, sistemas distribuidos — que quieren especializarse en arquitectura de sistemas de IA. No es un curso introductorio de IA para managers ni un tutorial de Python básico. Es para quien ya sabe construir sistemas y quiere entender cómo los LLMs cambian las reglas del diseño.

---

## Estructura del curso

| Semestre | Nombre | Lecciones | Descripción | Prerequisitos |
|---|---|---|---|---|
| **S1** | Foundations of LLMs | 7 | Cómo funcionan los LLMs por dentro: next-token prediction, tokens, embeddings, temperatura, finetuning vs RAG, prompt engineering, coste real en producción. | Ninguno — punto de entrada al curso. |
| **S2** | AI Engineering | 6 | Construcción de pipelines de IA fiables: cuándo usar un LLM, structured outputs, tipos de memoria, MCP, caching y evaluación básica. | S1 |
| **S3** | Agent Engineering | 7 | Diseño e implementación de agentes autónomos: skills y herramientas, verifiers, supervisión humana, self-correction, memoria de agentes y patrones de comunicación. | S1 + S2 |
| **S4** | AI Architect | 8 | Arquitectura de sistemas multi-agente con grafos: dependency graphs, execution graphs, workflow design, task decomposition, concurrencia, contexto distribuido y diseño para el fallo. | S1 + S2 + S3 |
| **S5** | Context Engineering | 7 | La disciplina de construir el contexto correcto: RAG, chunking, reranking, compresión de contexto, context poisoning y evaluación de pipelines de recuperación. | S1 + S2 |
| **Bonus** | Production Essentials | 4 | Lo que no aparece en los tutoriales pero sí en producción: tracing y observabilidad, testing de sistemas no deterministas, seguridad y guardrails, latencia y escalado. | S1 + S2 + S3 + S4 |
| **S6** | IA en la Organización *(solo YouTube)* | 8 | Por qué fracasan las iniciativas de IA, cómo evaluar casos de uso, equipos, build vs buy, gobernanza, ROI. Audiencia: managers y CTOs. | Ninguno (independiente del track técnico) |

---

## Mapa de progresión

```
S1 Foundations
     │
     ▼
S2 AI Engineering ──────────────────────────┐
     │                                      │
     ▼                                      ▼
S3 Agent Engineering              S5 Context Engineering
     │
     ▼
S4 AI Architect
     │
     ▼
Bonus Production Essentials
```

S5 puede cursarse en paralelo con S3 o S4. Solo requiere S1 + S2.

---

## Estructura del repositorio

```
ai_architect_course/
│
├── README.md                          ← este archivo
├── PRODUCTION_GUIDE.md                ← guía de formato y producción de lecciones
│
├── semester_1_foundations/
│   ├── README.md
│   ├── 1.1_como_piensan_los_llms.md
│   ├── 1.2_tokens_y_context_windows.md
│   ├── 1.3_embeddings_para_arquitectos.md
│   ├── 1.4_temperatura_y_determinismo.md
│   ├── 1.5_finetuning_vs_rag.md
│   ├── 1.6_prompt_engineering_arquitectos.md
│   ├── 1.7_coste_real_llm_produccion.md
│   └── cierre_diagrama_anatomia_sistema.md
│
├── semester_2_ai_engineering/
│   ├── README.md
│   ├── 2.1_cuando_usar_llm.md
│   ├── 2.2_structured_outputs_function_calling.md
│   ├── 2.3_memory_tipos.md
│   ├── 2.4_mcp_arquitectura.md
│   ├── 2.5_caching_optimizacion.md
│   ├── 2.6_evaluacion_basica.md
│   └── cierre_diagrama_pipeline_ia.md
│
├── semester_3_agent_engineering/
│   ├── README.md
│   ├── 3.1_que_es_un_agente.md
│   ├── 3.2_skills_herramientas_limites.md
│   ├── 3.3_verifiers_validacion.md
│   ├── 3.4_supervisors_supervision_humana.md
│   ├── 3.5_selfcorrection_reflexion.md
│   ├── 3.6_memoria_agentes.md
│   ├── 3.7_comunicacion_agentes_patrones.md
│   └── cierre_diagrama_agente_supervisor.md
│
├── semester_4_ai_architect/
│   ├── README.md
│   ├── 4.1_graph_engineering_intro.md
│   ├── 4.2_dependency_graphs.md
│   ├── 4.3_execution_graphs.md
│   ├── 4.4_workflow_design.md
│   ├── 4.5_task_decomposition.md
│   ├── 4.6_concurrencia_agentes.md
│   ├── 4.7_distributed_context.md
│   ├── 4.8_disenar_para_el_fallo.md
│   └── cierre_diagrama_multiagente_completo.md
│
├── semester_5_context_engineering/
│   ├── README.md
│   ├── 5.1_que_es_context_engineering.md
│   ├── 5.2_anatomia_del_contexto.md
│   ├── 5.3_rag_como_context_engineering.md
│   ├── 5.4_chunking_y_reranking.md
│   ├── 5.5_context_compression.md
│   ├── 5.6_context_poisoning_y_drift.md
│   ├── 5.7_evaluacion_de_contextos.md
│   └── cierre_diagrama_context_pipeline.md
│
├── bonus_production_essentials/
│   ├── README.md
│   ├── b1_tracing_observabilidad.md
│   ├── b2_testing_sistemas_no_deterministas.md
│   ├── b3_seguridad_guardrails.md
│   └── b4_latencia_escalado.md
│
├── youtube_semester_6/
│   ├── README.md
│   ├── 6.1_que_cambia_cuando_empresa_adopta_ia.md
│   ├── 6.2_departamentos_que_desaparecen.md
│   ├── 6.3_equipo_ai_first.md
│   ├── 6.4_tareas_que_siguen_siendo_humanas.md
│   ├── 6.5_procesos_ai_native.md
│   ├── 6.6_vender_ia_internamente.md
│   ├── 6.7_liderar_equipos_ai_first.md
│   └── 6.8_case_study_saas_con_ia.md
│
├── notebooks/
│   ├── s1_llm_fundamentals.ipynb       ← tokens, temperatura, llamadas a API
│   ├── s2_ai_engineering.ipynb         ← structured outputs, memory, caching
│   ├── s3_agent_engineering.ipynb      ← agente con herramientas, verifiers
│   ├── s4_multi_agent.ipynb            ← grafo de agentes, orquestación
│   ├── s5_context_engineering.ipynb    ← RAG completo, chunking, evaluación
│   └── bonus_production.ipynb          ← tracing, testing, cost tracking
│
└── resources/
    └── stitch_plantilla_slides_curso_comunidad/   ← plantillas HTML para slides
```

---

## Notebooks de práctica

Cada semestre tiene un notebook de Jupyter en `/notebooks/` que traduce los conceptos del guión a código ejecutable. Los notebooks son independientes — puedes correr el de S3 sin haber corrido el de S1, aunque el contenido asume el conocimiento de los semestres anteriores.

Requisitos para correr los notebooks:

```bash
pip install openai anthropic langchain-core numpy pandas jupyter
```

Los notebooks usan la API de OpenAI por defecto. Requieren `OPENAI_API_KEY` en las variables de entorno. Donde sea posible, el modelo usado es el más económico disponible (`gpt-4o-mini`) para minimizar coste durante el aprendizaje.

---

## Nota sobre S6

El Semestre 6 — *IA en la Organización* — es contenido publicado exclusivamente en YouTube, dirigido a una audiencia diferente: directores, product managers, CTOs y líderes de equipo que necesitan tomar decisiones sobre IA sin necesariamente implementarla ellos mismos.

No forma parte del track técnico del curso. No hay prerequisitos técnicos ni lecciones que lo continúen. Es independiente por diseño.

Canal: [The Learning Curve en YouTube](https://youtube.com/@iamdgarcia)

---

## Formato de las lecciones

Cada lección `.md` es un guión de grabación con la siguiente estructura:

- **Objetivo de la lección** — qué debe saber hacer el alumno al terminar
- **Guión** — dividido en bloques temáticos con timing estimado
- **Decisión de diseño** — el cierre práctico: qué decisión arquitectónica cubre la lección
- **Spec del diagrama** — descripción del visual que acompaña el video

Las lecciones están escritas para ser grabadas como videos de 8-12 minutos. El guión no es un script palabra por palabra — es una guía de contenido y estructura para el presentador.

Para los detalles de producción (formato de grabación, checklist, plantillas de descripción, protocolo de publicación): ver `PRODUCTION_GUIDE.md`.
