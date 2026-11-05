# AI Architect Academy — Guía de Producción

Esta guía define el proceso completo de grabación y publicación del curso. Quien la lea puede empezar a grabar sin preguntas adicionales.

---

## Formato estándar de cada lección

### Estructura del guión

Cada lección sigue esta estructura sin excepción:

**1. Intro (20-30 segundos)**
Contextualiza dónde estamos en el semestre. No es presentación personal — el alumno ya sabe quién eres. Es orientación: "Llevamos tres lecciones hablando de contexto. Hoy vemos qué pasa cuando ese contexto no es suficiente."

**2. Núcleo conceptual**
El contenido principal de la lección. Siempre acompañado de un diagrama en pantalla (ver sección de diagramas). Explicar el concepto, luego mostrar el diagrama, luego reforzar con el diagrama visible.

**3. Decisión de diseño (1 minuto)**
El cierre de cada lección. Siempre responde la misma pregunta: "¿Cuándo usas esto y cuándo no?". Sin esta sección, la lección no está terminada. Es el diferenciador del curso frente a documentación técnica.

### Duración objetivo

- Mínimo: 6 minutos
- Máximo: 10 minutos
- Si el guión supera los 10 minutos, divide en dos lecciones o elimina contenido secundario

### Formato de grabación

- Cámara principal con el presentador en pantalla
- Diagrama visible simultáneamente (picture-in-picture o pantalla dividida)
- Herramientas de diagrama: Excalidraw (preferido) o Google Slides exportado a PDF
- Resolución mínima: 1080p

---

## Checklist de grabación

Completar antes de presionar REC:

- [ ] Cámara encuadrada correctamente (cara en el tercio superior)
- [ ] Iluminación sin sombras duras en la cara
- [ ] Diagrama preparado y visible en pantalla (no en pestaña oculta)
- [ ] Guión leído en voz alta al menos una vez antes de grabar
- [ ] CTA al final preparado — texto exacto copiado del guión (ver plantillas de CTA más abajo)
- [ ] Micrófono probado — sin eco, sin ruido de fondo
- [ ] Notificaciones del sistema desactivadas

---

## Plantillas de CTA

Copiar el texto exacto al final del guión según corresponda:

**Udemy (cierre de lección estándar):**
> "Si quieres el curso completo con todos los semestres estructurados, lo tienes en Udemy — link en la descripción."

**DigitalOcean (diagramas de cierre de semestre con despliegue):**
> "Despliega este sistema en DigitalOcean por menos de 20 dólares al mes — link en la descripción."

**Anthropic API (lecciones de coste y evaluación):**
> "Empieza con 5 dólares de crédito en la API de Anthropic — link en la descripción."

---

## Plantilla de descripción YouTube

Usar esta plantilla para cada video publicado en YouTube. Sustituir los corchetes por el contenido real.

```
[Título de la lección] | AI Architect Academy

En este video aprenderás [objetivo de la lección en una frase].

🎓 Curso completo y estructurado en Udemy → [LINK UDEMY]

🔧 Despliega este tipo de sistemas en DigitalOcean → [LINK DIGITALOCEAN AFILIADO]

📧 Newsletter The Learning Curve → https://iamdgarcia.substack.com

⏱️ Timestamps:
0:00 - Intro
[timestamps del video]

#AIArchitect #InteligenciaArtificial #ArquitecturaIA #LLM
```

Notas sobre la descripción YouTube:
- El link de Udemy va siempre primero
- El link de DigitalOcean solo se incluye en lecciones donde tiene sentido contextual (ver tabla de afiliaciones)
- Los timestamps son obligatorios en videos de más de 5 minutos

---

## Plantilla de descripción Udemy

Usar esta plantilla para la descripción de cada lección dentro de la plataforma Udemy:

```
Esta lección forma parte del Semester [N] — [Nombre del semestre] del curso AI Architect — Diseña sistemas de IA que duran.

Aprenderás: [objetivo de la lección en una frase]

Al finalizar este semestre sabrás: [objetivo del semestre en dos o tres frases]
```

Notas sobre la descripción Udemy:
- Sin links de afiliación dentro de Udemy (va contra los términos de servicio)
- Mantener el texto corto — el alumno ya pagó el curso, no necesita ser convencido

---

## Protocolo de publicación

### Orden de publicación

1. Grabar todo el semestre antes de publicar nada
2. Subir el semestre completo a Udemy (acceso inmediato para alumnos de pago)
3. Publicar en YouTube lección a lección, una por semana
4. Cada video de YouTube incluye CTA al curso completo en Udemy

### Cadencia de publicación en YouTube

- Una lección por semana
- Publicar el mismo día de la semana (consistencia para el algoritmo)
- No publicar más de una lección por semana aunque haya presión — el objetivo es retención, no volumen

### Checklist pre-publicación YouTube

- [ ] Thumbnail con el nombre de la lección legible en miniatura
- [ ] Descripción completa con todos los links activos
- [ ] Timestamps añadidos
- [ ] Capítulos habilitados en YouTube (requiere timestamps)
- [ ] Tarjetas al final apuntando al curso en Udemy

---

## Tabla de afiliaciones

| Afiliación | Cuándo mencionarlo | Texto de CTA |
|---|---|---|
| DigitalOcean | Diagramas de cierre de semestre con despliegue del sistema | "Despliega este sistema en DigitalOcean por menos de 20 dólares al mes — link en la descripción" |
| Anthropic API | Lecciones de coste y evaluación | "Empieza con 5 dólares de crédito en la API de Anthropic — link en la descripción" |

Regla general: no forzar afiliaciones. Si el contenido no menciona despliegue o costes de API, no incluir el CTA de afiliado. La credibilidad del curso depende de no parecer un canal de marketing.

---

## Instrucciones para crear diagramas Excalidraw

Cada lección tiene en su carpeta un archivo `DIAGRAM_SPEC.md` con los elementos exactos del diagrama.

### Proceso para crear un diagrama

1. Abrir excalidraw.com o la app de escritorio
2. Leer el `DIAGRAM_SPEC.md` de la lección antes de empezar
3. Crear los elementos siguiendo la lista del spec — en el orden indicado
4. Revisar que todos los elementos del spec están presentes antes de exportar
5. Exportar como PNG para incrustar en el video (fondo transparente o blanco)
6. Guardar el archivo `.excalidraw` en la carpeta de la lección

### Para diagramas en slides/PDF

- Herramienta: Google Slides o PowerPoint
- Exportar a PDF antes de usar en el video
- Guardar el archivo fuente (.pptx o el link de Google Slides) en la carpeta de la lección

### Convenciones de estilo

- Usar colores con significado consistente en todo el curso (definir paleta en la primera lección y no cambiarla)
- Flechas con dirección clara
- Texto en los nodos: corto (máximo 4 palabras por caja)
- No usar colores de fondo que dificulten la lectura en video comprimido

---

## Estructura de carpetas por lección

Cada lección tiene su propia carpeta con:

```
lección_X.Y/
├── SCRIPT.md          # Guión completo
├── DIAGRAM_SPEC.md    # Especificación del diagrama
├── diagrama.excalidraw # Archivo fuente del diagrama
├── diagrama.png       # Exportación para video
└── NOTES.md           # Notas de producción (opcional)
```

---

## Notas generales

- El tono del curso es de profesional a profesional. No explicar lo que el alumno ya sabe. No condescender.
- Las lecciones de YouTube son independientes — un alumno puede llegar a cualquiera sin haber visto las anteriores. La intro debe funcionar también para nuevos espectadores.
- Las lecciones de Udemy asumen que el alumno ha visto las anteriores del semestre.
