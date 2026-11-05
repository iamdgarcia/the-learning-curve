# Cierre S1 — Diagrama: Anatomía de un sistema con LLM

**Semestre:** 1 — Foundations
**Tipo:** Cierre de semestre
**Duración estimada:** 4-5 min
**Formato visual:** Excalidraw complejo (diagrama de arquitectura completo)

---

## Objetivo

Mostrar cómo los 7 conceptos del semestre se integran en un sistema real, construyendo el diagrama en pantalla mientras el presentador explica cada conexión.

---

## Guión de cierre

### Apertura (20 seg)

Siete lecciones. Cada una con un concepto independiente, con su propio árbol de decisión. Ahora los conectamos. Voy a construir en pantalla el diagrama de un sistema LLM completo. Un sistema que podrías encontrarte en producción. Mientras lo construyo, verás exactamente dónde vive cada concepto del semestre.

---

### Construcción: la ruta principal

Empezamos desde donde siempre empieza un sistema: el usuario.

El usuario genera una petición. Esa petición llega a la interfaz — la capa que el usuario ve, sea una app web, un chat, una API externa. [Dibujar: Usuario → Interfaz]

La interfaz pasa la petición a la capa de prompt. Aquí es donde el sistema construye lo que el modelo va a recibir. No es solo el mensaje del usuario. Es el mensaje del usuario más todo lo que el sistema ha decidido que el modelo necesita saber. [Dibujar: Interfaz → Constructor de Prompt]

Y en esa capa de prompt, el sistema prompt que definimos en la lección 1.6. Cuatro secciones. Rol, contexto, restricciones, formato. No es texto informal. Es la interfaz del sistema. [Anotar en el nodo de Prompt: ROL / CONTEXTO / RESTRICCIONES / FORMATO]

Ese prompt completo — con todas sus secciones — entra en la context window del modelo. La ventana de contexto que estudiamos en la lección 1.2. Tiene límites numéricos duros. Todo lo que el modelo puede ver en una llamada tiene que caber ahí. [Anotar junto a la flecha Prompt → LLM: "Context Window — límite en tokens (L1.2)"]

El modelo procesa el prompt. Genera tokens uno a uno, con la temperatura que el sistema ha configurado para esta tarea específica — lección 1.4. Temperatura 0 si es extracción, temperatura más alta si es generación conversacional. [Anotar en el nodo LLM: "Temperatura configurada por tipo de tarea (L1.4)"]

El output del modelo llega a un verificador. En muchos sistemas en producción hay una capa que valida que el output tiene el formato correcto, que no viola restricciones del dominio, que el JSON es parseable. Esa capa filtra antes de que la respuesta llegue al usuario. [Dibujar: LLM → Verificador → Respuesta final al usuario]

---

### Construcción: la ruta de conocimiento (RAG)

Hay una segunda ruta en este sistema. La ruta del conocimiento.

El sistema tiene una Knowledge Base. Documentos internos, manuales de producto, base de datos de conocimiento, lo que sea que el sistema necesita saber y que no está en los pesos del modelo. [Dibujar: Knowledge Base separada a la izquierda del diagrama]

Esos documentos han pasado por un Embedding Model — lección 1.3. Cada fragmento de documento se ha convertido en un vector numérico que captura su significado semántico. [Dibujar: Knowledge Base → Embedding Model]

Esos vectores están almacenados en un Vector Store. Un índice que permite buscar por similitud semántica, no por palabras clave exactas. [Dibujar: Embedding Model → Vector Store]

Cuando llega la petición del usuario, antes de construir el prompt, el sistema hace una búsqueda de retrieval. Convierte la petición del usuario en un vector, busca en el Vector Store los fragmentos más relevantes, y los recupera. Ese es el RAG de la lección 1.5. [Dibujar: petición del usuario → Retrieval → Vector Store (flecha bidireccional)]

Los fragmentos recuperados entran al Constructor de Prompt como parte del contexto. Así el modelo tiene acceso a información específica y actualizada sin necesidad de fine-tuning. [Dibujar: Retrieval → Constructor de Prompt]

---

### Construcción: las anotaciones de coste

El diagrama está casi completo. Queda una capa de anotación.

En cada flecha principal que cruza el sistema, el coste tiene un nombre: tokens. [Anotar en flechas principales: "tokens de entrada" en la flecha al LLM, "tokens de salida" en la flecha desde el LLM]

El coste total de una llamada es la suma de tokens de entrada por su precio más tokens de salida por su precio — lección 1.7. El arquitecto que diseñó este sistema eligió el modelo correcto para la tarea y configuró el system prompt de forma que la parte estática sea cacheable. Esas dos decisiones definen si este sistema es económicamente viable o no a escala.

---

### Lectura del diagrama completo (30 seg)

Ahora miramos el diagrama completo y lo leemos de izquierda a derecha.

