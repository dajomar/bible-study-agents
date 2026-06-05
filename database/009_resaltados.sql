-- Migración 009: Resaltados de versículos por usuario
-- Un usuario puede resaltar un versículo con un color; upsert al cambiar color.

CREATE TABLE IF NOT EXISTS bible_resaltados (
  id            SERIAL PRIMARY KEY,
  id_usuario    UUID    NOT NULL REFERENCES bible_usuarios(id) ON DELETE CASCADE,
  id_versiculo  INT     NOT NULL REFERENCES bible_versiculos(id) ON DELETE CASCADE,
  color         TEXT    NOT NULL CHECK (color IN ('amarillo','verde','azul','rosa','naranja')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (id_usuario, id_versiculo)
);

CREATE INDEX IF NOT EXISTS idx_resaltados_usuario ON bible_resaltados (id_usuario);
