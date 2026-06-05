-- Migración 008: Búsqueda de versículos sin tildes (accent-insensitive)
-- Requiere la extensión unaccent de PostgreSQL (disponible en Supabase por defecto)

-- Habilitar extensión unaccent
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Función RPC para búsqueda accent-insensitive
-- Usada por /api/biblia/buscar con fallback automático a ilike si no existe
CREATE OR REPLACE FUNCTION buscar_versiculos_v2(termino TEXT, p_version TEXT)
RETURNS TABLE(id INT, numero INT, texto TEXT, capitulo_numero INT, libro_nombre TEXT)
LANGUAGE sql
AS $$
  SELECT v.id, v.numero, v.texto, c.numero AS capitulo_numero, l.nombre AS libro_nombre
  FROM bible_versiculos v
  JOIN bible_capitulos c ON c.id = v.id_capitulo
  JOIN bible_libros l ON l.id = c.id_libro
  WHERE l.version = p_version
    AND unaccent(lower(v.texto)) LIKE '%' || unaccent(lower(termino)) || '%'
  LIMIT 30;
$$;