Una petición del usuario entra por la interfaz. El sistema construye el prompt — con el system prompt del L1.6 — combinando la petición con los fragmentos relevantes recuperados del Vector Store a través de RAG. Ese prompt completo entra en la context window — límite numérico del L1.2. El modelo, operando con los pesos que describen cómo piensa un LLM — L1.1 — y con la temperatura apropiada para la tarea — L1.4 — genera un output. El output se verifica y llega al usuario. El coste de cada llamada es predecible y optimizable — L1.7.

Eso es el Semestre 1. No como siete lecciones separadas. Como un sistema que funciona.

---

### CTA de afiliación

Este tipo de sistema, en producción, puede desplegarse en DigitalOcean por menos de 20 dólares al mes. Vector store, API backend, base de datos: la infraestructura completa a un coste que no requiere justificación ejecutiva para experimentar. El link está en la descripción.

En el Semester 2 empezamos a construir sobre este diagrama. Añadimos agentes, patrones de orquestación, y los bloques de decisión que convierten un sistema LLM básico en un sistema que puede actuar, no solo responder. Nos vemos ahí.

---

## Spec del diagrama (el más importante del semestre)

**Tipo:** Excalidraw complejo — diagrama de arquitectura completo, construido de forma incremental durante el video

**Layout general:**
- Eje horizontal principal de izquierda a derecha: Usuario → Interfaz → Constructor de Prompt → LLM → Verificador → Respuesta
- Ruta secundaria inferior/lateral: Knowledge Base → Embedding Model → Vector Store → Retrieval → (entra al Constructor de Prompt)
- Anotaciones flotantes en nodos clave con referencia a la lección correspondiente

**Nodos y etiquetas exactas:**

| Nodo | Etiqueta | Forma |
|------|----------|-------|
| Usuario | `Usuario` | Figura persona |
| Interfaz | `Interfaz (App / API)` | Rectángulo |
| Constructor de Prompt | `Constructor de Prompt` | Rectángulo doble borde |
| System Prompt | `System Prompt` con 4 sub-etiquetas: `ROL`, `CONTEXTO`, `RESTRICCIONES`, `FORMATO` | Rectángulo con divisiones internas, fondo azul suave |
| LLM | `LLM` con anotación: `Temperatura (L1.4)` | Rectángulo grande, borde grueso |
| Verificador | `Verificador / Validador` | Rombo o rectángulo con borde discontinuo |
| Respuesta | `Respuesta al usuario` | Figura persona |
| Knowledge Base | `Knowledge Base (docs internos)` | Cilindro / base de datos |
| Embedding Model | `Embedding Model (L1.3)` | Rectángulo |
| Vector Store | `Vector Store` | Cilindro con fondo verde suave |
| Retrieval | `Retrieval (RAG — L1.5)` | Rectángulo con fondo naranja suave |

**Flechas y anotaciones en flechas:**

| Flecha | Etiqueta/Anotación |
|--------|-------------------|
| Usuario → Interfaz | (sin etiqueta) |
| Interfaz → Constructor de Prompt | `Query del usuario` |
| Constructor de Prompt → LLM | `Prompt completo` + badge `Context Window — límite en tokens (L1.2)` |
| LLM → Verificador | `Output del modelo` + badge `tokens de salida — coste mayor (L1.7)` |
| Verificador → Respuesta | `Respuesta validada` |
| Knowledge Base → Embedding Model | `Documentos` |
| Embedding Model → Vector Store | `Vectores (L1.3)` |
| Petición → Vector Store (retrieval) | `Query vectorizada` |
| Vector Store → Retrieval | `Fragmentos relevantes` |
| Retrieval → Constructor de Prompt | `Contexto recuperado` |
| Flecha entrada al LLM | badge adicional: `tokens de entrada — cacheables (L1.7)` |

**Anotaciones flotantes adicionales:**
- Junto al LLM: `"El modelo solo ve lo que está en la Context Window (L1.2)"`
- Junto al System Prompt: `"Versionable, testeable, revisable en PR (L1.6)"`
- Junto al path RAG: `"El conocimiento vive fuera del modelo — actualizable sin reentrenar (L1.5)"`
- Junto al Verificador: `"El output es tan bueno como el diseño del sistema completo"`

**Flujo de construcción durante el video:**
1. Aparece `Usuario` + `Interfaz` + flecha
2. Aparece `Constructor de Prompt` con sección de System Prompt anotada
3. Aparece `LLM` con anotación de temperatura
4. Aparece `Verificador` + `Respuesta`
5. Aparece la ruta completa de RAG (Knowledge Base → Embedding → Vector Store → Retrieval → Prompt)
6. Se añaden las anotaciones de tokens y coste en las flechas principales
7. Vista final: diagrama completo con todas las referencias a lecciones visibles simultáneamente

---

## CTA de afiliación

**Texto exacto para incluir en el video y en la descripción:**

"Este tipo de sistema, en producción, puede desplegarse en DigitalOcean por menos de 20 dólares al mes. El link está en la descripción."

**Formato para descripción de YouTube:**
```
Despliega tu propio sistema LLM en producción por menos de $20/mes:
[link de afiliado DigitalOcean]

En el Semester 2 veremos cómo conectar las piezas que nos faltan: agentes, orquestación, y sistemas que actúan, no solo responden.
```
