# Cierre del Semestre 2 — El pipeline completo

**Semestre:** 2 — AI Engineering
**Lección:** Cierre
**Duración estimada:** 4-5 min
**Formato visual:** Excalidraw (pipeline integrado, construido en pantalla durante el guión)

---

## Objetivo de la lección

Integrar los seis conceptos del semestre en un único diagrama de pipeline que muestre cómo se relacionan entre sí y qué decide cada componente.

---

## Guión

### Intro (15 seg)

Seis lecciones. Seis decisiones de diseño distintas. Las hemos visto por separado porque tiene sentido aprenderlas así. Ahora las vemos juntas, porque en producción siempre son juntas.

Voy a construir el pipeline en pantalla mientras lo explico.

---

### Construcción del diagrama — en vivo

Empezamos por la izquierda. El input del usuario llega al sistema.

Antes de llegar al LLM, hay una primera decisión que vimos en la Lección 2.1: ¿este input necesita un LLM, o puedo resolverlo con código? Si la query es determinista, estructurada, con una respuesta exacta — código. Rápido, barato, confiable. Si requiere razonamiento, lenguaje natural, o generalización — LLM. El árbol de decisión vive aquí, en el borde de entrada del sistema, antes de cualquier llamada al modelo.

Si la decisión es LLM, el sistema construye el prompt. Y aquí entra la Lección 2.5: la estructura del prompt no es arbitraria. Las partes estáticas van primero — el system prompt con las instrucciones, el contexto de referencia, los ejemplos fijos. Las partes dinámicas van al final — el input del usuario, los datos específicos de esta llamada. Esa estructura activa el prompt caching. Todo lo estático se procesa una vez y se reutiliza. Los costes de tokens de entrada caen de forma significativa.

Antes de llamar al LLM, el sistema también consulta la memoria. Y aquí entra la Lección 2.3. Si la conversación es corta, el historial va directamente al contexto — in-context memory. Si la conversación es larga o el usuario vuelve después de días, hay un path de RAG: el sistema recupera los fragmentos de historial o documentos relevantes del almacén externo y los añade al prompt. La memoria no está en el modelo. Está en lo que el sistema decide incluir en cada llamada.

Ahora el LLM procesa el prompt y genera un output. Ese output puede ser de dos tipos, que vimos en la Lección 2.2. Un structured output — JSON con un esquema definido, fiable, que el código downstream puede procesar sin ambigüedad. O una llamada a herramienta — function calling — cuando el LLM necesita información externa o necesita ejecutar una acción.

Cuando hay function calling, entra la Lección 2.4: las herramientas se exponen como servidores MCP. El LLM descubre qué servidores están disponibles, decide cuál necesita, el orquestador ejecuta la llamada, y el resultado vuelve al LLM para continuar. Si las mismas herramientas las usan más de un agente, el servidor MCP es el punto de reutilización. Una integración, accesible por todos los modelos que hablen el protocolo.

El output final — ya sea texto estructurado o el resultado de un ciclo de function calling — sale del LLM y va a evaluación. Aquí entra la Lección 2.6. Las heurísticas programáticas se ejecutan siempre: checks de formato, longitud, campos. El LLM-as-a-judge se ejecuta para evaluación de regresión y muestreo de producción. La evaluación humana vive en el golden dataset que crece con cada incidencia de producción. Esas métricas informan la decisión de release y la iteración del sistema.

Ese es el pipeline completo. No es un diagrama teórico. Es la arquitectura de referencia de cualquier sistema LLM en producción mínimamente serio.

---

### Síntesis (45 seg)

Cada componente tiene un coste. El árbol de decisión del input tiene coste de latencia si es complejo, pero ahorra el coste de llamadas innecesarias al modelo. El prompt caching reduce el coste de tokens en hasta el noventa por ciento en el prefijo estático. La memoria en contexto es gratis hasta que escala — cuando escala, el RAG es más caro en infraestructura pero más barato en tokens. El servidor MCP tiene overhead de implementación pero paga dividendos en reutilización. La evaluación tiene coste de operación, pero el coste de no tenerla es mayor: es degradación silenciosa en producción.

Ningún sistema de producción va a usar todos estos componentes desde el día uno. Se añaden en el orden en que el problema lo requiere. Pero tener el mapa completo desde el principio evita que tengas que reescribir la arquitectura cuando añades el siguiente componente.

---

### Cierre y CTA

Todo este pipeline puede desplegarse en DigitalOcean. Cada componente — el orquestador, los servidores MCP, el almacén vectorial para RAG, el sistema de evaluación — tiene una forma de correr en producción real.

En el Semester 3 añadimos la capa que falta en este diagrama: los agentes. Hasta ahora el sistema responde a un input. En el Semester 3, el sistema planifica, ejecuta pasos en secuencia, maneja fallos, y decide cuándo ha terminado. El pipeline que acabamos de ver es la base sobre la que los agentes se construyen.

Link en la descripción.

---

## Spec del diagrama

**Tipo:** Excalidraw
**Elementos (construidos en orden durante el guión):**

1. Nodo de entrada: `"Input del usuario"` — flecha hacia la derecha

2. Rombo de decisión: `"¿LLM o código? (L2.1)"` — dos salidas:
   - Flecha hacia abajo: `"CÓDIGO — determinista, exacto"` con nodo final `"Output directo"`
   - Flecha a la derecha: `"LLM — razonamiento, lenguaje natural"`

3. Bloque de construcción del prompt (antes del LLM):
   - Caja dividida verticalmente: sección superior verde: `"Partes estáticas — system prompt / contexto / ejemplos (L2.5)"` con etiqueta lateral `"CACHEADO"` — sección inferior naranja: `"Partes dinámicas — input usuario / contexto de sesión (L2.5)"`
   - Flecha lateral desde un almacén con etiqueta: `"Memoria (L2.3)"` con dos sub-flechas: `"In-context (conversación corta)"` y `"RAG path (conversación larga / sesiones anteriores)"`

4. Nodo central grande: `"LLM"` — dos flechas salientes:
   - Flecha hacia abajo: `"Structured output — JSON / schema (L2.2)"`
   - Flecha lateral: `"Function calling (L2.2)"` → bloque `"Servidores MCP (L2.4)"` con nota: `"N modelos + M herramientas — reutilizable"` → flecha de retorno al LLM: `"Resultado de herramienta"`

5. Nodo intermedio: `"Output final"` con flecha hacia abajo

6. Bloque de evaluación con tres ramas paralelas (L2.6):
   - Rama izquierda: `"Heurísticas — siempre activas"` con etiqueta `"Coste: BAJO"`
   - Rama central: `"LLM-as-a-judge — regresión y muestreo"` con etiqueta `"Coste: MEDIO"`
   - Rama derecha: `"Evaluación humana — golden dataset"` con etiqueta `"Coste: ALTO"`
   - Convergencia en: `"MÉTRICAS"` → `"Decisión de release / iteración"`

7. Anotación de costes en cada componente principal:
   - Junto al prompt: `"Cache → hasta -90% tokens de entrada"`
   - Junto al LLM: `"Coste: mayor — solo cuando es necesario"`
   - Junto a MCP: `"Overhead inicial → ahorro en reutilización"`
   - Junto a evaluación: `"Coste de operar < coste de no detectar fallos"`

8. Nota de título superior del diagrama completo: `"Pipeline de IA — Semester 2 completo"`

**Flujo visual:** El diagrama se construye de izquierda a derecha, elemento por elemento, mientras el presentador habla. Cada componente aparece en el momento en que se menciona. El diagrama completo solo es visible en el momento de la síntesis, cuando todos los elementos están en pantalla simultáneamente.
