-- ============================================================
-- 004_crear_tabla_configuracion.sql
-- Tabla de configuración global del sistema +
-- columna version en bible_libros +
-- columna version_biblica en bible_usuarios
-- ============================================================

-- Configuración global del sistema
CREATE TABLE IF NOT EXISTS bible_configuracion (
    clave       TEXT PRIMARY KEY,
    valor       TEXT NOT NULL,
    descripcion TEXT,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Versiones disponibles en el sistema y configuración general
INSERT INTO bible_configuracion (clave, valor, descripcion) VALUES
    ('version_disponible_1', 'RV1909',  'Reina Valera 1909'),
    ('version_disponible_2', 'RVR1960', 'Reina Valera Revisada 1960'),
    ('idioma',               'es',      'Idioma del sistema'),
    ('modelo_llama',         'llama3.1','Modelo de Ollama activo para análisis')
ON CONFLICT (clave) DO NOTHING;

-- Versión explícita en cada libro (para saber qué está cargado)
ALTER TABLE bible_libros
ADD COLUMN IF NOT EXISTS version TEXT NOT NULL DEFAULT 'RVR1960';

-- Versión preferida por usuario
ALTER TABLE bible_usuarios
ADD COLUMN IF NOT EXISTS version_biblica TEXT NOT NULL DEFAULT 'RVR1960';