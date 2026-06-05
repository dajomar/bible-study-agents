# bible-study-agents

## Contexto del proyecto

Sistema de agentes Python para estudio bíblico automatizado. Analiza textos de la Biblia usando Llama 3.1 local via Ollama, guarda el progreso en Supabase y envía el estudio diario por Slack.

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
bible_libros        → id, orden (1-66), nombre, abreviatura, testamento, version
bible_capitulos     → id, id_libro, numero
bible_versiculos    → id, id_capitulo, numero, texto
bible_secciones     → id, id_libro, capitulo, versiculo_inicio, titulo
                      -- id_libro ya implica la versión via JOIN con bible_libros
bible_configuracion → id, clave, valor, descripcion
```

> `bible_libros.version` identifica la versión bíblica de cada registro.
> Los constraints UNIQUE son compuestos: `(orden, version)` y `(abreviatura, version)` para soportar múltiples versiones simultáneas.

### Tablas de usuarios y plan

```sql
bible_usuarios    → id (UUID), email, nombre, version_biblica (default 'RVR1960')
bible_planes      → id, id_usuario, nombre, descripcion, activo, version
bible_sesiones    → id, id_plan, orden, versiculo_inicio_id, versiculo_fin_id,
                    fecha_programada, completada
```

> `bible_planes.version` determina qué versículos se usan en el análisis.
> `bible_usuarios.version_biblica` es solo la preferencia para crear nuevos planes.

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
├── 001_crear_tablas_base.sql                 # bible_libros, bible_capitulos, bible_versiculos
├── 002_crear_tablas_plan.sql                 # bible_usuarios, bible_planes, bible_sesiones
├── 003_crear_tablas_estudio.sql              # bible_analisis, bible_tareas
├── 004_crear_tabla_configuracion.sql         # bible_configuracion + version en bible_libros
│                                             # + version_biblica en bible_usuarios
├── 005_corregir_constraint_bible_libros.sql  # Constraints compuestos (orden, version)
│                                             # y (abreviatura, version)
└── 006_agregar_version_a_planes.sql          # Columna version en bible_planes
    (007 pendiente)                           # bible_secciones
```

### Estado actual de la base de datos (2026-06-05)

| Tabla | Registros | Notas |
|---|---|---|
| `bible_libros` | 264 (66 × 4 versiones) | ✅ Poblada |
| `bible_capitulos` | ~4.756 | ✅ Poblada |
| `bible_versiculos` | ~119.000 | ✅ Poblada |
| `bible_secciones` | Varias | ✅ Poblada (RVR1960, NVI, TLA) |
| `bible_configuracion` | 6 | ✅ Poblada |
| `bible_usuarios` | 0 | ⏳ Pendiente |
| `bible_planes` | 0 | ⏳ Pendiente |
| `bible_sesiones` | 0 | ⏳ Pendiente |
| `bible_analisis` | 0 | ⏳ Pendiente |
| `bible_tareas` | 0 | ⏳ Pendiente |

### Versiones bíblicas activas

| Clave | Valor | Secciones | Notas |
|---|---|---|---|
| `version_disponible_1` | `RV1909` | No | Solo para estudios comparativos |
| `version_disponible_2` | `RVR1960` | Sí | **Versión principal del sistema** |
| `version_disponible_3` | `NVI` | Sí | |
| `version_disponible_4` | `TLA` | Sí | ~26.000 versículos (traducción libre) |
| `idioma` | `es` | — | |
| `modelo_llama` | `llama3.1` | — | |

---

## Formato estándar de JSON bíblico

Cualquier versión futura debe estar en este formato antes de cargarse:

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

> Si el JSON fuente tiene versículos duplicados, **el primero gana** (comportamiento de `descargar_y_cargar_versiones.py`).

---

## Reglas del proyecto

1. **Llama es el analista — nunca la fuente.** El texto bíblico viene siempre de Supabase, nunca de Llama.
2. **RVR1960 es la versión principal** — RV1909 se mantiene solo para estudios comparativos.
3. **Versión por plan** — `bible_planes.version` determina el texto del análisis. No cambiar la versión del plan una vez creado.
4. **Formato estándar obligatorio** — convertir cualquier JSON fuente antes de cargarlo.
5. **Script de carga unificado** — usar `scripts/descargar_y_cargar_versiones.py` para nuevas versiones.
6. **Convenciones** iguales a Café con Historia: snake_case, archivos numerados, manejo de errores diferenciado.
7. **Dos repositorios separados** — este repo es local y privado. El frontend Next.js vive en `bible-study-web`.

---

## Estado actual del código

| Componente | Archivo | Estado |
|---|---|---|
| Agente de análisis | `agents/agente_0_analisis.py` | ✅ Implementado, lee version del plan |
| Descarga y carga multi-versión | `scripts/descargar_y_cargar_versiones.py` | ✅ Definitivo — RVR1960, NVI, TLA |
| Carga manual | `scripts/cargar_biblia.py` | ✅ Para cargas desde archivo local |
| Conversor JSON | `scripts/convertir_rvr1960.py` | ✅ Disponible |
| Carga del plan | `scripts/cargar_plan.py` | ✅ Filtra libros por VERSION_BIBLICA |
| Scheduler Windows | `scripts/setup_scheduler.ps1` | ✅ Listo para desplegar |
| Migraciones SQL | `database/001-006_*.sql` | ✅ Ejecutadas (falta crear 007 para bible_secciones) |
| Manejo de errores | `utils/errores.py` | ⚠️ Adaptado de otro proyecto — revisar |
| `requirements.txt` | — | ✅ Creado |

### Scripts deprecados (no usar)

| Archivo | Reemplazado por |
|---|---|
| `scripts/cargar_biblia_rvr09.py` | `scripts/descargar_y_cargar_versiones.py` |
| `scripts/cargar_biblia_rvr1960.py` | `scripts/descargar_y_cargar_versiones.py` |

---

## Próximos pasos

### Despliegue inmediato

- [ ] Crear migración `007_crear_tabla_secciones.sql` y ejecutarla en Supabase
- [ ] Crear usuario en `bible_usuarios` con `version_biblica = 'RVR1960'`
- [ ] Ejecutar `python scripts/cargar_plan.py` — carga 338 sesiones en RVR1960
- [ ] Probar el agente manualmente: `python3 agents/agente_0_analisis.py`
- [ ] Desplegar `scripts/setup_scheduler.ps1` como administrador en Windows

### Deuda técnica

- [ ] Revisar y adaptar `utils/errores.py` — actualmente es de "Café con Historia"
- [ ] Hacer configurable el modelo Llama (hardcodeado como `"llama3.1"`, también en `bible_configuracion`)
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
