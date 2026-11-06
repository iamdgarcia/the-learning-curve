# The Learning Curve AI Stack

Construir una aplicación de IA es cada vez más fácil. Lo difícil es decidir qué utilizar para cada parte.

¿Dónde ejecutas el modelo? ¿Necesitas una GPU? ¿Te conviene consumir un modelo mediante API o desplegarlo tú mismo? ¿Dónde alojas el backend? ¿Y la interfaz?

El problema ya no es que falten herramientas. Es justo lo contrario: hay demasiadas.

Esta es una selección de las herramientas que recomiendo para construir aplicaciones y sistemas de IA, **organizada por el problema que resuelven**.

No es un ranking de popularidad ni una lista exhaustiva. Es el stack que elegiría hoy para empezar a construir.

> **Transparencia:** algunos enlaces son de afiliado. Si los usas, The Learning Curve puede recibir una comisión sin coste adicional para ti. La afiliación no determina qué herramientas aparecen: primero tienen que tener sentido técnicamente.

---

## Una aplicación de IA no es solamente un modelo

Normalmente tiene varias piezas:

```
┌─────────────────────────────────────────────────────┐
│                  Tu aplicación de IA                │
├──────────────┬──────────────┬────────────┬──────────┤
│  AI Inference│  GPU Compute │  Backend   │ Frontend │
│  (el modelo) │  (si lo      │  (API,     │ (lo que  │
│              │  necesitas)  │  workers,  │ ve el    │
│              │              │  BBDD)     │ usuario) │
└──────────────┴──────────────┴────────────┴──────────┘
```

No necesitas todas. Un prototipo puede ser una web conectada a una API de modelos. En otros casos necesitarás GPUs propias, workers y una infraestructura más completa.

---

## 1. AI Inference — Novita AI

<table>
<tr>
<td width="72" align="center" valign="top"><br>
  <img src="https://www.google.com/s2/favicons?domain=novita.ai&sz=64" width="40" height="40" alt="Novita AI"/>
</td>
<td valign="top">

### [Novita AI ↗](https://novita.ai/?ref=mzblm2z&utm_source=affiliate)
**Quiero utilizar un modelo sin gestionar toda la infraestructura.**

Novita ofrece APIs para modelos open source (DeepSeek, Llama, Qwen y otros) además de GPUs serverless e instancias bajo demanda. Compatible con el SDK de OpenAI — funciona como drop-in replacement.

| ✅ Usaría Novita cuando… | ❌ Buscaría otra opción cuando… |
|--------------------------|-------------------------------|
| Prototipo de aplicación de IA | Necesito controlar completamente el entorno |
| Pruebas rápidas de modelos open source | Quiero instalar mi propio stack de serving |
| Consumir un modelo vía API | Necesito modificar el runtime |
| No quiero gestionar el serving | Quiero gestionar directamente la GPU |

**Key:** `NOVITA_API_KEY` + `NOVITA_BASE_URL`
</td>
</tr>
</table>

---

## 2. GPU & Compute — RunPod

<table>
<tr>
<td width="72" align="center" valign="top"><br>
  <img src="https://www.google.com/s2/favicons?domain=runpod.io&sz=64" width="40" height="40" alt="RunPod"/>
</td>
<td valign="top">

### [RunPod ↗](https://runpod.io)
**Quiero controlar dónde y cómo se ejecuta mi modelo.**

Hay situaciones en las que una API no es suficiente: quizás necesitas desplegar tu propio modelo, una GPU concreta, o controlar el container y el runtime. RunPod ofrece GPUs bajo demanda y una plataforma serverless que puede escalar a cero.

| ✅ Usaría RunPod cuando… | ❌ Buscaría otra opción cuando… |
|--------------------------|-------------------------------|
| Ejecuto modelos propios | Solo necesito consumir un modelo vía API |
| Fine-tuning | Quiero llegar rápido sin gestionar infraestructura |
| Inference self-hosted | El modelo ya existe como API pública |
| Containers o runtimes personalizados | — |

**Novita vs RunPod en una línea:**
- *"Dame acceso a este modelo y quiero empezar"* → **Novita**
- *"Quiero decidir exactamente qué se ejecuta y dónde"* → **RunPod**
</td>
</tr>
</table>

---

## 3. Backend & Infrastructure — Railway

<table>
<tr>
<td width="72" align="center" valign="top"><br>
  <img src="https://cdn.simpleicons.org/railway" width="40" height="40" alt="Railway"/>
</td>
<td valign="top">

### [Railway ↗](https://railway.com?referralCode=6Lguh2)
**El modelo no es la aplicación.**

Puedes tener un modelo funcionando perfectamente y todavía no tener una aplicación. Una aplicación real necesita APIs, autenticación, bases de datos, workers, webhooks o tareas programadas. Railway permite desplegar todos estos servicios dentro de un mismo proyecto.

