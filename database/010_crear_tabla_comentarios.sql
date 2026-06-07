-- ============================================================
-- 010_crear_tabla_comentarios.sql
-- Comentarios bíblicos por rango de versículos
-- Independientes de la versión bíblica — aplican a todas
-- ============================================================

CREATE TABLE IF NOT EXISTS bible_comentarios (
    id                SERIAL PRIMARY KEY,
    abreviatura_libro TEXT    NOT NULL,
    capitulo          INTEGER NOT NULL,
    titulo_capitulo   TEXT,                    -- Índice completo del capítulo
    versiculo_inicio  INTEGER NOT NULL,
    versiculo_fin     INTEGER NOT NULL,
    titulo_seccion    TEXT,                    -- Título del rango específico
    texto             TEXT    NOT NULL,
    autor             TEXT    NOT NULL DEFAULT 'matthew_henry',
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (abreviatura_libro, capitulo, versiculo_inicio, autor)
);

-- Índices para consultas frecuentes del frontend
CREATE INDEX IF NOT EXISTS idx_comentarios_libro    ON bible_comentarios(abreviatura_libro);
CREATE INDEX IF NOT EXISTS idx_comentarios_cap      ON bible_comentarios(abreviatura_libro, capitulo);
CREATE INDEX IF NOT EXISTS idx_comentarios_rango    ON bible_comentarios(abreviatura_libro, capitulo, versiculo_inicio, versiculo_fin);