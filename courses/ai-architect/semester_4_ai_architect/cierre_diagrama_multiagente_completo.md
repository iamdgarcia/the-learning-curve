# Cierre del Semestre 4 — Sistema multi-agente completo

**Semestre:** 4 — AI Architect
**Lección:** Cierre
**Duración estimada:** 5-6 min
**Formato visual:** Excalidraw, construcción por capas en pantalla

## Objetivo de la lección

Integrar todos los conceptos de los cuatro semestres en un único sistema multi-agente completo que pueda servir como referencia de diseño.

---

## Guión

### Intro (30 seg)

Durante cuatro semestres hemos construido un vocabulario, una manera de pensar y un conjunto de decisiones de diseño. Cada lección ha añadido una pieza: structured outputs, evaluación, herramientas con niveles de riesgo, verifiers, reflexión, memoria, grafos de dependencia, ejecución condicional, descomposición, concurrencia, contexto distribuido, resiliencia.

Hoy vamos a poner todas esas piezas juntas en un solo diagrama. No como ejercicio teórico. Como síntesis de lo que significa diseñar un sistema de agentes que puede ir a producción.

Vamos a construir el diagrama por capas.

---

### Capa 1: La estructura del sistema (1.5 min)

Empezamos con la estructura de alto nivel.

En la cima del sistema hay un supervisor humano en el loop. No un usuario que espera resultados. Un supervisor con capacidad de revisar, aprobar y rechazar antes de que el sistema continúe en puntos críticos. Esto viene de la lección 3.4. El human-in-the-loop no es una limitación del sistema. Es la decisión consciente de que ciertas decisiones requieren juicio humano que el sistema no puede sustituir.

Debajo del supervisor, el orquestador. El orquestador tiene el execution graph: sabe qué nodos existen, en qué orden ejecutan, qué condiciones activan qué caminos. El grafo no es plano. Tiene nodos condicionales que cambian el flujo según los resultados intermedios. Tiene nodos de terminación anticipada cuando el sistema detecta que el objetivo ya se ha alcanzado o que la ejecución no puede continuar de forma útil. Eso viene de la lección 4.3.

La estructura que subyace al grafo de ejecución es el grafo de dependencias. El orquestador sabe qué tareas deben completarse antes de que otras puedan empezar. Esa información está codificada en el grafo de dependencias de la lección 4.2. No es implícita. No depende de que el diseñador recuerde el orden correcto. Está explícita en la estructura del sistema.

Debajo del orquestador, tres agentes trabajadores. En este sistema, esos tres agentes ejecutan en paralelo cuando sus dependencias están resueltas, siguiendo el patrón fork-join que vimos en la lección 4.6. El orquestador los lanza en paralelo y espera a que todos terminen antes de pasar al siguiente nodo del grafo.

---

### Capa 2: Los mecanismos internos de cada agente (1.5 min)

Ahora añadimos los mecanismos internos de cada agente. Esta capa es donde el diagrama se vuelve denso, porque cada agente es un sistema en sí mismo.

Cada agente tiene acceso a herramientas. No a todas las herramientas. A las herramientas que necesita para su tarea. Y cada herramienta tiene un nivel de riesgo asignado: bajo, medio o alto. Las herramientas de riesgo alto requieren confirmación humana antes de ejecutar. Las de riesgo bajo pueden ejecutar de forma autónoma. Esta jerarquía de riesgo viene de la lección 3.2. Sin ella, el agente puede ejecutar herramientas destructivas sin supervisión.

Cada agente tiene un verifier en el output. Antes de que el resultado del agente llegue al orquestador o al estado compartido, el verifier lo evalúa. Si el output no cumple los criterios, el agente no ha terminado su tarea. La lección 3.3 mostró por qué el verifier es la diferencia entre un sistema que detecta sus propios errores y uno que los propaga hacia adelante.

Cada agente tiene un loop de reflexión. Si el verifier rechaza el output, el agente no falla inmediatamente. Reflexiona: ¿por qué falló? ¿Qué información le falta? ¿Qué estrategia diferente puede intentar? Ese loop viene de la lección 3.5. La reflexión convierte el agente de un ejecutor ciego en un solucionador de problemas.

Y cada output del agente es un structured output. El esquema está definido antes de que el agente ejecute. El orquestador sabe exactamente qué formato va a recibir. Los sistemas downstream saben exactamente qué formato van a consumir. La lección 2.2 estableció por qué la estructura no es un detalle de implementación, es el contrato del sistema.

---

### Capa 3: El contexto y la memoria (45 seg)

Añadimos la capa de información.

En el centro del sistema está el estado compartido. Los tres agentes leen del estado compartido y escriben en él. El orquestador también lee del estado compartido para tomar decisiones de enrutamiento. La lección 4.7 mostró los tres enfoques para gestionar ese contexto distribuido, y en este sistema usamos una combinación: contexto explícito en el prompt para la información que todos los agentes necesitan siempre, estado compartido para la información que cada agente recupera bajo demanda.

Y hay memoria long-term accesible. No toda la historia del sistema está en el context window del orquestador. Lo que importa de ejecuciones anteriores, de aprendizajes acumulados, de patrones observados, está en memoria long-term y se recupera cuando es relevante. Eso viene de la lección 3.6.

