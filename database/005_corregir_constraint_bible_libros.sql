5 corregir constraint bible libros · SQL
-- ============================================================
-- 005_corregir_constraint_bible_libros.sql
-- Cambia constraints UNIQUE simples por compuestos con version
-- para permitir múltiples versiones bíblicas
-- ============================================================
 
-- Eliminar constraints actuales
ALTER TABLE bible_libros DROP CONSTRAINT IF EXISTS bible_libros_orden_key;
ALTER TABLE bible_libros DROP CONSTRAINT IF EXISTS bible_libros_abreviatura_key;
 
-- Agregar constraints compuestos con version
ALTER TABLE bible_libros ADD CONSTRAINT bible_libros_orden_version_key UNIQUE (orden, version);
ALTER TABLE bible_libros ADD CONSTRAINT bible_libros_abreviatura_version_key UNIQUE (abreviatura, version);