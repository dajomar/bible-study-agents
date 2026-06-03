-- ============================================================
-- 002_crear_tablas_plan.sql
-- Tablas del plan de lectura: planes, sesiones
-- ============================================================

-- Tabla de usuarios (mínima para escalabilidad futura)
CREATE TABLE IF NOT EXISTS bible_usuarios (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email      TEXT NOT NULL UNIQUE,
    nombre     TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de planes de lectura
CREATE TABLE IF NOT EXISTS bible_planes (
    id          SERIAL PRIMARY KEY,
    id_usuario  UUID NOT NULL REFERENCES bible_usuarios(id) ON DELETE CASCADE,
    nombre      TEXT NOT NULL,                    -- Ej: "Plan cronológico 2024"
    descripcion TEXT,
    activo      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de sesiones del plan (cada entrada = un día de estudio)
CREATE TABLE IF NOT EXISTS bible_sesiones (
    id                  SERIAL PRIMARY KEY,
    id_plan             INTEGER NOT NULL REFERENCES bible_planes(id) ON DELETE CASCADE,
    orden               INTEGER NOT NULL,          -- Posición en el plan (día 1, día 2...)
    versiculo_inicio_id INTEGER NOT NULL REFERENCES bible_versiculos(id),
    versiculo_fin_id    INTEGER NOT NULL REFERENCES bible_versiculos(id),
    fecha_programada    DATE,                      -- Cuándo está programada
    fecha_completada    TIMESTAMPTZ,               -- Cuándo se completó realmente
    completada          BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (id_plan, orden)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_sesiones_plan      ON bible_sesiones(id_plan);
CREATE INDEX IF NOT EXISTS idx_sesiones_completada ON bible_sesiones(completada);