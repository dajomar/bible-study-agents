#!/usr/bin/env python3
"""
cargar_biblia.py
Carga una versión de la Biblia a Supabase desde el formato estándar del proyecto.

Formato estándar (único soportado):
[
  {
    "orden": 1,
    "nombre": "Génesis",
    "abreviatura": "gn",
    "testamento": "Antiguo",
    "capitulos": [
      {
        "numero": 1,
        "versiculos": [
          { "numero": 1, "texto": "En el principio creó Dios..." }
        ]
      }
    ]
  }
]

Uso:
    python3 scripts/cargar_biblia.py RVR1960 "scripts/biblia_rvr1960_supabase.json"
    python3 scripts/cargar_biblia.py RV1909  "scripts/biblia_rv1909_supabase.json"

Tablas que puebla:
  - bible_libros
  - bible_capitulos
  - bible_versiculos
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# ============================================================
# CONFIGURACIÓN
# ============================================================

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BATCH_SIZE   = 500

# ============================================================
# HELPERS
# ============================================================

def insertar_en_lotes(supabase, tabla, registros):
    for i in range(0, len(registros), BATCH_SIZE):
        lote = registros[i:i + BATCH_SIZE]
        supabase.table(tabla).insert(lote).execute()

# ============================================================
# CARGA PRINCIPAL
# ============================================================

def cargar_biblia(version: str, json_path: Path):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Faltan SUPABASE_URL o SUPABASE_KEY en .env")
        sys.exit(1)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Verificar si esta versión ya está cargada
    existentes = (
        supabase.table("bible_libros")
        .select("id", count="exact")
        .eq("version", version)
        .execute()
    )
    if existentes.count and existentes.count > 0:
        print(f"La versión {version} ya está cargada ({existentes.count} libros). Abortando.")
        print("Si deseas recargar, trunca primero las tablas en Supabase.")
        sys.exit(0)

    # Leer JSON
    print(f"📖 Cargando {version} desde {json_path.name}...")
    with open(json_path, encoding="utf-8-sig") as f:
        libros = json.load(f)

    # Validar formato estándar
    if not isinstance(libros, list) or not libros[0].get("abreviatura"):
        print("ERROR: El archivo no está en el formato estándar del proyecto.")
        print("Formato esperado: lista de libros con campos orden, nombre, abreviatura, testamento, capitulos.")
        sys.exit(1)

    # Ordenar por orden canónico
    libros = sorted(libros, key=lambda x: x["orden"])
    print(f"   Libros encontrados: {len(libros)}\n")

    # --------------------------------------------------------
    # PASO 1 — bible_libros
    # --------------------------------------------------------
    print("[1] Insertando bible_libros...")

    libros_data = [{
        "orden":       l["orden"],
        "nombre":      l["nombre"],
        "abreviatura": l["abreviatura"],
        "testamento":  l["testamento"],
        "version":     version,
    } for l in libros]

    supabase.table("bible_libros").insert(libros_data).execute()

    libros_db = (
        supabase.table("bible_libros")
        .select("id, orden")
        .eq("version", version)
        .order("orden")
        .execute()
        .data
    )
    id_por_orden = {l["orden"]: l["id"] for l in libros_db}
    print(f"  → {len(libros_db)} libros insertados\n")

    # --------------------------------------------------------
    # PASO 2 — bible_capitulos y bible_versiculos
    # --------------------------------------------------------
    print("[2] Insertando capítulos y versículos...")

    total_caps = 0
    total_vers = 0

    for libro in libros:
        id_libro = id_por_orden[libro["orden"]]

        # Insertar capítulos
        caps_data = [
            {"id_libro": id_libro, "numero": c["numero"]}
            for c in libro["capitulos"]
        ]
        supabase.table("bible_capitulos").insert(caps_data).execute()

        # Recuperar IDs de capítulos
        caps_db = (
            supabase.table("bible_capitulos")
            .select("id, numero")
            .eq("id_libro", id_libro)
            .order("numero")
            .execute()
            .data
        )
        id_por_cap = {c["numero"]: c["id"] for c in caps_db}

        # Construir versículos
        versiculos_data = []
        for cap in libro["capitulos"]:
            id_cap = id_por_cap[cap["numero"]]
            for ver in cap["versiculos"]:
                versiculos_data.append({
                    "id_capitulo": id_cap,
                    "numero":      ver["numero"],
                    "texto":       ver["texto"],
                })

        insertar_en_lotes(supabase, "bible_versiculos", versiculos_data)

        total_caps += len(caps_db)
        total_vers += len(versiculos_data)

        print(f"  ✓ {libro['nombre']:25} {len(caps_db):3} caps  {len(versiculos_data):5} vers")

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------
    print(f"\n{'='*50}")
    print(f"✅ Carga completada — {version}")
    print(f"   Libros     : {len(libros)}")
    print(f"   Capítulos  : {total_caps}")
    print(f"   Versículos : {total_vers:,}")
    print(f"{'='*50}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python3 scripts/cargar_biblia.py <VERSION> <ARCHIVO_JSON>")
        print("Ejemplo: python3 scripts/cargar_biblia.py RVR1960 'scripts/biblia_rvr1960_supabase.json'")
        sys.exit(1)

    version   = sys.argv[1].upper()
    json_path = Path(sys.argv[2])

    if not json_path.exists():
        print(f"ERROR: No se encontró el archivo {json_path}")
        sys.exit(1)

    cargar_biblia(version, json_path)