-- ============================================================
-- 003_crear_tablas_estudio.sql
-- Tablas de estudio: análisis generados por Llama, tareas
-- ============================================================

-- Tabla de análisis bíblico generados por Llama
CREATE TABLE IF NOT EXISTS bible_analisis (
    id                  SERIAL PRIMARY KEY,
    id_sesion           INTEGER NOT NULL REFERENCES bible_sesiones(id) ON DELETE CASCADE,
    contexto_historico  TEXT,                        -- Contexto histórico y cultural del pasaje
    resumen             TEXT,                        -- Resumen de lo que ocurre en el pasaje
    temas_principales   TEXT,                        -- Temas teológicos y espirituales principales
    conexiones          TEXT,                        -- Conexiones con otros pasajes bíblicos
    preguntas_reflexion TEXT,                        -- Preguntas para reflexión personal
    modelo_usado        TEXT,                        -- Ej: "llama3.1"
    tokens_usados       INTEGER,                     -- Tokens del response de Ollama
    duracion_segundos   NUMERIC(6,2),               -- Tiempo total del análisis
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de tareas derivadas del estudio
CREATE TABLE IF NOT EXISTS bible_tareas (
    id          SERIAL PRIMARY KEY,
    id_sesion   INTEGER NOT NULL REFERENCES bible_sesiones(id) ON DELETE CASCADE,
    id_analisis INTEGER REFERENCES bible_analisis(id),
    id_usuario  UUID    NOT NULL REFERENCES bible_usuarios(id),
    descripcion TEXT    NOT NULL,
    origen      TEXT    NOT NULL CHECK (origen IN ('llama', 'usuario')),
    completada  BOOLEAN DEFAULT FALSE,
    notas       TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_analisis_sesion ON bible_analisis(id_sesion);
CREATE INDEX IF NOT EXISTS idx_tareas_sesion   ON bible_tareas(id_sesion);
CREATE INDEX IF NOT EXISTS idx_tareas_usuario  ON bible_tareas(id_usuario);
