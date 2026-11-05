# Latencia y Escalado

**Semestre:** Bonus — Production Essentials
**Lección:** B.4
**Duración estimada:** 7-9 min
**Formato visual:** Cámara + diagrama en Slides PDF

## Objetivo de la lección
Diseñar para el rendimiento antes de que la latencia o el coste sean un problema, no después.

---

## Guión

### Intro (20-30 seg)

Tienes el sistema funcionando. Los tests pasan. La seguridad está diseñada. Ahora la pregunta que te falta responder: ¿cuánto tarda? ¿Y cuánto cuesta?

En la mayoría de sistemas de software, el rendimiento se optimiza después de que hay evidencia de un problema. En sistemas de agentes, esa estrategia es cara. Porque los problemas de latencia y coste en sistemas LLM se resuelven principalmente cambiando el diseño, y cambiar el diseño después de que el sistema está en producción es costoso.

Esta lección es sobre tomar las decisiones de rendimiento en el momento correcto: antes del primer deploy.

---

### Bloque 1: Las tres fuentes de latencia en sistemas de agentes

Para diseñar para rendimiento, primero necesitas entender de dónde viene la latencia. En un sistema de agentes, hay tres fuentes, y no tienen el mismo peso.

La primera y dominante es la latencia de las llamadas al LLM. Cada llamada tarda entre uno y diez segundos dependiendo del modelo, el tamaño del contexto, y la longitud del output esperado. En un sistema con múltiples agentes, esta es la fuente de latencia que domina todo lo demás. Si tienes cinco agentes y cada uno hace una llamada al LLM, el tiempo de esas llamadas es tu latencia base.

La segunda fuente son las llamadas a herramientas externas: APIs de terceros, bases de datos, búsquedas web. Una búsqueda web puede tardar entre 0.5 y 3 segundos. Una llamada a una API externa puede añadir otro segundo. Estas latencias son menos predecibles que las llamadas al LLM y dependen de factores fuera de tu control — la disponibilidad y rendimiento del servicio externo.

La tercera fuente es el overhead del orquestador: serialización, deserialización, paso de mensajes entre agentes, coordinación. En la mayoría de sistemas bien diseñados, este overhead es despreciable — decenas de milisegundos. Pero si el diseño del orquestador es ineficiente, si hay serialización de objetos grandes en cada paso, si hay polling innecesario, puede acumularse hasta hacerse notable.

La regla de optimización: ataca siempre la fuente dominante primero. En casi todos los sistemas de agentes, eso significa las llamadas al LLM.

---

### Bloque 2: Paralelización — la palanca más potente

Miremos el diagrama.

[Pausa — mostrar panel izquierdo del diagrama]

Este es un sistema sin optimizar. Diez llamadas al LLM en secuencia. Cada una tarda 3 segundos. Total: 30 segundos. La secuencia tiene sentido solo si cada llamada depende del output de la anterior.

Ahora el panel derecho.

[Pausa — mostrar panel derecho del diagrama]

Mismo trabajo. Las mismas diez llamadas al LLM. Pero ahora hemos identificado cuáles son independientes entre sí. Las primeras cuatro pueden ejecutarse en paralelo — no necesitan el resultado de ninguna de las otras para hacer su trabajo. Luego hay dos rondas más. Total: 9 segundos en vez de 30.

El diseño del sistema no cambió en términos de lo que hace. Cambió en términos de cuándo lo hace.

La paralelización es la palanca más potente disponible antes de que exista un problema de rendimiento, porque es una decisión de diseño que se toma cuando se diseña el grafo de dependencias entre agentes. Si esperas a tener el sistema en producción y descubres que tardas 30 segundos, replantear las dependencias es un rediseño significativo. Si lo decides antes, es parte del diseño inicial.

La pregunta concreta que tienes que hacerte al diseñar cada flujo: ¿cuáles de estas llamadas al LLM son independientes entre sí? Las independientes van en paralelo.

---

### Bloque 3: Streaming para la latencia percibida

Hay una distinción importante entre latencia real y latencia percibida.

La latencia real es cuánto tarda el sistema en producir el output completo. La latencia percibida es cuánto tarda el usuario en ver que el sistema está respondiendo.

