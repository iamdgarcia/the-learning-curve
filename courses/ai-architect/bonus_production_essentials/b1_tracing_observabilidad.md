# Tracing y Observabilidad

**Semestre:** Bonus — Production Essentials
**Lección:** B.1
**Duración estimada:** 7-9 min
**Formato visual:** Cámara + diagrama Excalidraw en pantalla

## Objetivo de la lección
Saber exactamente qué hizo el sistema y por qué, cuando algo falla en producción.

---

## Guión

### Intro (20-30 seg)

Son las 2 de la mañana. Tienes una alerta. El sistema de agentes que desplegaste la semana pasada está fallando para el 15% de los usuarios. ¿Qué haces?

Si tienes observabilidad, en cinco minutos sabes qué agente falla, con qué input, y cuántos tokens está gastando antes de hacerlo. Si no la tienes, pasas la noche haciendo suposiciones.

Esta lección es sobre no quedarte sin respuestas cuando algo va mal.

---

### Bloque 1: El problema concreto

Cuando algo falla en un sistema de agentes en producción, las preguntas que necesitas responder son siempre las mismas. ¿Qué agente falló? ¿Qué input recibió ese agente? ¿Qué output produjo antes de fallar? ¿Cuántos tokens consumió? ¿Cuánto costó ese error?

En software tradicional, tienes stack traces. Tienes logs de errores. El código es determinista y reproducible.

En un sistema de agentes, la situación es distinta. Una misma request pasa por múltiples agentes, cada uno con su propio contexto. Hay llamadas al LLM que tardan segundos. Hay herramientas que se invocan. Hay decisiones que se toman basadas en contenido semántico, no en condiciones booleanas. Si no instrumentas explícitamente el sistema, cuando algo falla solo ves el síntoma: el output final no es correcto, o el sistema tardó demasiado, o hubo un error HTTP 500. Pero no sabes dónde ni por qué.

Eso no es suficiente para producción.

---

### Bloque 2: Tracing distribuido — el concepto central

El tracing distribuido es la solución. La idea es simple: cada request que entra al sistema genera un trace ID único. Ese ID se propaga a cada componente del sistema. Cada unidad de trabajo — una llamada al LLM, una invocación de herramienta, la ejecución de un agente — crea un span dentro de ese trace. El resultado es un árbol: la request completa como raíz, y cada componente como nodo hijo.

Miremos el diagrama.

[Pausa — mostrar diagrama completo]

Esta es una request completa en un sistema con dos agentes. La request entra y el orquestador crea el span raíz. Dentro de ese span, el orquestador hace una llamada al LLM para decidir qué agentes activar — eso es el span 1.1. También invoca una herramienta para obtener contexto — el span 1.2.

Luego el orquestador lanza dos agentes en paralelo: el Agente A y el Agente B. Cada uno tiene su propio span. Cada uno hace su propia llamada al LLM. El Agente B, fíjate, tiene su span marcado en rojo: la primera llamada al LLM falló y el sistema hizo un retry. El retry tuvo éxito, pero costó tiempo extra y tokens extra.

Eso es exactamente lo que necesitas ver cuando hay un problema. No "el sistema tardó 8 segundos en vez de 3". Sino "el Agente B hizo retry en el span 3.1, añadió 2.3 segundos, y eso ocurrió porque la primera llamada devolvió un error de timeout del proveedor".

---

### Bloque 3: Qué registrar en cada span

El tracing es útil solo si registras la información correcta. En cada span de una llamada al LLM debes capturar: el input completo que recibió el modelo, el output completo que devolvió, la latencia de esa llamada específica, los tokens de entrada y de salida por separado, el coste calculado, si fue un hit de caché de prompt, y si hubo retry y cuántas veces.

En cada span de una llamada a una herramienta: qué herramienta se invocó, con qué argumentos, qué devolvió, y cuánto tardó.

En cada span de un agente: qué instrucción recibió el agente, qué decisión tomó, y cuál fue su output final al orquestador.

Puede parecer mucho. Pero en producción, cada uno de esos campos ha salvado una investigación de fallo en algún momento. El coste de no tenerlos es mucho mayor que el coste de almacenarlos.

---

### Bloque 4: Niveles de logging — la decisión que más te importa en producción

No puedes — ni debes — loggear lo mismo en desarrollo que en producción. Hay tres niveles que tienes que definir explícitamente antes de desplegar.

Desarrollo: log todo. Inputs completos, outputs completos, decisiones intermedias, todo el contenido. Estás entendiendo el sistema, necesitas visibilidad total.

Staging: log todo excepto contenido de usuario real. Las métricas, las latencias, los tokens, los errores — todo. Pero el contenido que ingresa el usuario se anonimiza o se sustituye por datos sintéticos. Staging es el entorno donde identificas problemas de rendimiento antes de producción. No necesitas datos reales para eso.

Producción: aquí la regla es clara y no negociable. Métricas y errores, siempre. El contenido de las conversaciones del usuario, solo bajo dos condiciones: el usuario ha dado su consentimiento explícito, o hay un incidente activo que requiere ese nivel de diagnóstico. Y en el segundo caso, el acceso debe ser auditado, temporal, y restringido a la persona que está resolviendo el incidente.

