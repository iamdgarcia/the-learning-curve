# Testing en Sistemas No Deterministas

**Semestre:** Bonus — Production Essentials
**Lección:** B.2
**Duración estimada:** 7-9 min
**Formato visual:** Cámara + diagrama en Slides PDF

## Objetivo de la lección
Tener confianza en el sistema sin poder hacer assertions exactas sobre el output.

---

## Guión

### Intro (20-30 seg)

Imagina que construiste un test para tu sistema de agentes. El test pasa hoy. Mañana lo corres de nuevo, sin cambiar nada, y falla. No porque el sistema haya cambiado — sino porque el LLM generó una formulación diferente.

Bienvenido al problema central del testing en sistemas no deterministas. Las reglas cambian. Y si no adaptas tu estrategia de testing, vas a producción sin red de seguridad.

---

### Bloque 1: Por qué los tests tradicionales no funcionan

El test unitario clásico tiene una estructura que todos conocemos: dado un input, el output es exactamente este valor, y hacemos assert. Es simple, es rápido, y es completamente inútil aplicado directamente a un sistema LLM.

El mismo input puede producir outputs lingüísticamente distintos pero semánticamente equivalentes. "El cliente ha sido notificado" y "Se ha enviado notificación al cliente" son respuestas igualmente correctas para la misma pregunta. Un assert de igualdad exacta rechazaría una de las dos.

Peor aún: incluso con temperatura cero, los LLMs no son estrictamente reproducibles entre versiones del modelo, entre regiones de inferencia, o después de ciertos tipos de actualizaciones del proveedor. El software que escribes tú es determinista. Los modelos de lenguaje, por diseño, no lo son.

Esto no significa que no puedas testear el sistema. Significa que tienes que cambiar qué testeas y cómo.

---

### Bloque 2: El golden dataset — tu primer entregable

Antes de hablar de estrategias de testing, hay un entregable que todo sistema LLM en producción debe tener: el golden dataset.

Un golden dataset es un conjunto de inputs representativos del sistema, junto con los criterios de evaluación que cada output debe cumplir. No el output exacto — los criterios. Cubriendo los casos típicos, los casos límite, y los casos que históricamente han causado problemas.

La clave está en la distinción. No dices "para este input, el output correcto es esta frase exacta". Dices "para este input, el output correcto debe cumplir estas propiedades: debe tener menos de 200 palabras, debe mencionar el nombre del cliente, no debe contener lenguaje de disculpa, y debe terminar con una llamada a la acción".

Si no tienes un golden dataset antes de hacer el primer deploy, no sabes si tu sistema funciona. No lo sabes en desarrollo, no lo sabes en staging, y definitivamente no lo sabes en producción. El golden dataset es la diferencia entre "creo que funciona" y "tengo evidencia de que funciona".

---

### Bloque 3: Las tres estrategias de testing

Hay tres estrategias de testing para sistemas LLM, y no son alternativas — son complementarias. Miremos el diagrama mientras las explico.

[Pausa — mostrar diagrama del pipeline de testing]

La primera estrategia es el property-based testing. Dado el output del sistema, compruebas propiedades estructurales y formales: ¿el output tiene menos de N palabras? ¿El JSON es válido y tiene los campos requeridos? ¿El output no contiene palabras de la lista prohibida? ¿El output está en el idioma correcto?

Esta estrategia es rápida, barata, y completamente automática. Puedes correrla en cada commit, en segundos, sin coste de API. Su limitación es que solo captura propiedades que puedes expresar como reglas formales. No te dice si el output es correcto semánticamente, solo si tiene la forma correcta.

La segunda estrategia es LLM-as-a-judge. Usas un LLM, típicamente el mismo u otro de calidad comparable, para evaluar si el output del sistema es correcto dado el criterio de evaluación. Le das al juez el input, el criterio de evaluación, y el output del sistema. El juez devuelve una puntuación y una justificación.

Esta estrategia es mucho más potente. Puede evaluar corrección semántica, tono, adecuación al contexto, cosas que ninguna regla formal puede capturar. Su limitación es doble: tiene coste de API por cada evaluación, y el juez tiene su propio margen de error. Un juez con una tasa de error del 5% es útil, pero debes conocer ese margen cuando interpretas los resultados.

La tercera estrategia es la evaluación humana. Un evaluador humano revisa el output y decide si es correcto. Es la más fiable de las tres, captura matices que ningún modelo automatizado detecta, y es imprescindible para construir el golden dataset inicial.

Su coste es alto — en tiempo y en dinero — así que en producción se usa para muestras representativas del tráfico real y para los casos ambiguos que el LLM-as-a-judge marca con baja confianza. No para evaluar cada request.

---

### Bloque 4: El ciclo de mejora continua

El testing no es un evento que ocurre antes del deploy. Es un ciclo continuo.

El sistema va a producción. Con observabilidad activa — como vimos en la lección anterior — detectas un caso problemático. Un output que no debería haber pasado, un fallo que no anticipaste. Tomas ese caso, lo añades al golden dataset con su criterio de evaluación, y ahora tienes un dataset un caso más robusto.

Esto parece simple, pero tiene una implicación importante: el golden dataset crece con el tiempo. En el primer deploy puede tener 50 casos. Seis meses después tiene 200. Un año después tiene 500. Cada uno de esos casos adicionales representa un tipo de fallo real que el sistema encontró en producción y que ya no puede repetir sin ser detectado.

