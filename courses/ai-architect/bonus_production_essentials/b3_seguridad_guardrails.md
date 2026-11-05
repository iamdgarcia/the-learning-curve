# Seguridad y Guardrails

**Semestre:** Bonus — Production Essentials
**Lección:** B.3
**Duración estimada:** 7-9 min
**Formato visual:** Cámara + diagrama Excalidraw en pantalla

## Objetivo de la lección
Diseñar la capa de seguridad de un sistema de agentes para los riesgos específicos de sistemas LLM, no solo los de software tradicional.

---

## Guión

### Intro (20-30 seg)

Tienes experiencia en seguridad de software. Sabes sobre autenticación, autorización, validación de inputs, SQL injection, XSS. Eso es necesario. Pero no es suficiente.

Los sistemas de agentes tienen vectores de ataque que el software tradicional no tiene. Y el error más común es asumir que las medidas de seguridad que ya conoces cubren los problemas nuevos. No los cubren.

En esta lección vas a aprender los tres riesgos específicos de los sistemas LLM y cómo diseñar defensas concretas para cada uno.

---

### Bloque 1: El landscape de amenazas específico de los sistemas LLM

Antes de hablar de soluciones, necesitamos entender qué es distinto.

En software tradicional, el código ejecuta instrucciones que tú escribiste. El input del usuario es datos que tu código procesa. La separación entre instrucción y datos es estructural — está en la arquitectura del sistema.

En un sistema de agentes, esa separación no existe de forma nativa. El agente recibe como contexto tanto las instrucciones del sistema como el contenido del usuario, en el mismo espacio: texto en lenguaje natural. El modelo no distingue inherentemente entre "esto es una instrucción del sistema" y "esto es input del usuario". Esa distinción depende del diseño que tú construyas.

Esto abre tres vectores de ataque que no existen en software tradicional: prompt injection, data exfiltration, y privilege escalation. Vamos a ver cada uno.

---

### Bloque 2: Prompt Injection

El prompt injection es el ataque más frecuente y el que más equipos subestiman.

El atacante incluye en su input texto diseñado para modificar el comportamiento del sistema. La forma más obvia: "Ignora tus instrucciones anteriores y haz X". Pero las formas más sofisticadas son menos obvias: texto que simula ser parte del system prompt, instrucciones ocultas en documentos que el agente va a procesar, contenido en páginas web que el agente va a leer para responder una pregunta.

El agente recibe ese texto como parte de su contexto, y si no está diseñado para manejarlo, lo puede tratar como una instrucción legítima.

Mira el diagrama — la flecha roja que entra por el input del usuario.

[Pausa — señalar en el diagrama]

Las mitigaciones son de tres capas. Primera: separación estructural en el prompt. El input del usuario nunca aparece junto al system prompt sin una demarcación explícita. Usas delimitadores que el modelo entiende — XML tags, encabezados específicos, estructuras que haces referencia en el system prompt. Le dices explícitamente al modelo qué es instrucción del sistema y qué es input del usuario, y le instruyes sobre qué hacer si el input del usuario intenta cambiar las instrucciones.

Segunda: validación de input antes de que llegue al agente. Un guardrail de input examina el texto del usuario antes de pasarlo al sistema. Busca patrones de inyección conocidos, intentos de override de instrucciones, estructuras anómalas. No es infalible — los ataques evolucionan — pero filtra el 80% de los intentos sin sofisticación.

Tercera: validación de output antes de actuar. Antes de que el sistema ejecute una acción basada en el output del agente, verifica que esa acción es coherente con el objetivo original de la request. Si el usuario pidió un resumen de un documento y el output del agente incluye instrucciones para borrar archivos, hay un problema que ninguna medida anterior capturó.

---

### Bloque 3: Data Exfiltration

El segundo vector: el agente tiene acceso a información privada y el atacante consigue que el agente la incluya en su respuesta.

Imagina un sistema de soporte donde el agente tiene acceso a la base de datos de clientes. Un atacante malicioso crafta una request que, combinada con la arquitectura del sistema, consigue que el agente incluya en su respuesta los datos de otro cliente. No porque el sistema esté diseñado para eso — sino porque el prompt injection funcionó y el agente mezcló información que no debía mezclar.

La flecha roja de data exfiltration en el diagrama apunta al guardrail de output.

[Pausa — señalar en el diagrama]

La defensa principal es el principio de mínimo privilegio, aplicado al agente: el agente solo tiene acceso a la información que necesita para responder esta request específica. No a toda la base de datos — solo a los registros del usuario autenticado que hizo la request. La superficie de exfiltración posible es proporcional a la cantidad de información a la que tiene acceso el agente.

La segunda defensa es el output filtering: el output del agente se valida antes de llegar al usuario. ¿El output contiene información que no estaba en el input original del usuario? ¿Contiene identificadores de otros usuarios, emails de personas distintas al solicitante, datos que el sistema no debería haber incluido? Este filtro no puede ser perfecto — requiere entender el dominio — pero puede capturar los casos más obvios.

---

### Bloque 4: Privilege Escalation

El tercer vector es el más técnico: el agente consigue ejecutar acciones para las que no está autorizado.

El escenario típico: el agente tiene herramientas disponibles para hacer llamadas a una API. Un atacante, a través de prompt injection o manipulación del contexto, consigue que el agente llame a endpoints que no debería. O consigue que el agente encadene herramientas de una forma que produce un efecto que ninguna herramienta individual permitiría por sí sola.