Streaming mejora la latencia percibida sin cambiar la latencia real. Si el modelo tarda 5 segundos en generar una respuesta completa, con streaming el usuario ve los primeros tokens en 0.5 segundos. El sistema sigue tardando 5 segundos en terminar, pero el usuario tiene la experiencia de una respuesta casi inmediata.

En interfaces conversacionales o dashboards donde el usuario espera activamente, streaming puede ser la diferencia entre una experiencia que se siente rápida y una que se siente lenta, sin ningún cambio en la arquitectura subyacente.

La implementación de streaming no cambia el diseño del sistema de agentes — es una decisión de cómo expones el output al usuario. Pero es una decisión que tienes que tomar antes de diseñar la interfaz, no después.

---

### Bloque 4: Caching a nivel de sistema

Además del prompt caching que muchos proveedores ofrecen para prefijos de contexto, puedes diseñar caching a un nivel más alto: cachear el output completo de un agente para un input determinado.

El caso de uso más claro: tienes un agente que analiza documentos. El mismo documento puede llegar 100 veces al día en requests de distintos usuarios. Sin caching, haces 100 llamadas al LLM y pagas por 100 análisis. Con caching, haces una llamada, cacheas el resultado, y los 99 siguientes son instantáneos.

El caching a nivel de agente reduce tanto la latencia como el coste. En el diagrama, fíjate en la anotación del sistema optimizado: el coste base es X, pero con caching activo para entradas recurrentes, el coste efectivo cae a 0.4X.

La pregunta de diseño: ¿qué partes de tu sistema procesan inputs que se repiten con alta frecuencia? Para esas partes, el caching es una optimización de primer orden.

Dos consideraciones al diseñar el caching: la invalidación — cuándo el resultado cacheado deja de ser válido — y la granularidad — a qué nivel de abstracción cacheas. Cachear a nivel de documento entero es simple pero puede desperdiciar espacio. Cachear a nivel de sección del documento es más granular pero más complejo de implementar.

---

### Bloque 5: Escalar horizontal — cuándo tiene sentido

Cuando el diseño ya está optimizado — las llamadas independientes están en paralelo, el caching está activo — y la latencia sigue siendo mayor de lo aceptable, el siguiente paso es el escalado horizontal: más instancias del sistema procesando requests en paralelo.

Pero hay una regla importante: escalar un diseño ineficiente solo amplifica la ineficiencia.

Si tu sistema tarda 30 segundos porque tiene 10 llamadas secuenciales que podrían ser paralelas, añadir más instancias te permite atender más usuarios simultáneamente, pero cada usuario sigue esperando 30 segundos. El problema de latencia no se resuelve con escala horizontal — se resuelve con paralelización en el diseño.

El escalado horizontal resuelve un problema distinto: throughput. Cuántas requests puede manejar el sistema simultáneamente. Si tu sistema está optimizado en latencia pero tiene picos de tráfico que saturan el sistema, el escalado horizontal añade capacidad.

La secuencia correcta: primero optimiza el diseño para latencia. Luego escala horizontalmente para throughput.

---

### Bloque 6: El SLA de latencia — la decisión que toma todas las demás

Todo lo que hemos hablado — paralelización, streaming, caching, escalado — sirve para alcanzar un objetivo específico. Y ese objetivo tiene que estar definido antes de construir.

El SLA de latencia son los compromisos que tu sistema tiene sobre qué latencia los usuarios pueden esperar. Se expresa en percentiles: P50, P95, P99.

El P50 es la latencia que experimenta el usuario mediano — la mitad de las requests son más rápidas, la mitad más lentas. El P95 es la latencia que no supera el 95% de las requests. El P99 es el caso extremo — el 1% más lento.

Miremos la tabla del diagrama.

[Pausa — señalar la tabla]

Los sistemas de procesamiento por lotes — donde el usuario no espera una respuesta en tiempo real — pueden tolerar latencias de minutos. El diseño puede ser más secuencial, más robusto, sin necesidad de streaming.

Los sistemas near-real-time — donde el usuario espera una respuesta en segundos, como un chatbot o un asistente de búsqueda — necesitan diseño con paralelización activa, streaming, y caching. P95 de 5-10 segundos es razonable. P99 puede ser más alto y aun así aceptable si los casos extremos son infrecuentes.

