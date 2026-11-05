# Arquitectura de un VAD Semántico para Agentes de Voz en Español

*The Learning Curve · Daniel García Peña*

---

Llevaba semanas queriendo escribir sobre esto. Al final me salió largo, así que lo organicé en dos partes: este post con la arquitectura y los diagramas, y un webinar donde lo construyo en vivo con código. Empezamos por lo escrito.

---

## Antes de empezar: qué es un agente de voz y por qué es diferente

Un agente de voz no es un chatbot de texto con micrófono. La diferencia parece trivial pero no lo es.

Cuando hablas con un chatbot de texto, tú decides cuándo has terminado — pulsas Enter. El sistema nunca tiene que adivinar si has acabado la frase. En voz, esa señal no existe. El agente tiene que escucharte, decidir en tiempo real cuándo has terminado de hablar, y responder sin hacerte esperar dos segundos incómodos ni interrumpirte a mitad de frase.

Esa decisión — *¿ha terminado el usuario?* — se llama **detección de actividad de voz** o VAD (Voice Activity Detection). Es la primera pieza de cualquier sistema de voz y, en mi experiencia, la que más problemas da en español.

El resto del sistema es más familiar: hay un modelo que convierte tu voz en texto (STT), un LLM que genera la respuesta, y otro modelo que convierte esa respuesta en audio (TTS). Pero todo depende de que el VAD haga bien su trabajo. Si se equivoca, el agente interrumpe, o se queda callado cuando debería responder, o las dos cosas en la misma conversación.

---

## El problema concreto con el español

Llevo meses trabajando en esto. El síntoma más frecuente es el siguiente: el agente interrumpe cuando el usuario está pensando.

El usuario dice "necesito que me ayudes con el... eh..." y el agente salta. Técnicamente, el VAD ha hecho lo que se le pide: ha detectado un silencio de energía después de un pico de voz y ha concluido que el turno ha terminado. El problema es que el usuario solo estaba eligiendo palabras.

Esto pasa mucho en español porque tenemos muchas más muletillas de pausas que en inglés. "Eh", "ajá", "mmm", "este", "o sea", "pues", "bueno" — todas suenan, todas tienen energía de voz, y todas van seguidas de silencios breves mientras el hablante organiza el siguiente pensamiento. Para un VAD acústico, son indistinguibles de un fin de turno.

---

## 👇 Una pregunta antes de seguir

Estoy preparando un **webinar sobre agentes de voz en producción**: arquitectura completa, código en vivo, casos reales de interrupción y cómo depurarlos. Antes de cerrar fechas quiero saber si tiene sentido organizarlo.

*¿Te interesaría un webinar dedicado a construir un agente de voz de producción desde cero?*

<!-- ENCUESTA SUBSTACK — insertar poll nativo con las opciones:
  ✅ Sí, me interesa mucho
  🤔 Depende del contenido, cuéntame más
  📅 Me interesa pero necesito verlo grabado
  ❌ No es mi área ahora mismo
-->

*(Si estás leyendo esto en el email, la encuesta aparece arriba. Tarda 3 segundos.)*

---

## Cómo funciona realmente el VAD acústico

Volviendo al problema técnico.

Los dos VADs más usados en producción son **Silero VAD** y **WebRTC VAD**. Silero es un modelo neuronal pequeño entrenado para distinguir voz de ruido de fondo. WebRTC es un clasificador GMM escrito en C que lleva en el ecosistema de videoconferencias desde hace diez años. Los dos funcionan midiendo energía de la señal de audio: si el frame supera un umbral → voz activa, si cae por debajo → silencio.

Son muy buenos en lo que hacen. El problema es que lo que hacen no es suficiente.

**[📷 Diagrama 1: Cascada Tradicional vs End-to-End]**
*El pipeline de tres etapas y cómo se acumula la latencia*

