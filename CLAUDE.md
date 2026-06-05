# bible-study-agents

## Contexto del proyecto

Sistema de agentes Python para estudio bíblico automatizado. Analiza textos de la Biblia (Reina Valera, 66 libros protestantes) usando Llama 3.1 local via Ollama, guarda el progreso en Supabase y envía el estudio diario por Slack.

Construido con la misma arquitectura de **Café con Historia** — pipeline de agentes numerados, migraciones SQL secuenciales y manejo de errores diferenciado.

---

## Stack

| Componente       | Tecnología                        |
|------------------|-----------------------------------|
| Lenguaje         | Python 3.11                       |
| Modelo IA        | Llama 3.1 local via Ollama        |
| Base de datos    | Supabase (compartida con el web)  |
| Notificaciones   | Slack API                         |
| Orquestación     | Windows Task Scheduler            |

---

## Estructura de carpetas

```
bible-study-agents/
├── agents/          # Agentes Python numerados (agente_0_, agente_1_...)
├── database/        # Migraciones SQL numeradas (001_, 002_...)
├── scripts/         # Utilidades y scripts de carga
├── utils/           # Manejo de errores y helpers
├── CLAUDE.md
├── main.py
├── requirements.txt
└── .gitignore
```

---

## Base de datos — Supabase

Todas las tablas usan el prefijo `bible_`.

### Tablas base (texto bíblico — inmutable)

```sql
bible_libros      → id, orden (1-66), nombre, abreviatura, testamento
bible_capitulos   → id, id_libro, numero
bible_versiculos  → id, id_capitulo, numero, texto
```

### Tablas de usuarios y plan

```sql
bible_usuarios    → id (UUID), email, nombre
bible_planes      → id, id_usuario, nombre, descripcion, activo
bible_sesiones    → id, id_plan, orden, versiculo_inicio_id, versiculo_fin_id,
                    fecha_programada, completada
```

### Tablas de estudio

```sql
bible_analisis    → id, id_sesion, contexto_historico, resumen, temas_principales,
                    conexiones, preguntas_reflexion, modelo_usado,
                    tokens_usados, duracion_segundos
bible_tareas      → id, id_sesion, id_analisis (opcional), id_usuario,
                    descripcion, origen (llama/usuario), completada, notas
```

### Archivos de migración

```
database/
├── 001_crear_tablas_base.sql     # bible_libros, bible_capitulos, bible_versiculos
├── 002_crear_tablas_plan.sql     # bible_usuarios, bible_planes, bible_sesiones
└── 003_crear_tablas_estudio.sql  # bible_analisis, bible_tareas
```

---

## Reglas del proyecto

1. **Llama es el analista — nunca la fuente.** El texto bíblico viene siempre de Supabase, nunca de Llama.
2. **El JSON fuente** es `thiagobodruk/bible` en GitHub — Reina Valera. Los índices del JSON empiezan en 0, los números reales en 1.
3. **Convenciones** iguales a Café con Historia: snake_case, archivos numerados, manejo de errores diferenciado.
4. **Dos repositorios separados** — este repo es local y privado. El frontend Next.js vive en `bible-study-web`.

---

## Estado actual del código

| Componente | Archivo | Estado |
|---|---|---|
| Agente de análisis | `agents/agente_0_analisis.py` | ✅ Implementado |
| Carga de Biblia | `scripts/cargar_biblia.py` | ✅ Listo para ejecutar |
| Carga del plan | `scripts/cargar_plan.py` | ✅ Listo para ejecutar |
| Scheduler Windows | `scripts/setup_scheduler.ps1` | ✅ Listo para desplegar |
| Migraciones SQL | `database/001-003_*.sql` | ✅ Definidas |
| Manejo de errores | `utils/errores.py` | ⚠️ Adaptado de otro proyecto — revisar |
| `main.py` | — | ❌ No existe (mencionado en estructura) |
| `requirements.txt` | — | ❌ No existe |

---

## Próximos pasos

### Despliegue (orden obligatorio)

- [ ] Crear repositorio `bible-study-agents` en GitHub (privado)
- [ ] Ejecutar las 3 migraciones SQL en Supabase (`001`, `002`, `003`)
- [ ] Ejecutar `python scripts/cargar_biblia.py` — carga 66 libros, ~31.000 versículos
- [ ] Ejecutar `python scripts/cargar_plan.py` — carga 338 sesiones desde `2026-06-03`
- [ ] Probar el agente manualmente: `python agents/agente_0_analisis.py`
- [ ] Desplegar `scripts/setup_scheduler.ps1` como administrador en Windows

### Deuda técnica

- [ ] Crear `requirements.txt` con dependencias reales (`python-dotenv`, `supabase`, `requests`, `slack-sdk`)
- [ ] Crear `main.py` como punto de entrada central o eliminarlo de la estructura documentada
- [ ] Revisar y adaptar `utils/errores.py` — actualmente es de "Café con Historia", no del proyecto actual
- [ ] Hacer configurable el modelo Llama (actualmente hardcodeado como `"llama3.1"`)

### Agentes futuros

- [ ] `agente_1_tareas.py` — extraer tareas de reflexión del análisis y guardarlas en `bible_tareas`
- [ ] `agente_2_slack.py` — responder preguntas o feedback desde Slack

---

## Repositorios relacionados

| Repo                | Descripción                        | Visibilidad |
|---------------------|------------------------------------|-------------|
| `bible-study-agents`| Este repo — agentes Python         | Privado     |
| `bible-study-web`   | Frontend Next.js — dashboard web   | Público     |