El resultado es que el sistema mejora de forma sistemática, no por intuición del equipo, sino porque el dataset refleja el espacio real de problemas que el sistema enfrenta.

---

### Bloque 5: El threshold de release — la decisión que tienes que tomar antes

Tienes un golden dataset de 100 casos. Corres el pipeline de evaluación. El sistema pasa 87 de los 100. ¿Haces deploy?

No hay una respuesta universal, pero hay una cosa segura: si no has definido el threshold antes de ver ese número, vas a tomar la decisión bajo presión y con sesgo. "87 de 100 es bastante bueno, ¿no?" Es una frase que no debes estar diciendo el día del release.

El threshold depende de la criticidad del sistema. Un sistema que genera borradores de email internos y un sistema que procesa transacciones financieras no tienen el mismo umbral. Para el primero, 85 de 100 puede ser aceptable si la evaluación humana confirma que los 15 casos restantes son errores menores. Para el segundo, puede que necesites 99 de 100 solo en property checks, más evaluación humana de todos los casos que fallen LLM-as-a-judge.

La regla de esta lección: define el threshold antes de construir el sistema, no después de ver los resultados. Una vez que ves los números, el sesgo de confirmación hace que cualquier threshold razonable parezca demasiado exigente o demasiado permisivo dependiendo de cuánta presión hay para desplegar.

---

### Bloque 6: Regression testing — el uso más importante

El uso más crítico del golden dataset no es el test inicial de release. Es la regresión continua.

Antes de cualquier cambio en el sistema — un nuevo prompt, un agente adicional, un verifier que reemplaza a otro, un modelo diferente — corres el golden dataset completo y comparas el score con el baseline. Si el score baja, el cambio introduce regresión y no se mergea hasta entender por qué.

Esto resuelve un problema que cualquier equipo de ingeniería con sistema LLM ha vivido: haces un cambio que mejora una clase de inputs y empeora otra que no habías contemplado. Sin regression testing, el segundo efecto aparece en producción. Con regression testing, aparece en el pipeline de CI, antes del merge.

El golden dataset es, en este sentido, la especificación ejecutable del comportamiento del sistema. No lo que el sistema hace, sino lo que el sistema debe hacer. Y cada vez que el sistema se aleja de esa especificación, el pipeline te lo dice antes de que llegue al usuario.

---

### Decisión de diseño (cierre, ~1 min)

La decisión de esta lección tiene dos partes.

Primera: cuándo construir el golden dataset. La respuesta es antes de escribir el primer agente de producción. No después de que el sistema funcione en demos. Antes. Porque el golden dataset es la forma de definir qué significa "funcionar" para tu sistema específico.

Segunda: qué porcentaje del golden dataset debe pasar para hacer deploy. La respuesta depende de la criticidad, y debe estar escrita antes de ver los resultados. Para sistemas que afectan directamente a usuarios en decisiones importantes, el umbral es alto. Para sistemas auxiliares de bajo riesgo, puede ser más permisivo. Pero tiene que estar definido, y tiene que ser verificable antes de cada release.

Si sales de esta lección con una sola tarea concreta: escribe hoy los primeros 20 casos de tu golden dataset. No esperes a tener el sistema completo. Esos 20 casos van a revelar asunciones sobre el comportamiento que no sabías que tenías.

---

## Spec del diagrama

**Tipo:** Slides PDF (dos diapositivas o un panel amplio)

**Elementos:**

Panel principal — Pipeline de testing:
- Columna izquierda: "Golden Dataset" — caja con ejemplos de pares input/criterio (no input/output exacto). Anotación: "100 casos representativos"
- Flecha central descendente: "Sistema de agentes procesa cada input"
- Columna central: "Output del sistema" — caja de output
- Tres ramas paralelas a la derecha del output, cada una con su evaluador:
  - Rama 1: "Property checks" — caja con ejemplos: longitud, formato JSON, palabras prohibidas. Etiqueta inferior: "Coste: bajo / Velocidad: alta / Cobertura: formal"
  - Rama 2: "LLM-as-a-judge" — caja con descripción: "LLM evalúa si output cumple criterio". Etiqueta inferior: "Coste: medio / Velocidad: media / Cobertura: semántica"
  - Rama 3: "Evaluación humana" — caja: "Revisor humano para muestra aleatoria y casos ambiguos". Etiqueta inferior: "Coste: alto / Velocidad: baja / Cobertura: total"
- Las tres ramas convergen en: "Score agregado" — número de casos superados sobre total
- Flecha final: "Comparar con threshold predefinido"
- Dos nodos finales: "DEPLOY" (verde) y "NO DEPLOY — investigar" (rojo)

Panel secundario — Ciclo de mejora:
- Circulo: "Producción" -> "Fallo detectado (con observabilidad)" -> "Caso añadido al golden dataset" -> "Dataset más robusto" -> "Próximo release más confiable" -> vuelve a "Producción"

**Flujo visual:**
- Fondo claro, código de colores consistente: verde para evaluadores exitosos, rojo para fallo/no deploy
- Las anotaciones de coste/velocidad en cada evaluador como etiquetas secundarias en gris
- El threshold aparece en la comparación final como línea horizontal con valor numérico: "Threshold: 90/100"
