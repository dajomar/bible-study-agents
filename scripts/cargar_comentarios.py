#!/usr/bin/env python3
"""
cargar_comentarios.py
Carga los comentarios de Matthew Henry desde el JSON a Supabase.
Limpia duplicados conservando el comentario más largo.

Uso:
    python3 scripts/cargar_comentarios.py scripts/comentarios_matthew_henry.json

Tablas que puebla:
    - bible_comentarios
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BATCH_SIZE   = 500


def limpiar_duplicados(comentarios: list) -> list:
    """
    Elimina duplicados por (abreviatura_libro, capitulo, versiculo_inicio, autor).
    Cuando hay duplicados, conserva el comentario con texto más largo.
    """
    indice = {}
    for c in comentarios:
        clave = (c["abreviatura_libro"], c["capitulo"], c["versiculo_inicio"], c["autor"])
        if clave not in indice:
            indice[clave] = c
        else:
            # Conservar el más largo
            if len(c["texto"]) > len(indice[clave]["texto"]):
                indice[clave] = c

    return list(indice.values())


def insertar_en_lotes(supabase, registros: list):
    for i in range(0, len(registros), BATCH_SIZE):
        lote = registros[i:i + BATCH_SIZE]
        supabase.table("bible_comentarios").insert(lote).execute()


def cargar_comentarios(json_path: Path):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Faltan SUPABASE_URL o SUPABASE_KEY en .env")
        sys.exit(1)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Verificar si ya están cargados
    existentes = supabase.table("bible_comentarios").select("id", count="exact").execute()
    if existentes.count and existentes.count > 0:
        print(f"Ya existen {existentes.count} comentarios. Abortando.")
        print("Si deseas recargar, elimina los registros primero:")
        print("  DELETE FROM bible_comentarios;")
        sys.exit(0)

    # Leer JSON
    print(f"📖 Leyendo {json_path.name}...")
    with open(json_path, encoding="utf-8") as f:
        comentarios = json.load(f)

    print(f"   Comentarios en JSON    : {len(comentarios)}")

    # Limpiar duplicados
    comentarios = limpiar_duplicados(comentarios)
    print(f"   Después de limpieza    : {len(comentarios)}")

    # Estadísticas por libro
    libros = sorted(set(c["abreviatura_libro"] for c in comentarios))
    print(f"   Libros cubiertos       : {len(libros)}/66")
    print(f"   Libros: {', '.join(libros)}\n")

    # Cargar en Supabase
    print("Insertando en Supabase...")
    insertar_en_lotes(supabase, comentarios)

    print(f"\n{'='*50}")
    print(f"✅ Carga completada")
    print(f"   Comentarios insertados : {len(comentarios)}")
    print(f"   Libros cubiertos       : {len(libros)}/66")
    print(f"{'='*50}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/cargar_comentarios.py <archivo_json>")
        print("Ejemplo: python3 scripts/cargar_comentarios.py scripts/comentarios_matthew_henry.json")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"ERROR: No se encontró {json_path}")
        sys.exit(1)

    cargar_comentarios(json_path)