| ✅ Usaría Railway para… |
|-------------------------|
| Backend de una AI application |
| APIs y workers |
| Bases de datos (Postgres, Redis) |
| Jobs programados y webhooks |
| Pasar rápidamente de local a producción |

**Free tier:** $5 de crédito/mes
</td>
</tr>
</table>

---

## 4. Frontend & Deployment — Netlify

<table>
<tr>
<td width="72" align="center" valign="top"><br>
  <img src="https://cdn.simpleicons.org/netlify/00C7B7" width="40" height="40" alt="Netlify"/>
</td>
<td valign="top">

### [Netlify ↗](https://join.netlify.com/uk2itht31g7b)
**El usuario no ve tu modelo. Ve tu aplicación.**

Podemos tener el mejor modelo del mundo y una infraestructura fantástica. Pero el usuario interactúa con una interfaz. Netlify resuelve esa parte del stack: llevar la aplicación web hasta el usuario.

| ✅ Usaría Netlify para… |
|-------------------------|
| Frontends e interfaces de IA |
| Landing pages y demos |
| Prototipos que necesitan estar online rápido |
| Funciones serverless ligeras |

**Railway + Netlify juntos:** Railway para el backend, Netlify para el frontend. Dos herramientas, dos problemas distintos — más fácil de razonar que meter todo en una única plataforma.

**Free tier:** 100GB de ancho de banda, 300 minutos de build/mes
</td>
</tr>
</table>

---

## 5. AI Voice — ElevenLabs

<table>
<tr>
<td width="72" align="center" valign="top"><br>
  <img src="https://cdn.simpleicons.org/elevenlabs" width="40" height="40" alt="ElevenLabs"/>
</td>
<td valign="top">

### [ElevenLabs ↗](https://try.elevenlabs.io/5rwirobe89kq)
**Necesito una voz o transcripción de calidad.**

La TTS más natural para español e inglés. Word-level timestamps para sincronización de subtítulos. También ofrece Scribe — el transcriptor con mejor alineación palabra a palabra para aplicaciones de voz y video.

| ✅ Usaría ElevenLabs para… |
|---------------------------|
| TTS en Shorts y video content |
| Voz en agentes conversacionales |
| Transcripción con timestamps precisos |
| Clonación de voz |

**Free tier:** 10K caracteres/mes · **Key:** `ELEVENLABS_API_KEY`
</td>
</tr>
</table>

---

## ¿Qué stack elegir?

### Quiero construir un MVP rápidamente
```
Novita AI (modelo vía API)
    +
Railway (backend)
    +
Netlify (frontend)
```
Punto de partida para la mayoría de aplicaciones. Sin GPUs que gestionar, foco en el producto.

### Quiero ejecutar mi propio modelo
```
RunPod (GPU + serving)
    +
Railway (backend)
    +
Netlify (frontend)
```
La infraestructura de inference pasa a estar bajo tu control.

### Quiero experimentar con modelos open source
```
Novita AI  →  prototipo rápido
RunPod     →  cuando necesito control del entorno
```

---

## Referencia rápida

| | Tool | Para qué | Free tier | Link |
|-|------|----------|-----------|------|
| <img src="https://www.google.com/s2/favicons?domain=novita.ai&sz=32" width="20"> | Novita AI | LLM inference barato | Pay-per-use | [↗](https://novita.ai/?ref=mzblm2z&utm_source=affiliate) |
| <img src="https://www.google.com/s2/favicons?domain=runpod.io&sz=32" width="20"> | RunPod | GPU & compute propio | — | [↗](https://runpod.io) |
| <img src="https://cdn.simpleicons.org/railway" width="20"> | Railway | Backend, BBDD, workers | $5 crédito/mes | [↗](https://railway.com?referralCode=6Lguh2) |
| <img src="https://cdn.simpleicons.org/netlify/00C7B7" width="20"> | Netlify | Frontend & deploy | 100GB bw/mes | [↗](https://join.netlify.com/uk2itht31g7b) |
| <img src="https://cdn.simpleicons.org/elevenlabs" width="20"> | ElevenLabs | TTS & transcripción | 10K chars/mes | [↗](https://try.elevenlabs.io/5rwirobe89kq) |
| <img src="https://www.google.com/s2/favicons?domain=groq.com&sz=32" width="20"> | Groq | Transcripción rápida | Generoso | [groq.com](https://console.groq.com) |
| <img src="https://cdn.simpleicons.org/pexels/05A081" width="20"> | Pexels | Stock footage | 200 req/hr | [pexels.com](https://www.pexels.com/api/) |

---

## Próximas incorporaciones

El stack irá creciendo a medida que se prueben nuevas herramientas. La regla seguirá siendo la misma: una herramienta entra porque la recomendaría técnicamente, no por su programa de afiliados.

Áreas pendientes: observabilidad · bases de datos vectoriales · model gateways · evaluación de modelos · AI coding tools · MLOps · seguridad
