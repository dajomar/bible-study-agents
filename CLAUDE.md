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
├── requirements.txt
└── .gitignore
```

---

## Base de datos — Supabase

Todas las tablas usan el prefijo `bible_`.

### Tablas base (texto bíblico — inmutable)

```sql
bible_libros      → id, orden (1-66), nombre, abreviatura, testamento, version
bible_capitulos   → id, id_libro, numero
bible_versiculos  → id, id_capitulo, numero, texto
bible_configuracion → id, clave, valor, descripcion
```

> `bible_libros.version` identifica la versión bíblica de cada registro (ej. `RV1909`, `RVR1960`).
> Los constraints UNIQUE son compuestos: `(orden, version)` y `(abreviatura, version)` para soportar múltiples versiones simultáneas.

### Tablas de usuarios y plan

```sql
bible_usuarios    → id (UUID), email, nombre, version_biblica (default 'RVR1960')
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
├── 001_crear_tablas_base.sql             # bible_libros, bible_capitulos, bible_versiculos
├── 002_crear_tablas_plan.sql             # bible_usuarios, bible_planes, bible_sesiones
├── 003_crear_tablas_estudio.sql          # bible_analisis, bible_tareas
├── 004_crear_tabla_configuracion.sql     # bible_configuracion + columna version en bible_libros
                                          # + columna version_biblica en bible_usuarios
└── 005_corregir_constraint_bible_libros.sql  # Constraints compuestos (orden, version)
                                              # y (abreviatura, version)
```

### Estado actual de la base de datos (2026-06-05)

| Tabla | Registros | Estado |
|---|---|---|
| `bible_libros` | 132 (66 × 2 versiones) | ✅ Poblada |
| `bible_capitulos` | 2.378 | ✅ Poblada |
| `bible_versiculos` | ~62.000 | ✅ Poblada |
| `bible_configuracion` | 4 | ✅ Poblada |
| `bible_usuarios` | 0 | ⏳ Pendiente |
| `bible_planes` | 0 | ⏳ Pendiente |
| `bible_sesiones` | 0 | ⏳ Pendiente |
| `bible_analisis` | 0 | ⏳ Pendiente |
| `bible_tareas` | 0 | ⏳ Pendiente |

### Versiones bíblicas activas

| Clave | Valor | Notas |
|---|---|---|
| `version_disponible_1` | `RV1909` | Reina Valera 1909 |
| `version_disponible_2` | `RVR1960` | Reina Valera Revisada 1960 — **versión principal** |
| `idioma` | `es` | |
| `modelo_llama` | `llama3.1` | |

---

## Formato estándar de JSON bíblico

Cualquier versión futura debe convertirse a este formato antes de cargarse con `cargar_biblia.py`:

```json
[{
  "orden": 1,
  "nombre": "Génesis",
  "abreviatura": "gn",
  "testamento": "Antiguo",
  "capitulos": [{
    "numero": 1,
    "versiculos": [
      { "numero": 1, "texto": "En el principio creó Dios..." }
    ]
  }]
}]
```

---

## Reglas del proyecto

1. **Llama es el analista — nunca la fuente.** El texto bíblico viene siempre de Supabase, nunca de Llama.
2. **Formato estándar obligatorio** — cualquier JSON bíblico nuevo debe convertirse con `scripts/convertir_rvr1960.py` o equivalente antes de cargarse.
3. **Script de carga unificado** — usar siempre `scripts/cargar_biblia.py <VERSION> <ARCHIVO_JSON>`. Los scripts específicos por versión están deprecados.
4. **Convenciones** iguales a Café con Historia: snake_case, archivos numerados, manejo de errores diferenciado.
5. **Dos repositorios separados** — este repo es local y privado. El frontend Next.js vive en `bible-study-web`.

---

## Estado actual del código

| Componente | Archivo | Estado |
|---|---|---|
| Agente de análisis | `agents/agente_0_analisis.py` | ✅ Implementado |
| Carga unificada | `scripts/cargar_biblia.py` | ✅ Definitivo — usar este |
| Conversor JSON | `scripts/convertir_rvr1960.py` | ✅ Disponible |
| Carga del plan | `scripts/cargar_plan.py` | ✅ Listo para ejecutar |
| Scheduler Windows | `scripts/setup_scheduler.ps1` | ✅ Listo para desplegar |
| Migraciones SQL | `database/001-005_*.sql` | ✅ Definidas (005 ejecutadas) |
| Manejo de errores | `utils/errores.py` | ⚠️ Adaptado de otro proyecto — revisar |
| `requirements.txt` | — | ✅ Creado |
| `main.py` | — | ❌ No existe — eliminar de la estructura documentada |

### Scripts deprecados (no usar)

| Archivo | Reemplazado por |
|---|---|
| `scripts/cargar_biblia_rvr09.py` | `scripts/cargar_biblia.py RV1909 <archivo>` |
| `scripts/cargar_biblia_rvr1960.py` | `scripts/cargar_biblia.py RVR1960 <archivo>` |

---

## Próximos pasos

### Despliegue inmediato

- [ ] Crear usuario en `bible_usuarios` con `version_biblica = 'RVR1960'`
- [ ] Ejecutar `python scripts/cargar_plan.py` — carga 338 sesiones
- [ ] Probar el agente manualmente: `python agents/agente_0_analisis.py`
- [ ] Desplegar `scripts/setup_scheduler.ps1` como administrador en Windows
- [ ] Crear repositorio `bible-study-agents` en GitHub (privado)

### Deuda técnica

- [ ] Revisar y adaptar `utils/errores.py` — actualmente es de "Café con Historia"
- [ ] Hacer configurable el modelo Llama (actualmente hardcodeado como `"llama3.1"`, también en `bible_configuracion`)
- [ ] Eliminar scripts deprecados de carga individuales

### Agentes futuros

- [ ] `agente_1_tareas.py` — extraer tareas de reflexión del análisis y guardarlas en `bible_tareas`
- [ ] `agente_2_slack.py` — responder preguntas o feedback desde Slack

---

## Repositorios relacionados

| Repo                | Descripción                        | Visibilidad |
|---------------------|------------------------------------|-------------|
| `bible-study-agents`| Este repo — agentes Python         | Privado     |
| `bible-study-web`   | Frontend Next.js — dashboard web   | Público     |
