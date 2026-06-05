-- ============================================================
-- 009_crear_tablas_templates.sql
-- Tablas de templates de planes de estudio
-- ============================================================

-- Template principal
CREATE TABLE IF NOT EXISTS bible_planes_templates (
    id                     SERIAL PRIMARY KEY,
    titulo                 TEXT NOT NULL,
    descripcion            TEXT NOT NULL,
    para_quien             TEXT NOT NULL,
    nivel                  TEXT NOT NULL CHECK (nivel IN ('principiante', 'intermedio', 'avanzado', 'completo')),
    es_completo            BOOLEAN NOT NULL DEFAULT FALSE,
    duracion_estimada_dias INTEGER NOT NULL,
    icono                  TEXT NOT NULL,
    color_acento           TEXT NOT NULL CHECK (color_acento IN ('info', 'warning', 'success', 'danger')),
    recomendado            BOOLEAN NOT NULL DEFAULT FALSE,
    creado_por             TEXT NOT NULL CHECK (creado_por IN ('sistema', 'usuario')) DEFAULT 'sistema',
    id_usuario             UUID REFERENCES bible_usuarios(id) ON DELETE CASCADE,
    activo                 BOOLEAN NOT NULL DEFAULT TRUE,
    orden                  INTEGER NOT NULL,
    created_at             TIMESTAMPTZ DEFAULT NOW()
);

-- Fases del template
CREATE TABLE IF NOT EXISTS bible_planes_templates_fases (
    id           SERIAL PRIMARY KEY,
    id_template  INTEGER NOT NULL REFERENCES bible_planes_templates(id) ON DELETE CASCADE,
    numero       INTEGER NOT NULL,
    titulo       TEXT NOT NULL,
    descripcion  TEXT NOT NULL,
    color_acento TEXT NOT NULL CHECK (color_acento IN ('info', 'warning', 'success', 'danger', 'secondary')),
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (id_template, numero)
);

-- Sesiones abstractas del template (sin IDs de versículos)
CREATE TABLE IF NOT EXISTS bible_planes_templates_sesiones (
    id               SERIAL PRIMARY KEY,
    id_fase          INTEGER NOT NULL REFERENCES bible_planes_templates_fases(id) ON DELETE CASCADE,
    orden            INTEGER NOT NULL,
    abreviatura_libro TEXT NOT NULL,
    capitulo_inicio  INTEGER NOT NULL,
    capitulo_fin     INTEGER NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (id_fase, orden)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_templates_activo      ON bible_planes_templates(activo);
CREATE INDEX IF NOT EXISTS idx_templates_fases       ON bible_planes_templates_fases(id_template);
CREATE INDEX IF NOT EXISTS idx_templates_sesiones    ON bible_planes_templates_sesiones(id_fase);