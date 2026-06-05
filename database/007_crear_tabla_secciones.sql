-- ============================================================
-- 007_crear_tabla_secciones.sql
-- Títulos de sección bíblicos por versículo de inicio
-- Refleja exactamente cómo aparecen en cada versión bíblica
-- ============================================================

CREATE TABLE IF NOT EXISTS bible_secciones (
    id               SERIAL PRIMARY KEY,
    id_libro         INTEGER NOT NULL REFERENCES bible_libros(id) ON DELETE CASCADE,
    capitulo         INTEGER NOT NULL,
    versiculo_inicio INTEGER NOT NULL,
    titulo           TEXT    NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (id_libro, capitulo, versiculo_inicio)
);

-- Índices para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_secciones_libro    ON bible_secciones(id_libro);
CREATE INDEX IF NOT EXISTS idx_secciones_capitulo ON bible_secciones(id_libro, capitulo);