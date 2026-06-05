-- Agregar columna version a bible_planes
-- La versión del plan determina qué texto bíblico se usa en el análisis.
-- bible_usuarios.version_biblica actúa como preferencia para nuevos planes.

ALTER TABLE bible_planes ADD COLUMN version TEXT NOT NULL DEFAULT 'RVR1960';