Hay una alternativa al pipeline de cascada: los modelos end-to-end como GPT-4o Audio o Gemini Live, que van de audio a audio en un solo modelo. Latencia mucho menor, sin problemas de coordinación entre etapas. Pero en entornos regulados — banca, salud, atención al cliente con compliance — la cascada no va a desaparecer pronto. La razón es simple: cuando el regulador te pide el log de una conversación, un modelo end-to-end es una caja negra. Con STT+LLM+TTS tienes texto en cada paso.

Así que el problema de las interrupciones hay que resolverlo dentro de la cascada, no abandonándola.

**[📷 Diagrama 2: VAD Acústico vs VAD Semántico]**
*El mismo "eh..." visto por los dos sistemas*

La diferencia entre los dos enfoques es la pregunta que responden. El VAD acústico responde "¿hay sonido?". Lo que necesitas saber es "¿el usuario ha terminado su turno?". No es la misma pregunta.

---

## La capa semántica: jev-vad

La idea es añadir un segundo VAD que corra después del acústico — no en lugar de él. El VAD acústico sigue siendo la primera criba, porque es instantáneo. Pero antes de disparar el STT, un modelo pequeño confirma que el turno realmente ha terminado.

A esto lo llamamos **jev-vad**: un LLM de 0.5B–3B parámetros cuantizado a int4 y exportado a ONNX para correr en CPU. Sin GPU. Sin infraestructura especial.

**[📷 Diagrama 3: Motor jev-vad — System-1 en CPU]**
*El flujo de entrada, modelo y salida*

El modelo recibe la transcripción parcial del STT (lo que el usuario ha dicho hasta ahora) y el tiempo de silencio detectado por el VAD acústico. Con eso, decide si el turno ha terminado o no.

La parte contraintuitiva es cómo se le pregunta.

### Por qué las preguntas van en inglés

Los modelos pequeños no distribuyen su capacidad de razonamiento igual en todos los idiomas. En inglés tienen más datos de entrenamiento, más diversidad de tareas, y un razonamiento más fino. Si le preguntas en español a un modelo de 0.5B parámetros, una parte de su capacidad se va en la traducción implícita.

La solución que encontré: pasarle el estado en español como dato, y hacerle las preguntas en inglés.

```
# Contexto (en español)
Transcripción: "Necesito que me ayudes con el eh..."
Silencio acústico: 220ms

# Preguntas (en inglés)
"Is the sentence grammatically complete?"  → no
"Is the last word a filler or hesitation?" → yes
"Has the main intent been stated?"         → partial
```

El modelo no razona en español. Solo hace clasificación binaria en el idioma donde es más preciso, sobre información que llega como contexto. El resultado: **+3.3 puntos de precisión sin cambiar el modelo ni el hardware**. Que en 100 frases de evaluación son cuatro frases que antes fallaba y ahora no.

---

## Los números reales

Benchmark sobre un VPS estándar de 4 vCPU, sin GPU, con onnxruntime 1.18:

| Modelo | Tamaño int4 | Latencia p50 | Latencia p95 | Precisión |
|---|---|---|---|---|
| SmolLM-135M | 80 MB | 38 ms | 67 ms | 81.0% |
| Qwen2.5-0.5B | 206 MB | 101 ms | 143 ms | 91.0% |
| Qwen2.5-0.5B + preguntas EN | 206 MB | 104 ms | 151 ms | **94.3%** |
| Phi-3.5-mini | 2.2 GB | 162 ms | 187 ms | 96.1% |

El p95 de 151ms en el modelo recomendado significa que en el 95% de las frases la decisión llega en menos de 151ms. Sumado a los ~180ms del STT parcial, el sistema responde en menos de 350ms desde que el usuario termina de hablar. Por encima de 300ms la conversación empieza a sentirse torpe; por encima de 500ms el usuario asume que el agente no ha entendido.

Phi-3.5-mini llega al 96.1% pero pesa 2.2GB y tarda hasta 187ms. Para la mayoría de casos, Qwen2.5-0.5B es el punto de equilibrio.

---

## El Filler Guard: la capa barata que nadie añade

