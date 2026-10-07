# Sistema RAG de Producción: Más allá del Tutorial de 10 Minutos

Este repositorio contiene el código y los ejemplos discutidos en el video de YouTube: **"Cómo diseño un sistema RAG que realmente funciona en producción"**.

## 🎯 Objetivo

Mostrar un enfoque realista para construir un sistema RAG (Retrieval-Augmented Generation) que funcione en entornos de producción, cubriendo aspectos que rara vez se abordan en los tutoriales básicos:

- Estrategias avanzadas de *chunking*
- Técnicas de *reranking*
- Evaluación rigurosa del proceso de recuperación
- Análisis de fallos comunes y cómo abordarlos
- Consideraciones de monitoreo y mantenimiento en producción

## 📁 Estructura del Repositorio

```
rag-production-system/
├── data/                       # Datos de ejemplo y procesados
├── notebooks/                  # Jupyter notebooks explicativos
├── src/                        # Código fuente del sistema RAG
│   ├── chunking/               # Diferentes estrategias de chunking
│   ├── embedding/              # Modelos de embedding y gestión
│   ├── retrieval/              # Módulos de recuperación y reranking
│   ├── evaluation/             # Métricas y herramientas de evaluación
│   └── pipeline/               # Orquestación del pipeline RAG completo
├── configs/                    # Archivos de configuración
├── tests/                      # Tests unitarios e integración
├── requirements.txt            # Dependencias de Python
└── README.md                   # Este archivo
```

## 🔧 Características Principales

### 1. Estrategias de Chunking Avanzadas
- Chunking semántico basado en similitud
- Chunking por estructura de documentos (títulos, párrafos)
- Chunking adaptativo según tipo de contenido
- Overlap inteligente y preservación de contexto

### 2. Sistema de Reranking
- Implementación de Cross-Encoders para reranking
- Combinación de scores de embedding y reranker
- Estrategias de fallback cuando el reranking falla
- Optimización de latencia en producción

### 3. Evaluación de Retrieval
- Métricas clásicas: MRR, Recall@K, Precision@K
- Evaluación basada en LLMs (LLM-as-a-judge)
- Detección de problemas de cobertura y relevancia
- Visualización de resultados de recuperación

### 4. Análisis de Fallos
- Herramientas para diagnosticar fallos de recuperación
- Análisis de consultas que fallan sistemáticamente
- Identificación de brechas en la base de conocimientos
- Monitoreo de drift en datos y consultas

### 5. Consideraciones de Producción
- Logging estructurado y trazabilidad
- Métricas de rendimiento y latencia
- Estrategias de actualización incremental de índices
- Manejo de versiones de modelos y datos
- A/B testing para diferentes configuraciones

## 🚀 Cómo Empezar

### Prerrequisitos
- Python 3.8+
- Cuenta en algún proveedor de LLMs (OpenAI, Anthropic, etc.) o acceso a modelos locales
- GPU recomendada para embeddings y reranking (opcional pero recomendado)

### Instalación
```bash
git clone https://github.com/tu-usuario/rag-production-system.git
cd rag-production-system
pip install -r requirements.txt
```

### Configuración
1. Copiar `.env.example` a `.env` y completar las variables necesarias
2. Preparar los datos de entrenamiento en la carpeta `data/`
3. Ajustar las configuraciones en `configs/` según tu caso de uso

### Ejecución de Ejemplos
Los notebooks en `notebooks/` muestran paso a paso:
- `01_chunking_strategies.ipynb`: Comparación de diferentes técnicas de chunking
- `02_retrieval_and_reranking.ipynb`: Implementación de retrieval con reranking
- `03_evaluation_metrics.ipynb`: Cómo evaluar eficazmente tu sistema RAG
- `04_production_considerations.ipynb`: Aspectos clave para despliegue en producción

## 📊 Métricas de Evaluación Incluidas

El módulo `src/evaluation/` contiene implementaciones de:
- Métricas clásicas de información retrieval
- Métricas basadas en embeddings (BERTScore, etc.)
- Evaluación con LLMs para juzgar relevancia
- Métricas de diversidad y novedad
- Herramientas para análisis de errores

## 🐛 Contribuyendo

Si encuentras problemas o tienes sugerencias para mejorar este ejemplo de sistema RAG de producción, por favor:
1. Haz un fork del repositorio
2. Crea una rama para tu feature/fix
3. Envía un pull request con una descripción clara de los cambios

## ⚠️ Limitaciones y Advertencias

Este es un código de ejemplo diseñado con fines educativos. Para uso en producción real:
- Debes implementar medidas de seguridad adecuadas
- Considera aspectos de privacidad y cumplimiento (GDPR, etc.)
- Realiza pruebas de carga y estrés exhaustivas
- Implementa sistemas de monitoreo y alertas robustos
- Planifica estrategias de rollback y recuperación ante fallos

## 📚 Recursos Adicionales

Mencionados en el video:
- Guías de optimización de chunking para diferentes tipos de documentos
- Comparativa de modelos de embedding en español
- Técnicas de reranking ligeras para baja latencia
- Marcos de evaluación para sistemas RAG
- Estudios de caso de fallos en producción y cómo se resolvieron

---

**Nota**: Este repositorio acompaña al video de YouTube donde se explica cada uno de estos componentes en detalle, incluyendo los trade-offs de diseño y las lecciones aprendidas en implementaciones reales.

¡Éxitos construyendo tu sistema RAG de producción!