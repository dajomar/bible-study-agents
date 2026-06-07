-- ============================================================
-- 011_crear_tabla_notas.sql
-- Notas personales por rango de versículos
-- Independientes de la versión bíblica — aplican a todas
-- ============================================================

CREATE TABLE IF NOT EXISTS bible_notas (
    id                SERIAL PRIMARY KEY,
    id_usuario        UUID    NOT NULL REFERENCES bible_usuarios(id) ON DELETE CASCADE,
    abreviatura_libro TEXT    NOT NULL,
    capitulo          INTEGER NOT NULL,
    versiculo_inicio  INTEGER NOT NULL,
    versiculo_fin     INTEGER NOT NULL,
    texto             TEXT    NOT NULL,
    color             TEXT    NOT NULL DEFAULT 'amarillo'
                      CHECK (color IN ('amarillo', 'verde', 'azul', 'rosado')),
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (id_usuario, abreviatura_libro, capitulo, versiculo_inicio)
);

-- Índices para consultas frecuentes del frontend
CREATE INDEX IF NOT EXISTS idx_notas_usuario       ON bible_notas(id_usuario);
CREATE INDEX IF NOT EXISTS idx_notas_libro         ON bible_notas(id_usuario, abreviatura_libro);
CREATE INDEX IF NOT EXISTS idx_notas_capitulo      ON bible_notas(id_usuario, abreviatura_libro, capitulo);