---

### Capa 4: La resiliencia y los checkpoints (45 seg)

Ahora la última capa: la resiliencia.

Cada agente tiene los tres mecanismos de la lección 4.8: retry con contexto del error cuando el output es inválido, fallback a un path más simple cuando los reintentos se agotan, circuit breaker cuando la tasa de fallo supera el umbral.

Entre cada etapa completada hay un checkpoint. Si el sistema falla después del checkpoint, reanuda desde ahí. No desde el principio. El coste de un fallo no es perder todo el trabajo. Es perder solo el trabajo después del último checkpoint.

---

### La imagen completa (1 min)

Ahora mira el diagrama completo.

Es complejo. Tiene muchas capas. Tiene muchas conexiones. Pero cada elemento del diagrama viene de una decisión de diseño que hemos examinado en detalle en este curso. No hay nada arbitrario. No hay nada que esté ahí por convención o por moda. Cada pieza está ahí porque resuelve un problema concreto que aparece en sistemas de producción.

El supervisor humano está ahí porque hay decisiones que requieren juicio que el sistema no puede sustituir.

El grafo de ejecución está ahí porque el comportamiento del sistema debe ser predecible, depurable y auditable.

El grafo de dependencias está ahí porque las dependencias entre tareas son una propiedad del dominio, no del código.

La paralelización está ahí porque la latencia importa y el grafo de dependencias dice exactamente qué puede ejecutar en paralelo.

Los verifiers están ahí porque los agentes cometen errores y el sistema debe detectarlos localmente antes de que se propaguen.

La reflexión está ahí porque la primera estrategia no siempre funciona y el agente necesita capacidad de recuperación.

El contexto distribuido está ahí porque la información tiene que fluir entre agentes y ese flujo tiene coste y riesgo.

La resiliencia está ahí porque los agentes van a fallar y el sistema debe tolerar ese fallo sin colapsar.

Y la observabilidad, que no ves en el diagrama porque es transversal a todo, está ahí porque no puedes operar lo que no puedes ver.

---

### Cierre y CTA (30 seg)

Este es el sistema que un AI Architect diseña.

No una demo. No un tutorial de fin de semana. Un sistema que puede ir a producción, que tolera el fallo, que escala con la carga, que puede ser auditado y depurado por un equipo que no estaba en la sala cuando se diseñó.

El Bonus que viene a continuación cubre cómo llevarlo hasta allí: deployment, monitorización, control de costes en producción, y las decisiones de infraestructura que hacen la diferencia entre un sistema que funciona en localhost y uno que funciona bajo carga real.

El link está en la descripción.

---

## Spec del diagrama

**Tipo:** Excalidraw, construcción por capas — se revela incrementalmente durante el video

**Capa 1 — Estructura del sistema (revelada primero):**
- Rectángulo superior "Supervisor Humano" (azul oscuro) con etiqueta "Human-in-the-loop (L3.4)"
- Flecha de aprobación/rechazo bajando a "Orquestador"
- Rectángulo "Orquestador" con sub-elemento "Execution Graph (L4.3)"
- Sub-elemento en el orquestador: "Dependency Graph (L4.2)"
- Tres rectángulos debajo en paralelo: "Agente A", "Agente B", "Agente C" con conector "fork-join (L4.6)"

**Capa 2 — Mecanismos internos de cada agente (revelada segunda):**
- Dentro de cada agente (expandidos):
  - Sub-elemento "Herramientas" con niveles de riesgo (bajo/medio/alto, L3.2)
  - Sub-elemento "Verifier" en el output (L3.3)
  - Sub-elemento "Loop de reflexión" (L3.5)
  - Etiqueta "Structured Output (L2.2)" en la flecha de salida de cada agente

**Capa 3 — Contexto y memoria (revelada tercera):**
- Rectángulo central "Estado Compartido" con flechas R/W hacia/desde cada agente (L4.7)
- Rectángulo lateral "Memoria Long-Term" con flecha al orquestador (L3.6)
- Contexto explícito en el prompt de cada agente anotado como "ctx"

**Capa 4 — Resiliencia y checkpoints (revelada cuarta):**
- Iconos de retry/fallback/circuit breaker en cada agente (L4.8)
- Símbolos de checkpoint entre etapas (discos de guardado en verde)
- Icono de observabilidad transversal (ojo o gráfica de monitoring)

**Capa 5 — Evaluación y coste (revelada última):**
- Nodo "Evaluación del output final (L2.6)" al final del pipeline
- Anotación de coste y latencia estimados en el nivel superior del sistema (L1.7)

**Flujo visual:**
- Vertical de arriba a abajo para el flujo principal: supervisor → orquestador → agentes → output → evaluación
- Los agentes en paralelo a la misma altura
- El estado compartido en el centro entre los agentes
- La memoria long-term en el margen derecho
- Las capas se revelan incrementalmente: primero la estructura limpia, luego los detalles internos, luego las conexiones de información, luego los mecanismos de resiliencia
- Código de color: azul = estructuras de control, verde = mecanismos de verificación/seguridad, naranja = flujos de información, gris = mecanismos de resiliencia
- Cada elemento con referencia entre paréntesis a la lección donde se explicó: (L1.7), (L2.2), etc.
