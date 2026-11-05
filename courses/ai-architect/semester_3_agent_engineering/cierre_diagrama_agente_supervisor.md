# Cierre del Semestre 3 — Diagrama: agente completo con supervisor y memoria

**Semestre:** 3 — Agent Engineering
**Lección:** Cierre de semestre
**Duración estimada:** 4-5 min
**Formato visual:** Cámara + diagrama Excalidraw construido en pantalla en tiempo real

## Objetivo de la lección

Integrar los siete conceptos del semestre en un único diagrama de arquitectura de agente completo, mostrando cómo se conectan en un sistema real.

---

## Guión

### Intro (20-30 seg)

Siete lecciones. Siete conceptos. Esta lección los pone todos juntos en un único diagrama. Mientras lo construyo en pantalla, voy a conectar cada elemento con la lección que lo enseñó. Al final del diagrama, tienes la arquitectura completa de un agente de producción.

---

### Construcción del diagrama (bloque principal, ~3 min)

Empezamos por el centro del sistema.

El agente orquestador. Tiene tres fases: percibe el entorno, razona sobre lo que percibe, y actúa. Eso es lo que vimos en la lección 3.1. Aquí está en el centro del diagrama porque todo lo demás gira alrededor de él.

Ahora añado las herramientas. El agente no actúa en el vacío, actúa a través de herramientas. Y esas herramientas tienen niveles de riesgo: algunas son de solo lectura, otras modifican estado, otras ejecutan acciones irreversibles. Eso fue la lección 3.2. Las conecto al agente con flechas que indican el tipo de acción.

Sobre el output de esas herramientas, añado el verifier. El agente produce un resultado, el verifier lo valida antes de que avance al sistema siguiente. Schema, formato, reglas de negocio. Eso fue la lección 3.3. El verifier vive entre el agente y el sistema destino, no dentro del agente.

Ahora el supervisor. El supervisor es humano-on-the-loop. Está en la cima del diagrama porque tiene visibilidad sobre todo el sistema. No interviene en cada paso, solo en los que requieren aprobación. Que son exactamente las herramientas de alto riesgo que marcamos antes. Eso fue la lección 3.4. Añado una línea desde el supervisor hacia el punto de aprobación, que vive antes de ejecutar cualquier herramienta de nivel alto.

Dentro del agente, añado el loop de reflexión. Después de cada acción, el agente puede evaluarse a sí mismo antes de entregar el resultado. Modo generativo, modo crítico, decisión. Con el contador de iteraciones y la salida al supervisor si no converge. Eso fue la lección 3.5.

A la izquierda del agente, los compartimentos de memoria. In-context, que es la conversación actual. Long-term, que son las preferencias del usuario y el conocimiento del dominio. El agente lee de ellas al inicio y escribe a ellas cuando produce información que debe persistir. Eso fue la lección 3.6.

Y a la derecha del agente, un sub-agente conectado con comunicación síncrona. El agente orquestador, cuando necesita un resultado específico para continuar, llama directamente al sub-agente y espera su respuesta. Eso fue la lección 3.7. Si la comunicación fuera asíncrona, habría una cola entre ellos.

---

### Lectura del diagrama completo (30 seg)

Ahora para un segundo y mira el diagrama completo.

Supervisor en la cima, con línea de visibilidad sobre todo. Agente orquestador en el centro, con su loop de percepción-razonamiento-acción. Herramientas a su derecha con niveles de riesgo marcados. Verifier en el output. Punto de aprobación supervisor antes de las herramientas de alto riesgo. Loop de reflexión interno. Memoria en sus cuatro formas. Sub-agente conectado síncronamente.

Este es un agente completo. No un prototipo, una arquitectura de producción.

---

### CTA y cierre (30-40 seg)

Eso es el Semestre 3.

Sabemos qué es un agente. Sabemos cómo diseñar sus herramientas. Sabemos cómo validar sus outputs. Sabemos cómo supervisarlo. Sabemos cómo hace que se corrija a sí mismo. Sabemos cómo gestiona su memoria. Y sabemos cómo se comunica con otros agentes.

En el Semester 4, que es donde nadie está enseñando realmente, veremos cómo diseñar sistemas con 10, 20, o más de estos agentes trabajando juntos. Cómo se orquestan, cómo se distribuye el trabajo, y cómo el sistema entero sigue siendo manejable cuando la complejidad escala. Link en la descripción.

---

## Spec del diagrama

**Tipo:** Excalidraw construido en tiempo real durante el guión

**Elementos (en orden de aparición):**

1. Caja central "Agente Orquestador" con tres sub-etiquetas internas: "Percibe / Razona / Actúa" (L3.1)

2. Tres cajas de herramientas a la derecha del agente, diferenciadas por color:
   - Verde: "Herramienta de bajo riesgo (solo lectura)" — flechas directas desde agente
   - Amarillo: "Herramienta de riesgo medio (modifica estado)" — flechas con punto de validación
   - Rojo: "Herramienta de alto riesgo (irreversible)" — flecha con rombo de aprobación (L3.2)

3. Caja "Verifier" entre el agente y la caja "Sistema destino":
   - Valida: schema, formato, reglas de negocio
   - Etiqueta: "L3.3 — Validación de output"

4. Caja "Supervisor (humano)" en la cima del diagrama:
   - Línea de visibilidad punteada hacia todo el sistema
   - Flecha sólida hacia "Punto de aprobación" que conecta con herramienta de alto riesgo
   - Etiqueta: "L3.4 — Human-on-the-loop"

5. Loop de reflexión dentro del agente (representado como sub-diagrama interior):
   - Mini-rombo "Suficientemente bueno?" con rama de vuelta
   - Contador "N iteraciones"
   - Flecha de escape hacia supervisor si N = 0
   - Etiqueta: "L3.5 — Reflexión"

6. Dos compartimentos de memoria a la izquierda del agente:
   - "In-context" con flecha R+W, etiqueta "conversación actual"
   - "Long-term (episodic + semantic)" con flecha R al inicio de sesión y W al cerrar
   - Etiqueta: "L3.6 — Memoria"

7. Caja "Sub-agente" a la derecha inferior:
   - Flecha bidireccional síncrona con etiqueta "petición / respuesta"
   - Etiqueta: "L3.7 — Comunicación síncrona"

**Flujo visual:** El diagrama se construye incrementalmente, un elemento por bloque del guión. Cada elemento añadido aparece resaltado brevemente antes de integrarse visualmente con el resto. El diagrama completo tiene una lectura de arriba (supervisor) hacia abajo y de izquierda (memoria) hacia derecha (herramientas y sub-agente), con el agente orquestador como núcleo central.

**Colores:**
- Supervisor: azul oscuro (autoridad)
- Agente orquestador: gris oscuro (núcleo)
- Herramientas: verde / amarillo / rojo según nivel de riesgo
- Verifier: naranja (validación)
- Memoria: morado (persistencia)
- Sub-agente: gris claro (componente secundario)
- Loop de reflexión: línea discontinua interior al agente