La razón es simple: los inputs de tus usuarios pueden contener información confidencial. Contratos, datos médicos, comunicaciones privadas. Tu sistema de observabilidad no puede ser un vector de fuga de datos.

---

### Bloque 5: El dashboard mínimo de producción

Con los traces almacenados, necesitas un dashboard operacional. El mínimo viable tiene cinco elementos.

Latencia por agente, en tres percentiles: P50, P95, y P99. El P50 te dice el caso típico. El P95 te dice lo que experimentan tus usuarios en mal día. El P99 te dice tus casos extremos — y en sistemas de agentes, el P99 puede ser sorprendentemente alto si algún agente tiene un comportamiento de tail latency problemático.

Tasa de error por agente. No el error total del sistema, sino desagregado. Si el Agente B falla el 12% de las veces y el Agente A falla el 0.3%, eso te dice dónde concentrar el trabajo.

Coste total por hora. No por semana, por hora. En sistemas de agentes, un prompt mal diseñado que consume el doble de tokens del necesario puede duplicar tu factura. Quieres ver eso el mismo día que ocurre, no en la factura del mes.

Alertas configuradas. No basta con tener el dashboard — necesitas alertas automáticas cuando cualquier métrica supera el umbral que has definido. El P95 de latencia del sistema supera X segundos: alerta. La tasa de error del Agente B supera Y por ciento: alerta. El coste por hora supera Z: alerta.

---

### Bloque 6: Por qué la observabilidad es también la herramienta de mejora

Hasta ahora hemos hablado de detectar fallos. Pero la observabilidad tiene otro uso igual de importante: mejorar el sistema de forma sistemática.

Si no sabes qué agentes son más lentos, no puedes optimizarlos. Si no sabes qué agentes fallan más frecuentemente, no puedes decidir cuál reforzar primero. Si no sabes cuánto cuesta cada tipo de request, no puedes priorizar la reducción de coste donde importa.

Los traces acumulados en producción son tu fuente de verdad. Son los casos reales que tu sistema ha procesado. Con el tiempo, te dicen qué partes del diseño son problemáticas bajo carga real, qué tipos de input generan los errores más frecuentes, y dónde el sistema gasta tiempo y dinero de forma ineficiente.

Sin observabilidad, estás optimizando a ciegas. Con observabilidad, cada mejora está guiada por datos reales de producción.

---

### Decisión de diseño (cierre, ~1 min)

La pregunta práctica de esta lección es: cuando te sientas a desplegar tu sistema, ¿qué nivel de logging activas en cada entorno?

La regla que debes llevarte: en desarrollo, log todo sin excepción. Necesitas visibilidad total para entender el comportamiento del sistema. En producción, métricas y errores siempre, contenido de usuario nunca por defecto. Y cuando hay un incidente activo que requiere ver el contenido, el acceso debe ser explícito, auditado, y con tiempo limitado.

Antes de hacer el primer deploy de cualquier sistema de agentes, tienes que haber respondido tres preguntas: ¿qué traces estoy capturando? ¿Dónde los almaceno? ¿Qué dashboard y qué alertas tengo configurados?

Si no tienes respuesta a las tres, no estás listo para producción.

---

## Spec del diagrama

**Tipo:** Excalidraw

**Elementos:**
- Nodo raíz: "Request entrante" (rectángulo azul)
- Span 1: "Orquestador" — duración 8.2s, estado: OK
- Span 1.1: "LLM call — decisión de routing" — duración 1.1s, tokens: 420 entrada / 85 salida, estado: OK, hit de caché: no
- Span 1.2: "Tool call — obtener contexto" — duración 0.3s, estado: OK
- Span 2: "Agente A" — duración 3.4s, estado: OK (se ejecuta en paralelo con Span 3)
- Span 2.1: "LLM call — análisis" — duración 2.9s, tokens: 1200 entrada / 340 salida, estado: OK
- Span 3: "Agente B" — duración 6.1s, estado: OK con retry (se ejecuta en paralelo con Span 2)
- Span 3.1: "LLM call — síntesis (intento 1)" — duración 2.0s, estado: ERROR (timeout), resaltado en rojo
- Span 3.2: "LLM call — síntesis (intento 2, retry)" — duración 3.8s, tokens: 980 entrada / 290 salida, estado: OK
- Nodo final: "Response" (rectángulo verde)

**Flujo visual:**
- Árbol vertical descendente con ramificación paralela entre Span 2 y Span 3
- Cada span como caja con campos internos: duración, tokens (donde aplica), estado
- El Span 3.1 con fondo rojo y etiqueta "TIMEOUT — RETRY"
- Línea de tiempo horizontal encima del árbol mostrando duración total: 8.2s
- Leyenda en esquina: verde = OK, rojo = ERROR, naranja = RETRY
- Anotación lateral: "Sin este árbol, solo ves: 'el sistema tardó 8 segundos'" apuntando al nodo raíz