Hay un problema con el jev-vad: cuesta ~100ms por decisión. Eso es razonable, pero hay una clase de casos donde es excesivo — cuando el último token de la transcripción es directamente una muletilla conocida. "Eh", "mmm", "este"... no hace falta un modelo para saber que el turno no ha terminado.

Lo que hago es añadir una comprobación de regex antes de llamar al modelo. Si los últimos tokens están en la lista de muletillas, la respuesta es directamente "esperar", sin invocar nada más. Eso filtra alrededor del 40% de los falsos positivos en microsegundos.

**[📷 Diagrama 4: Reglas de decisión y Filler Guard]**
*El flowchart de las 4 capas*

El pipeline completo de decisión antes de disparar el STT:

1. ¿Hay silencio acústico de al menos 300ms? Si no → esperar
2. ¿El último token es una muletilla conocida? Si sí → esperar
3. ¿La transcripción tiene al menos 4 tokens? Si no → esperar
4. ¿El score de jev-vad supera 0.6? Si no → esperar

Solo si pasa las cuatro capas el sistema dispara el STT. Cada capa filtra lo que la anterior no puede.

**[📷 Diagrama 5: Arquitectura completa de producción]**
*El pipeline completo de audio a respuesta*

El overhead total de este pipeline: 50–100ms en un servidor sin GPU. Eso es lo que cuesta no interrumpir a alguien que está pensando.

---

## Lo que está en abierto

Todo lo que he descrito aquí está documentado y disponible en el repositorio público:

**[github.com/iamdgarcia/jev-vad-poc](https://github.com/iamdgarcia/jev-vad-poc)**

Ahí está el paper completo con la metodología, el script que reproduce la tabla de latencias corriendo los cuatro modelos sobre el mismo dataset, las 100 frases etiquetadas en español con sus ground truths, y el modelo Qwen2.5-0.5B cuantizado a int4 listo para descargar. Todo público, todo reproducible.

---

*A partir de aquí es contenido para mecenas.*

---

## 🔒 Para mecenas: del poc al servicio

Entender cómo funciona es gratis. Tener algo que desplegar esta tarde es lo que incluye el acceso de mecenas.

Hay tres cosas que no están en el repositorio público porque no son investigación — son fontanería de producción:

**El servidor.** Un wrapper FastAPI con WebSockets que expone el VAD semántico como microservicio. El cliente manda frames de audio PCM en streaming, el servidor devuelve el score en cada chunk, y cuando supera el umbral emite `turn_complete`. Compatible con LiveKit y Twilio Media Streams. El modelo carga una vez en memoria y sirve peticiones concurrentes sin bloqueo.

**El Dockerfile.** Pelear con ONNX Runtime en Docker es la parte que más tiempo me lleva cada vez que empiezo un proyecto nuevo — versiones de `libgomp`, `OMP_NUM_THREADS`, `ONNXRUNTIME_INTRA_OP_NUM_THREADS`, imágenes base que rompen con ciertas versiones de Python. La plantilla tiene todo eso resuelto, con `docker-compose.yml` para local y `cloudbuild.yaml` para Google Cloud Run. El contenedor arranca en menos de 5 segundos y escala a cero cuando no hay tráfico.

**El dashboard Gradio.** Un frontal para probar el VAD con micrófono en directo sin tocar la terminal. Muestra la transcripción parcial con las muletillas resaltadas, y el score del modelo en tiempo real. Útil para demostrar el sistema a alguien que no es técnico, y para depurar frases específicas que han dado problemas en producción sin tener que montar un script de prueba cada vez.

---

Si ya eres mecenas, el enlace al repositorio privado está en el email de este post.

Si todavía no lo eres: **[iamdgarcia.substack.com](https://iamdgarcia.substack.com)**

---

*Los diagramas de este post están disponibles como diapositivas interactivas en el [repositorio público de The Learning Curve](https://github.com/iamdgarcia/the-learning-curve/tree/main/voice-agents/slides). Se abren en el navegador, sin instalación.*