Los sistemas real-time — donde la latencia tiene que ser sub-segundo — requieren un diseño radicalmente diferente. Modelos más pequeños, contextos más cortos, sin herramientas externas, posiblemente respuestas en caché para el espacio de inputs esperados. Si tu SLA requiere P99 menor a un segundo y estás usando un LLM de frontera con contextos largos, el diseño no puede cumplir el SLA. Tienes que cambiar uno de los dos.

La regla: define el SLA antes de construir. Porque una vez que ves el SLA y el diseño juntos, puedes detectar inconsistencias antes de escribir código. Si el SLA requiere P95 menor a 3 segundos y el diseño tiene 8 llamadas secuenciales al LLM, esa inconsistencia existe antes del primer deployment. Con el SLA definido previamente, la ves en el diseño. Sin el SLA, la ves en producción.

---

### Decisión de diseño (cierre, ~1 min)

La decisión de esta lección: para tu SLA de latencia, ¿qué partes del sistema paralelizar primero?

La respuesta estructurada: empieza por las llamadas al LLM que son independientes entre sí. Si ya las tienes todas en paralelo y la latencia sigue siendo mayor de lo que el SLA permite, el cuello de botella ya no son las llamadas al LLM — hay que buscar otro lado. Puede ser una herramienta externa lenta, puede ser el tamaño del contexto, puede ser que el SLA no es alcanzable con el diseño actual.

Y si el cuello de botella es el diseño, la única solución es cambiar el diseño. El escalado horizontal no lo resuelve. Más potencia de cómputo no lo resuelve. Mejor hardware de inferencia ayuda en el margen pero no cambia el orden de magnitud.

Antes de cerrar: define hoy el SLA de latencia de tu sistema. P50, P95, P99. Ponlo en el documento de diseño, junto al threshold del golden dataset de la lección anterior. Esas dos decisiones, tomadas antes de escribir código, van a guiar las demás mejor que cualquier optimización reactiva después del deploy.

---

## Spec del diagrama

**Tipo:** Slides PDF (dos paneles + tabla)

**Panel 1 — Sistema sin optimizar:**
- Diagrama vertical: 10 cajas en columna única, cada una etiquetada "LLM call N" con duración "3s"
- Flecha larga a la derecha etiquetada: "Tiempo total: 30s"
- Debajo: "Coste: X"
- Etiqueta encima: "10 llamadas secuenciales — cada una espera a la anterior"
- Color: fondo gris claro, cajas en azul oscuro

**Panel 2 — Sistema optimizado:**
- Diagrama con 3 rondas:
  - Ronda 1: 4 cajas en paralelo (horizontal), cada una "3s" — etiqueta: "Independientes: van en paralelo"
  - Ronda 2: 4 cajas en paralelo, "3s"
  - Ronda 3: 2 cajas en paralelo, "3s"
- Flecha a la derecha: "Tiempo total: 9s"
- Debajo: "Coste base: X / Con caching: 0.4X"
- Etiqueta encima: "Mismas 10 llamadas — dependencias rediseñadas"
- Color: fondo blanco, cajas en verde, flechas de paralelización en verde claro

**Tabla de SLA por tipo de sistema:**

| Tipo de sistema | P50 objetivo | P95 objetivo | Estrategia de diseño |
|---|---|---|---|
| Batch (procesamiento asíncrono) | < 60s | < 5 min | Secuencial permitido, throughput priorizado |
| Near-real-time (chatbot, asistente) | < 3s | < 8s | Paralelización + streaming + caching |
| Real-time (< 1s) | < 0.5s | < 1s | Modelos pequeños, contexto corto, respuestas precacheadas |

- Anotación en fila real-time: "Si usas LLM de frontera con contexto largo, este SLA no es alcanzable. Cambia el diseño o el SLA."

**Flujo visual:**
- Los dos paneles en paralelo horizontal para comparación directa
- Los números de latencia en grande y destacados (30s vs 9s)
- La tabla debajo con código de colores por fila: verde (batch), amarillo (near-real-time), rojo (real-time con advertencia)
