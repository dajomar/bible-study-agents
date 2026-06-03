-- ============================================================
-- 001_crear_tablas_base.sql
-- Tablas base: libros, capitulos, versiculos
-- Texto bíblico inmutable - Reina Valera
-- ============================================================

-- Tabla de libros (66 libros canónicos protestantes)
CREATE TABLE IF NOT EXISTS bible_libros (
    id          SERIAL PRIMARY KEY,
    orden       INTEGER NOT NULL UNIQUE,          -- 1 al 66, orden canónico
    nombre      TEXT    NOT NULL,                 -- Ej: "Génesis"
    abreviatura TEXT    NOT NULL UNIQUE,          -- Ej: "gn"
    testamento  TEXT    NOT NULL CHECK (testamento IN ('Antiguo', 'Nuevo')),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de capítulos
CREATE TABLE IF NOT EXISTS bible_capitulos (
    id         SERIAL PRIMARY KEY,
    id_libro   INTEGER NOT NULL REFERENCES bible_libros(id) ON DELETE CASCADE,
    numero     INTEGER NOT NULL,                  -- Número real del capítulo (1, 2, 3...)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (id_libro, numero)
);

-- Tabla de versículos
CREATE TABLE IF NOT EXISTS bible_versiculos (
    id           SERIAL PRIMARY KEY,
    id_capitulo  INTEGER NOT NULL REFERENCES bible_capitulos(id) ON DELETE CASCADE,
    numero       INTEGER NOT NULL,                -- Número real del versículo (1, 2, 3...)
    texto        TEXT    NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (id_capitulo, numero)
);

-- Índices para consultas frecuentes del agente
CREATE INDEX IF NOT EXISTS idx_capitulos_libro   ON bible_capitulos(id_libro);
CREATE INDEX IF NOT EXISTS idx_versiculos_cap    ON bible_versiculos(id_capitulo);