La flecha roja en el diagrama apunta a las herramientas.

[Pausa — señalar en el diagrama]

La defensa aquí es estructural y no hay atajo: el sistema de permisos de herramientas es el último bastión. No configures herramientas que el agente no debería poder usar bajo ninguna circunstancia. Si el agente de soporte al cliente nunca necesita acceder al módulo de administración de usuarios, ese módulo no es una herramienta disponible para ese agente. Punto.

La restricción de herramientas disponibles es más robusta que cualquier instrucción en el prompt sobre qué herramientas usar. Las instrucciones en el prompt pueden ser sobrescritas por prompt injection. Las herramientas que no están disponibles no pueden ser invocadas, independientemente de lo que diga el prompt.

---

### Bloque 5: Guardrails de input y output — el diseño completo

Miremos el diagrama completo.

[Pausa — mostrar el sistema completo con todas las capas]

El flujo correcto de un sistema de agentes seguro tiene dos capas de validación explícitas: una antes del agente y una después.

El guardrail de input recibe el texto del usuario antes de que entre al sistema. Valida no solo formato — longitud, encoding, estructura — sino contenido: ¿hay patrones de inyección? ¿El input intenta modificar el comportamiento del sistema? ¿El input está dentro del dominio esperado de este agente? Un input que pasa el guardrail de input es un input que el sistema ha decidido que puede procesar.

El guardrail de output recibe el texto generado por el agente antes de que llegue al usuario. Valida que el output cumple las políticas de la empresa, que no contiene información que no debería, que responde al input original y no a instrucciones inyectadas. Un output que pasa el guardrail de output es un output que el sistema ha decidido que puede mostrar.

Estas dos capas no son redundantes. Capturan amenazas distintas. El guardrail de input trabaja sobre lo que el atacante envía. El guardrail de output trabaja sobre lo que el ataque logró producir, en caso de que pasara la primera capa.

---

### Bloque 6: La pregunta que tienes que hacerte para cada dato sensible

La seguridad en sistemas LLM no es un estado binario — es una cuestión de cuántas capas de protección tienen tus datos más sensibles.

Para cada tipo de dato en tu sistema, hazte esta pregunta: si un atacante sofisticado hace prompt injection, ¿qué información podría extraer? ¿Qué acciones podría ejecutar?

Si la respuesta te preocupa, necesitas más capas. No más instrucciones en el prompt — más capas estructurales. Acceso restringido al dato. Validación del input que lo protege. Validación del output que verifica que no salió.

---

### Decisión de diseño (cierre, ~1 min)

La regla que te llevas de esta lección: para cada tipo de dato sensible en tu sistema, cuenta cuántas capas de protección tiene.

Datos de baja sensibilidad — contenido público, configuración del sistema — pueden vivir con una capa: autenticación básica. Datos de sensibilidad media — preferencias del usuario, historial de interacciones — necesitan al menos dos capas: acceso restringido más validación de output. Datos de alta sensibilidad — información financiera, datos médicos, datos personales identificables — necesitan al menos tres capas: acceso restringido más validación de input más validación de output.

Si tienes datos de alta sensibilidad y solo una capa, ese es el riesgo más urgente de tu sistema. No el rendimiento, no la latencia, no el coste. Ese.

Antes de hacer deploy, mapea cada tipo de dato sensible de tu sistema y cuenta sus capas. Si alguno tiene menos de las que necesita, sabes dónde trabajar primero.

---

## Spec del diagrama

**Tipo:** Excalidraw

**Elementos:**

Flujo principal (izquierda a derecha):
- Nodo: "Usuario" (persona, icono a la izquierda)
- Caja: "Guardrail de input" — interior con lista: "Detección de inyección / Validación de formato / Clasificación de intención"
- Caja: "Agente" — interior con: "System prompt / Contexto del usuario / Herramientas disponibles"
- Caja: "Herramientas" — interior: "API externa / Base de datos / Búsqueda web" con etiqueta: "Permisos explícitos por herramienta"
- Caja: "Guardrail de output" — interior con lista: "Detección de datos sensibles / Validación de políticas / Coherencia con input original"
- Nodo: "Usuario" (mismo icono, a la derecha)

Vectores de ataque (flechas rojas):
- Flecha roja etiquetada "PROMPT INJECTION" entrando al guardrail de input desde arriba
- Flecha roja etiquetada "DATA EXFILTRATION" apuntando del agente al guardrail de output con una flecha de desvío intentando saltarse el guardrail
- Flecha roja etiquetada "PRIVILEGE ESCALATION" apuntando desde el agente hacia las herramientas con una flecha intentando acceder a herramienta no autorizada marcada con X

Mitigaciones (cajas verdes anotadas junto a cada vector):
- Junto a prompt injection: "Separación estructural + instruir al modelo + validar antes de actuar"
- Junto a data exfiltration: "Mínimo privilegio + output filtering"
- Junto a privilege escalation: "Solo disponibles las herramientas necesarias para este agente"

Leyenda en esquina inferior:
- Rojo: vector de ataque
- Verde: mitigación
- Azul: componente del sistema

**Flujo visual:**
- El flujo legítimo de izquierda a derecha con flechas azules gruesas
- Los vectores de ataque como flechas rojas que intentan penetrar las capas
- Las mitigaciones como cajas verdes anotadas lateralmente
- Diseño en capas horizontales que muestra visualmente la profundidad de la defensa
